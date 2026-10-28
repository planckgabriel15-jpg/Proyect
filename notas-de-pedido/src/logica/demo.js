// =============================================================
// demo.js
// DATOS DE DEMOSTRACIÓN: 50 notas emitidas por cada local de datos/sucursales.json,
// con semilla fija (siempre salen iguales), marcadas demo: true y con número propio
// ("D-C001"): NO usan los contadores reales ni se mezclan con las notas reales
// (almacenamiento.borrarDemo() saca solo lo marcado como demo).
//
// Mezcla pensada para mostrar el agrupamiento:
// - ~45 % de los renglones son "productos de siempre" con la misma medida y material
//   (canaleta de la nota real, cumbrera D30, limahoya, babeta…) → forman familias;
// - ~35 % son variantes parecidas (mismo producto, otra medida o calibre);
// - ~20 % son claramente distintos (piezas a medida, caños, boquetas, artículos).
// Las notas viejas quedan terminadas, con tiempo real simulado (para ver la eficiencia),
// las del medio a medio hacer y las nuevas pendientes.
// =============================================================

import { crearRenglonDesdePlantilla, buscarPlantilla } from './renglones.js';
import { calcularRenglon } from './calculoRenglon.js';
import { fotoDelCalculo } from './fotoCalculo.js';
import { tiempoDeNota } from './tiemposRenglon.js';
import { sumarDiasHabiles, diaDe, registroVacio } from './produccion.js';
import { redondear } from './numeros.js';

export const SEMILLA_DEMO = 20261028;
export const NOTAS_POR_LOCAL = 50;

/** Generador de números al azar con semilla (mulberry32): mismos números en cada corrida. */
export function crearAzar(semilla) {
  let a = semilla >>> 0;
  const siguiente = () => {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  return {
    numero: siguiente,
    entero: (min, max) => min + Math.floor(siguiente() * (max - min + 1)),
    elegir: (lista) => lista[Math.floor(siguiente() * lista.length)],
    pesado: (opciones) => {
      const total = opciones.reduce((s, o) => s + o.peso, 0);
      let x = siguiente() * total;
      for (const o of opciones) { x -= o.peso; if (x <= 0) return o; }
      return opciones[opciones.length - 1];
    },
  };
}

// Productos "de siempre": misma plantilla, misma medida y mismo material → misma familia.
const REPETIDOS = [
  { plantilla: 'canaleta_nota_real', largoCm: 244, calibreId: 'C25', terminacion: 'P', colorId: 'negro', peso: 6, cantidades: [2, 4, 6, 10] },
  { plantilla: 'std_cumbrera_d30', largoCm: 200, calibreId: 'C25', terminacion: 'N', peso: 5, cantidades: [3, 5, 8] },
  { plantilla: 'std_limahoya_ch30', largoCm: 200, calibreId: 'C25', terminacion: 'N', peso: 3, cantidades: [2, 4] },
  { plantilla: 'babeta_l_15', largoCm: 244, calibreId: 'C25', terminacion: 'P', colorId: 'rojo_teja', peso: 4, cantidades: [4, 6, 10] },
  { plantilla: 'std_canaleta_hiper', largoCm: 244, calibreId: 'C25', terminacion: 'N', peso: 3, cantidades: [2, 3, 5] },
  { plantilla: 'cumbrera_lisa_20', largoCm: 244, calibreId: 'C27', terminacion: 'P', colorId: 'gris', peso: 3, cantidades: [3, 6] },
];
// Variantes: mismo producto con otra medida, calibre o color.
const VARIANTES = [
  { plantilla: 'canaleta_americana', largos: [150, 200, 244, 300, 400], calibres: ['C25', 'C27'], colores: ['negro', 'blanco', null] },
  { plantilla: 'babeta_l_20', largos: [122, 200, 244], calibres: ['C25', 'C27'], colores: ['rojo_teja', 'verde', null] },
  { plantilla: 'cenefa_lisa', largos: [200, 244, 300], calibres: ['C25'], colores: ['blanco', 'negro'] },
  { plantilla: 'std_media_cumbrera_d33', largos: [122, 200, 244], calibres: ['C25', 'C22'], colores: [null] },
  { plantilla: 'media_cumbrera', largos: [200, 244], calibres: ['C25', 'C27'], colores: [null, 'gris'] },
  { plantilla: 'chapa_lisa', largos: [100, 122, 244], calibres: ['C25', 'C22'], colores: [null] },
];
// Claramente distintos.
const DISTINTOS = [
  { plantilla: 'cano', peso: 3 },
  { plantilla: 'boqueta_suelta', peso: 3 },
  { plantilla: 'pieza_libre', peso: 2 },
  { plantilla: 'sombrero_chino', peso: 1 },
  { plantilla: 'compriband', peso: 1 },
  { plantilla: 'soporte_canaleta', peso: 2 },
];

function aplicarMaterial(renglon, { calibreId, terminacion, colorId }) {
  renglon.materialId = 'galvanizado';
  renglon.calibreId = calibreId;
  renglon.terminacion = terminacion;
  renglon.colorId = terminacion === 'P' ? colorId : null;
  renglon.ladoPintura = 'afuera';
}

function renglonDemo(azar, datos, indice) {
  const tipo = azar.pesado([{ id: 'repetido', peso: 45 }, { id: 'variante', peso: 35 }, { id: 'distinto', peso: 20 }]).id;
  let renglon;
  if (tipo === 'repetido') {
    const p = azar.pesado(REPETIDOS);
    renglon = crearRenglonDesdePlantilla(buscarPlantilla(datos.catalogo, p.plantilla), datos.config);
    renglon.largoCm = p.largoCm;
    aplicarMaterial(renglon, p);
    renglon.cantidad = azar.elegir(p.cantidades);
  } else if (tipo === 'variante') {
    const p = azar.elegir(VARIANTES);
    renglon = crearRenglonDesdePlantilla(buscarPlantilla(datos.catalogo, p.plantilla), datos.config);
    renglon.largoCm = azar.elegir(p.largos);
    const color = azar.elegir(p.colores);
    aplicarMaterial(renglon, { calibreId: azar.elegir(p.calibres), terminacion: color ? 'P' : 'N', colorId: color });
    renglon.cantidad = azar.entero(1, 8);
    // Algunas variantes con tapas (canaletas) para que haya detalles.
    if (renglon.accesorios && azar.numero() < 0.4) renglon.accesorios.tapaIzquierda = 'soldada';
  } else {
    const p = azar.pesado(DISTINTOS);
    renglon = crearRenglonDesdePlantilla(buscarPlantilla(datos.catalogo, p.plantilla), datos.config);
    aplicarMaterial(renglon, { calibreId: 'C25', terminacion: 'N', colorId: null });
    renglon.cantidad = azar.entero(1, 6);
    if (p.plantilla === 'cano') {
      renglon.largoCm = azar.elegir([100, 200, 300]);
      renglon.parametros.forma = azar.elegir(['redonda', 'rectangular']);
    }
    if (p.plantilla === 'pieza_libre') {
      // Perfil a medida en "Z" con medidas al azar.
      renglon.perfil = { direccionInicial: 'arriba', tramos: [
        { medidaCm: azar.entero(3, 8), anguloPliegue: 90, sentido: 'izquierda', tipo: 'normal', observacion: '', corteLaser: null },
        { medidaCm: azar.entero(10, 25), anguloPliegue: azar.elegir([90, 100, 120]), sentido: 'izquierda', tipo: 'normal', observacion: '', corteLaser: null },
        { medidaCm: azar.entero(3, 8), anguloPliegue: 90, sentido: 'derecha', tipo: 'normal', observacion: '', corteLaser: null },
      ] };
      renglon.largoCm = azar.elegir([100, 200, 244]);
    }
  }
  renglon.id = `rdemo_${indice}`;
  return renglon;
}

/**
 * Genera los datos de demostración.
 * @param {{config, materiales, codigos, catalogo, sucursales}} datos
 * @param {{modelo, prod, operarios}} contexto  modelo de tiempos, datos/produccion.json y operarios
 * @param {{hoy?: string, semilla?: number, porLocal?: number}} opciones
 * @returns {{notas: Array, registros: object, resumen: object}}
 */
export function generarDemo(datos, { modelo, prod, operarios }, opciones = {}) {
  const azar = crearAzar(opciones.semilla ?? SEMILLA_DEMO);
  const hoy = opciones.hoy || diaDe(new Date());
  const porLocal = opciones.porLocal ?? NOTAS_POR_LOCAL;
  const notas = [];
  const registros = {};
  const activos = operarios.filter((o) => o.activo !== false);
  // Rendimiento "verdadero" simulado de cada operario (para que la eficiencia tenga algo que mostrar).
  const ritmo = Object.fromEntries(activos.map((o) => [o.id, 0.8 + azar.numero() * 0.35]));
  const vendedores = datos.vendedores || [];
  let indice = 0;
  // Fechas de emisión: los últimos 30 días hábiles, más notas recientes que viejas.
  const dias = [];
  for (let i = 30; i >= 0; i--) dias.push(sumarDiasHabiles(restarDiasHabiles(hoy, i, prod.diasHabiles), 0, prod.diasHabiles));

  for (const sucursal of datos.sucursales) {
    for (let n = 1; n <= porLocal; n++) {
      const emision = dias[Math.min(dias.length - 1, Math.floor(Math.sqrt(azar.numero()) * dias.length))];
      const urgente = azar.numero() < 0.1;
      const renglones = [];
      const cuantos = azar.pesado([{ n: 1, peso: 35 }, { n: 2, peso: 35 }, { n: 3, peso: 20 }, { n: 4, peso: 10 }]).n;
      for (let r = 0; r < cuantos; r++) {
        const renglon = renglonDemo(azar, datos, indice++);
        const resultado = calcularRenglon(renglon, datos);
        renglon.calculado = fotoDelCalculo(renglon, resultado, datos.config);
        renglones.push(renglon);
      }
      const vendedor = vendedores.filter((v) => v.sucursalHabitualId === sucursal.id)[0] || vendedores[0];
      const nota = {
        id: `nota_demo_${sucursal.id}_${n}`,
        demo: true,
        estado: 'emitida',
        numero: `D-${sucursal.letra}${String(n).padStart(3, '0')}`,
        sucursalId: sucursal.id,
        vendedorId: vendedor?.id || null,
        fechaCreacion: `${emision}T09:00:00.000Z`,
        fechaEmision: `${emision}T${String(8 + azar.entero(0, 9)).padStart(2, '0')}:${String(azar.entero(0, 59)).padStart(2, '0')}:00.000Z`,
        cliente: `Cliente demo ${String(azar.entero(1, 180)).padStart(3, '0')}`,
        factura: `A-${String(azar.entero(1, 9)).padStart(4, '0')}-${String(azar.entero(1, 99999)).padStart(8, '0')}`,
        fechaEntrega: sumarDiasHabiles(emision, urgente ? azar.entero(1, 2) : azar.entero(3, 8), prod.diasHabiles),
        prioridad: urgente ? 'urgente' : 'normal',
        mostrar3d: 'auto',
        renglones,
      };
      notas.push(nota);
      registros[nota.id] = simularProduccion(nota, azar, { hoy, emision, datos, modelo, prod, activos, ritmo });
    }
  }
  return { notas, registros, resumen: resumirDemo(notas, datos, modelo) };
}

function restarDiasHabiles(dia, n, diasHabiles) {
  const [a, m, d] = dia.split('-').map(Number);
  const f = new Date(a, m - 1, d);
  let quedan = n;
  while (quedan > 0) {
    f.setDate(f.getDate() - 1);
    if (diasHabiles.includes(f.getDay())) quedan -= 1;
  }
  return diaDe(f);
}

/** Registro de producción simulado: viejas terminadas, del medio a medias, nuevas pendientes. */
function simularProduccion(nota, azar, { hoy, emision, datos, modelo, prod, activos, ritmo }) {
  const registro = registroVacio(nota.id, true);
  const antiguedad = Math.max(0, Math.round((Date.parse(hoy) - Date.parse(emision)) / 86400000));
  const tiempos = tiempoDeNota(nota, datos, modelo);
  nota.renglones.forEach((renglon, i) => {
    const tiempo = tiempos.renglones[i];
    const minutos = tiempo.totalEstandarS / 60 + (i === 0 ? tiempos.pedidoEstandarS / 60 : 0);
    const habilitados = activos.filter((o) => o.maquinas.includes(tiempo.maquina));
    const operario = azar.elegir(habilitados.length ? habilitados : activos);
    const terminado = antiguedad > 6 || (antiguedad > 2 && azar.numero() < 0.5);
    const asignado = terminado || antiguedad > 0 || azar.numero() < 0.3;
    if (!asignado) return;
    const fecha = terminado ? sumarDiasHabiles(emision, azar.entero(0, 2), prod.diasHabiles) : sumarDiasHabiles(hoy, azar.entero(0, 3), prod.diasHabiles);
    const r = { operarioId: operario.id, fecha: fecha > hoy && terminado ? hoy : fecha, turno: operario.turno, loteId: null, hecha: false, horaHecha: null, eventos: [] };
    if (terminado) {
      const real = redondear((minutos / ritmo[operario.id]) * (0.85 + azar.numero() * 0.3), 2);
      const inicio = new Date(`${r.fecha}T${operario.turno === 'tarde' ? '15' : '07'}:${String(azar.entero(0, 59)).padStart(2, '0')}:00`);
      inicio.setMinutes(inicio.getMinutes() + azar.entero(0, 300));
      const fin = new Date(inicio.getTime() + real * 60000);
      const porCasilla = azar.numero() < 0.25;
      r.eventos = porCasilla ? [] : [{ tipo: 'inicio', hora: inicio.toISOString(), operarioId: operario.id }, { tipo: 'fin', hora: fin.toISOString(), operarioId: operario.id }];
      Object.assign(r, { hecha: true, horaHecha: fin.toISOString(), tiempoEstandarMin: redondear(minutos, 2), ahorroLoteMin: 0, tiempoRealMin: real, origenReal: porCasilla ? 'casilla' : 'cronometro' });
    }
    registro.renglones[renglon.id] = r;
  });
  registro.historial.push({ hora: nota.fechaEmision, rol: 'sistema', usuario: 'demo', accion: 'datos de demostración', detalle: 'generado con semilla fija' });
  return registro;
}

/** Resumen de los datos generados (tiempo total, distribución por nota). */
export function resumirDemo(notas, datos, modelo) {
  const minutos = notas.map((n) => tiempoDeNota(n, datos, modelo).totalMin).sort((a, b) => a - b);
  const total = minutos.reduce((s, m) => s + m, 0);
  const percentil = (p) => minutos[Math.min(minutos.length - 1, Math.floor(p * minutos.length))];
  const renglones = notas.reduce((s, n) => s + n.renglones.length, 0);
  const conError = notas.flatMap((n) => n.renglones).filter((r) => calcularRenglon(r, datos).errores.length).length;
  return {
    notas: notas.length,
    renglones,
    renglonesConError: conError,
    totalHoras: total / 60,
    promedioMin: total / Math.max(1, notas.length),
    minimoMin: minutos[0] || 0,
    medianaMin: percentil(0.5) || 0,
    p90Min: percentil(0.9) || 0,
    maximoMin: minutos[minutos.length - 1] || 0,
    histograma: [[0, 10], [10, 20], [20, 40], [40, 60], [60, 120], [120, Infinity]].map(([a, b]) => ({ desde: a, hasta: b, notas: minutos.filter((m) => m >= a && m < b).length })),
  };
}
