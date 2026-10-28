// Pruebas de la gestión de producción: chapas, foto del cálculo, 3D opcional, tiempos MTM,
// agrupamiento, cronómetro y casilla HECHA, eficiencia, demo y almacenamiento.
import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';

import { leerDatos, datosCompletos, crearMotorEnMemoria, renglonCanaletaNotaReal } from './ayudante.js';
import { calcularRenglon } from '../src/logica/calculoRenglon.js';
import { cantidadDeLaNota, consumoFisico, explicarDiferencia, repartirEnTiras } from '../src/logica/chapas.js';
import { fotoDelCalculo, completarFotoVieja, datosDelRenglon, mostrar3d } from '../src/logica/fotoCalculo.js';
import { prepararModelo, calcularItem, calcularNotaMtm, validarItem } from '../src/logica/tiempos.js';
import { tiempoDeRenglon, contarPliegues, tipoDePerfil, tiempoDeNota } from '../src/logica/tiemposRenglon.js';
import { crearRenglonDesdePlantilla, buscarPlantilla } from '../src/logica/renglones.js';
import * as A from '../src/logica/agrupamiento.js';
import * as P from '../src/logica/produccion.js';
import { generarDemo, crearAzar } from '../src/logica/demo.js';
import * as almacenamiento from '../src/datos/almacenamiento.js';
import { armarCsv, leerCsvParametros } from '../src/logica/exportar.js';

const datos = {
  ...datosCompletos(),
  sucursales: leerDatos('sucursales.json').sucursales,
  vendedores: leerDatos('vendedores.json').vendedores,
};
const prod = leerDatos('produccion.json');
const tabla = leerDatos('tiempos-mtm.json');
const modelo = prepararModelo(tabla, datos.config);
const mat = (codigo) => modelo.materiales.find((m) => m.codigo === codigo);
const nuevo = (plantillaId, cambios = {}) => Object.assign(crearRenglonDesdePlantilla(buscarPlantilla(datos.catalogo, plantillaId), datos.config), cambios);

// ---------- A1: cantidad de chapas ----------

test('chapas: 2,44 m → 1; 1,22 m → 0,5; 2 × 1,5 m → 1,23; por unidad → unidades', () => {
  const canaleta = renglonCanaletaNotaReal();
  const cuenta = (r) => cantidadDeLaNota(r, calcularRenglon(r, datos), datos.config);
  assert.deepEqual([cuenta(canaleta).valor, cuenta(canaleta).unidad], [1, 'chapas']);
  assert.equal(cuenta({ ...canaleta, largoCm: 122 }).valor, 0.5);
  assert.equal(cuenta({ ...canaleta, largoCm: 150, cantidad: 2 }).valor, 1.23);
  assert.equal(cuenta({ ...canaleta, largoCm: 300 }).texto, '1,23');
  const boqueta = nuevo('boqueta_suelta', { cantidad: 3 });
  assert.deepEqual([cuenta(boqueta).unidad, cuenta(boqueta).valor], ['unidades', 3]);
});

test('chapas: la estimación física se muestra aparte y explica la diferencia (no cambia la nota)', () => {
  const r = { ...renglonCanaletaNotaReal(), largoCm: 150, cantidad: 2 };
  const resultado = calcularRenglon(r, datos);
  const fisico = consumoFisico(r, resultado, datos.config);
  assert.equal(fisico.tirasBanda, 2, 'cada 1,5 m ocupa una tira de 2,44 (el recorte de 0,94 no entra otra pieza)');
  const explicacion = explicarDiferencia(r, resultado, datos.config);
  assert.equal(explicacion.diferencia, 0.77);
  assert.match(explicacion.texto, /Regla de la nota/);
  assert.equal(cantidadDeLaNota(r, resultado, datos.config).valor, 1.23, 'la nota sigue con la regla pedida');
  assert.deepEqual(repartirEnTiras([150, 150, 56, 94], 244), [0, 38]);
});

// ---------- A2/A3: foto única y 3D opcional ----------

test('foto del cálculo: lleva la cantidad de chapas; una foto vieja se completa sin tocar el código', () => {
  const r = renglonCanaletaNotaReal();
  const foto = fotoDelCalculo(r, calcularRenglon(r, datos), datos.config);
  assert.equal(foto.cantidad.valor, 1);
  const vieja = { descripcion: 'X', codigo: 'VIEJO', desarrolloCm: 60, banda: { numero: 60 }, porUnidad: false };
  const completa = completarFotoVieja({ ...r, cantidad: 2 }, vieja, datos.config);
  assert.equal(completa.codigo, 'VIEJO');
  assert.equal(completa.cantidad.valor, 2);
  assert.equal(datosDelRenglon({ ...r, calculado: vieja }, datos).foto.codigo, 'VIEJO');
});

test('3D opcional: renglón > nota > regla (sin 3D en productos estándar)', () => {
  const estandar = nuevo('std_cumbrera_d30');
  const canaleta = nuevo('canaleta_americana');
  assert.equal(mostrar3d(estandar, { mostrar3d: 'auto' }, datos), false);
  assert.equal(mostrar3d(canaleta, { mostrar3d: 'auto' }, datos), true);
  assert.equal(mostrar3d(canaleta, { mostrar3d: 'no' }, datos), false);
  assert.equal(mostrar3d({ ...estandar, mostrar3d: true }, { mostrar3d: 'no' }, datos), true);
});

// ---------- B: tiempos (réplica de la planilla) ----------

test('tiempos: los 3 ejemplos de la planilla dan lo mismo (EJ1 931,2 s; EJ2 2085,1 s; EJ3 4076,1 s)', () => {
  const ej1 = [{ tipoPerfil: 'ESTANDAR', largoM: 3, desarrolloMm: 333, material: mat('GALV-C25'), cantidad: 4, pliegues: { SIMPLE: 4, CIERRE180: 1 } }];
  const ej2 = [{ tipoPerfil: 'ESPECIAL', largoM: 2.44, desarrolloMm: 400, material: mat('GALV-C25'), cantidad: 6, pliegues: { SIMPLE: 3, ANGULO: 2, CIERRE180: 1, INVERSO: 1 }, detalles: [{ codigo: 'SELLADO', cantidad: 0.3 }] }];
  const ej3 = [
    { tipoPerfil: 'ESTANDAR', largoM: 2.44, desarrolloMm: 400, material: mat('PREP-C25'), cantidad: 10, pliegues: { SIMPLE: 2, CIERRE180: 2 } },
    { tipoPerfil: 'ESTANDAR', largoM: 3, desarrolloMm: 340, material: mat('GALV-C27'), cantidad: 5, pliegues: { SIMPLE: 3, CIERRE180: 2 }, detalles: [{ codigo: 'ENGRAFE', cantidad: 3 }] },
    { tipoPerfil: 'ESPECIAL', largoM: 0.5, desarrolloMm: 300, material: mat('GALV-C25'), cantidad: 2, pliegues: { SIMPLE: 2 }, detalles: [{ codigo: 'SOLDADURA', cantidad: 2 }, { codigo: 'ENCASTRE', cantidad: 2 }] },
  ];
  const cerca = (a, b) => assert.ok(Math.abs(a - b) < 1e-6, `${a} ≠ ${b}`);
  cerca(calcularNotaMtm(ej1, modelo).totalEstandarS, 931.19622011013);
  cerca(calcularNotaMtm(ej1, modelo).horasHombre, 0.403137900061183);
  cerca(calcularNotaMtm(ej2, modelo).totalEstandarS, 2085.06665974026);
  cerca(calcularNotaMtm(ej3, modelo).totalEstandarS, 4076.05211966061);
  const item = calcularItem(ej1[0], modelo);
  assert.equal(item.operarios, 2, '3 m > 2,5 m: dos operarios');
  assert.equal(item.setupNormalS, 241);
  cerca(item.piezaEstandarS, 130.02505502753246);
});

test('tiempos: errores claros con campos vacíos o fuera de rango', () => {
  assert.match(validarItem({ largoM: null, desarrolloMm: 300, material: mat('GALV-C25'), cantidad: 1 }, modelo), /faltan datos obligatorios \(largo\)/);
  assert.match(validarItem({ largoM: 2, desarrolloMm: 300, material: null, cantidad: '' }, modelo), /material, cantidad/);
  assert.match(validarItem({ largoM: 9, desarrolloMm: 300, material: mat('GALV-C25'), cantidad: 1 }, modelo), /largo fuera de rango/);
  assert.match(validarItem({ largoM: 2, desarrolloMm: 300, material: mat('GALV-C25'), cantidad: 1.5 }, modelo), /entero/);
  assert.match(calcularItem({ largoM: 2, desarrolloMm: 5, material: mat('GALV-C25'), cantidad: 1 }, modelo).estado, /^ERROR: desarrollo fuera de rango/);
});

test('tiempos: los parámetros editados cambian el resultado (sin números fijos en el código)', () => {
  const item = { tipoPerfil: 'ESTANDAR', largoM: 3, desarrolloMm: 333, material: mat('GALV-C25'), cantidad: 4, pliegues: { SIMPLE: 4, CIERRE180: 1 } };
  const base = calcularItem(item, modelo).itemEstandarS;
  const conMasSetup = prepararModelo(tabla, datos.config, { parametros: { p_setup_pleg_std_s: 190 } });
  assert.ok(Math.abs(calcularItem(item, conMasSetup).itemEstandarS - base - 100 * 1.2) < 1e-6, '100 s más de setup × (1 + 20 %)');
  const sinSuplementos = prepararModelo(tabla, datos.config, { parametros: { p_supl_np: 0, p_supl_fb: 0, p_supl_pie: 0, p_supl_postura: 0, p_supl_fuerza: 0, p_supl_ruido: 0, p_supl_demoras: 0 } });
  assert.equal(sinSuplementos.p.p_supl_total, 0);
  assert.ok(tabla.parametros.every((p) => p.unidad && p.fuente && p.estado), 'cada parámetro tiene unidad, fuente y estado');
});

test('tiempos del renglón: pliegues leídos del dibujo, estándar o especial, empalme y productos por unidad', () => {
  const real = renglonCanaletaNotaReal();
  assert.deepEqual(contarPliegues(real.perfil, modelo, datos.config), { SIMPLE: 2, ANGULO: 0, CIERRE180: 1, INVERSO: 0, ESPECIAL: 0 });
  assert.equal(tipoDePerfil(nuevo('std_cumbrera_d30'), datos, modelo), 'ESTANDAR');
  const cambiada = nuevo('canaleta_americana');
  cambiada.perfil.tramos[2].medidaCm = 11;
  assert.equal(tipoDePerfil(cambiada, datos, modelo), 'ESPECIAL');
  const larga = tiempoDeRenglon(nuevo('canaleta_americana', { largoCm: 300, cantidad: 2 }), datos, modelo);
  assert.equal(larga.items.length, 2, '2,44 + 0,56: cada tramo se corta y pliega aparte');
  assert.ok(larga.detalles.some((d) => d.codigo === 'REMACHE'), 'la unión del empalme lleva remaches');
  const corta = tiempoDeRenglon(nuevo('canaleta_americana', { largoCm: 244, cantidad: 2 }), datos, modelo);
  assert.equal(larga.setupEstandarS, corta.setupEstandarS, 'el setup se cuenta una sola vez');
  const articulo = tiempoDeRenglon(nuevo('compriband', { cantidad: 2 }), datos, modelo);
  assert.equal(articulo.fuente, 'porUnidad');
  const nota = tiempoDeNota({ renglones: [real] }, datos, modelo);
  assert.ok(nota.totalEstandarS > tiempoDeRenglon(real, datos, modelo).totalEstandarS, 'la nota suma el tiempo del pedido');
});

// ---------- C: agrupamiento ----------

function trabajoDePrueba(clave, atributos, extra = {}) {
  return {
    clave, numeroNota: clave, fechaEntrega: '2026-11-02', prioridad: 'normal', maquina: 'plegadora', minutos: 20, setupMin: 8,
    setupComponentesMin: { interpretacion: 1, chapa: 0.5, guillotina: 1.2, plegadora: 1.8, herramental: 0, control: 0.8, trasladoAtado: 1 },
    atributos: { producto: 'p', perfil: 'A', tipoPerfil: 'ESTANDAR', desarrolloMm: 330, material: 'g|C25|N|', espesorMm: 0.5, largoCm: 244, pliegues: 'S2', herramental: 'V6', ...atributos },
    ...extra,
  };
}

const opciones = { ...prod.agrupamiento, criterios: JSON.parse(JSON.stringify(prod.agrupamiento.criterios)) };

test('agrupamiento: similitud ponderada y ahorro solo de los componentes que se repiten', () => {
  const a = trabajoDePrueba('1', {});
  const b = trabajoDePrueba('2', {});
  const otroMaterial = trabajoDePrueba('3', { material: 'g|C27|N|', espesorMm: 0.4 });
  assert.equal(A.similitud(a, b, opciones.criterios), 1);
  assert.ok(A.similitud(a, otroMaterial, opciones.criterios) < 1);
  assert.equal(A.ahorroEntre(a, b), 0.5 + 1.2 + 1.8 + 0.8 + 1, 'todo menos traslado y atado');
  assert.equal(A.ahorroEntre(a, otroMaterial), 1.8 + 0.8 + 1, 'otro material: se repite chapa y guillotina');
});

test('agrupamiento: forma familias, respeta máquina, ventana de fechas y urgentes; calcula el ahorro', () => {
  const trabajos = [
    trabajoDePrueba('1', {}), trabajoDePrueba('2', {}), trabajoDePrueba('3', {}),
    trabajoDePrueba('4', { perfil: 'B', desarrolloMm: 500, material: 'x', pliegues: 'S5', herramental: 'V8' }),
    trabajoDePrueba('5', {}, { maquina: 'banco' }),
    trabajoDePrueba('6', {}, { fechaEntrega: '2026-12-20' }),
    trabajoDePrueba('7', {}, { prioridad: 'urgente' }),
  ];
  const lotes = A.proponerLotes(trabajos, opciones);
  const loteDe = (clave) => lotes.find((l) => l.claves.includes(clave));
  assert.deepEqual(loteDe('1').claves.sort(), ['1', '2', '3']);
  assert.notEqual(loteDe('4'), loteDe('1'), 'distinto');
  assert.notEqual(loteDe('5'), loteDe('1'), 'otra máquina');
  assert.notEqual(loteDe('6'), loteDe('1'), 'entrega lejana');
  assert.notEqual(loteDe('7'), loteDe('1'), 'urgente sola');
  assert.equal(loteDe('1').resumen.ahorroMin, 2 * 5.3);
  const totales = A.totalesDeLotes(lotes);
  assert.ok(totales.ahorroMin > 0 && totales.ahorroPorcentaje > 0);
  const chicos = A.proponerLotes(trabajos, { ...opciones, maxRenglonesPorLote: 2 });
  assert.ok(chicos.every((l) => l.trabajos.length <= 2), 'tope de renglones por lote');
});

test('agrupamiento: ninguna urgente termina más tarde con los lotes; el jefe puede rearmar', () => {
  const trabajos = [
    trabajoDePrueba('u1', {}, { prioridad: 'urgente', fechaEntrega: '2026-10-29' }),
    trabajoDePrueba('u2', {}, { prioridad: 'urgente', fechaEntrega: '2026-10-31', minutos: 200 }),
    trabajoDePrueba('u3', { perfil: 'Z', material: 'z' }, { prioridad: 'urgente', fechaEntrega: '2026-10-30' }),
  ];
  const { lotes } = A.proponerLotesProtegidos(trabajos, opciones, { plegadora: 1 });
  assert.deepEqual(A.urgentesDemoradas(lotes, { plegadora: 1 }), []);
  const rearmados = A.rearmarLotes([{ id: 'J1', claves: ['u3', 'u1'] }], trabajos);
  assert.deepEqual(rearmados[0].claves, ['u3', 'u1'], 'respeta el orden del jefe');
  assert.equal(rearmados.length, 2, 'el que no está en ningún lote queda solo');
});

// ---------- D: cronómetro, casilla HECHA y eficiencia ----------

test('cronómetro: inicio, pausa, reanudar y fin; error claro si la secuencia no corresponde', () => {
  const quien = { rol: 'operario', nombre: 'Operario 1', operarioId: 'op01' };
  let reg = P.asignarRenglon(P.registroVacio('n1'), 'r1', { operarioId: 'op01', fecha: '2026-10-28', turno: 'manana' }, quien, '2026-10-28T08:00:00.000Z');
  assert.throws(() => P.registrarEvento(reg, 'r1', 'pausa', quien), /todavía no empezó/);
  reg = P.registrarEvento(reg, 'r1', 'inicio', quien, '2026-10-28T10:00:00.000Z');
  reg = P.registrarEvento(reg, 'r1', 'pausa', quien, '2026-10-28T10:20:00.000Z');
  reg = P.registrarEvento(reg, 'r1', 'reanudar', quien, '2026-10-28T10:50:00.000Z');
  reg = P.marcarHecha(reg, 'r1', { hecha: true, tiempoEstandarMin: 25 }, quien, '2026-10-28T11:00:00.000Z');
  assert.equal(reg.renglones.r1.tiempoRealMin, 30, '20 + 10 minutos (la pausa no cuenta)');
  assert.equal(reg.renglones.r1.origenReal, 'cronometro');
  assert.equal(reg.renglones.r1.horaHecha, '2026-10-28T11:00:00.000Z', 'hora automática');
  assert.ok(reg.historial.length >= 5, 'queda la trazabilidad');
  assert.throws(() => P.asignarRenglon(reg, 'r1', { operarioId: 'op02' }, quien), /ya está HECHO/);
  reg = P.marcarHecha(reg, 'r1', { hecha: false }, quien);
  assert.equal(reg.renglones.r1.hecha, false);
});

test('casilla HECHA sin cronómetro: tiempo desde la HECHA anterior o el inicio del turno', () => {
  const local = (h, m) => new Date(2026, 9, 28, h, m).toISOString();
  assert.equal(P.tiempoRealPorCasilla(local(7, 45), [], '07:00'), 45);
  assert.equal(P.tiempoRealPorCasilla(local(9, 0), [local(7, 45), local(8, 30)], '07:00'), 30);
  assert.throws(() => P.marcarHecha(P.registroVacio('n'), 'r', { hecha: true, tiempoEstandarMin: 3 }, { rol: 'jefe' }), /tiene que tener un operario/);
});

test('eficiencia = estándar de lo terminado ÷ real, por día, semana y mes', () => {
  const t = (operarioId, hora, estandar, real) => ({ hecha: true, operarioId, horaHecha: hora, tiempoEstandarMin: estandar, tiempoRealMin: real, minutos: estandar });
  const lista = [t('op01', '2026-10-27T12:00:00', 50, 40), t('op01', '2026-10-28T12:00:00', 30, 60), t('op02', '2026-10-28T12:00:00', 20, 20)];
  const dia = P.eficienciaPorPeriodo(lista, 'dia');
  assert.equal(dia.find((e) => e.operarioId === 'op01' && e.periodo === '2026-10-27').eficiencia, 1.25);
  const semana = P.eficienciaPorPeriodo(lista, 'semana').find((e) => e.operarioId === 'op01');
  assert.equal(semana.periodo, '2026-S44');
  assert.equal(semana.eficiencia, 80 / 100);
  assert.equal(P.eficienciaPorPeriodo(lista, 'mes')[0].periodo, '2026-10');
});

test('fechas hábiles, estado de la nota y demorada (calculado, no guardado)', () => {
  assert.equal(P.sumarDiasHabiles('2026-10-30', 1), '2026-11-02', 'viernes + 1 hábil = lunes');
  assert.equal(P.diasHabilesHasta('2026-10-28', '2026-11-02'), 3);
  const base = { fechaEntrega: '2026-10-30', minutos: 10 };
  assert.equal(P.estadoDeNota([{ ...base, hecha: true }], '2026-10-28'), 'hecha');
  assert.equal(P.estadoDeNota([{ ...base, operarioId: 'op01', fecha: '2026-10-29' }], '2026-10-28'), 'programada');
  assert.equal(P.estadoDeNota([{ ...base, operarioId: 'op01', fecha: '2026-11-03' }], '2026-10-28'), 'demorada');
  assert.equal(P.estadoDeNota([{ ...base }], '2026-11-02'), 'demorada');
});

// ---------- F: demo ----------

test('demo: 50 notas por local, semilla fija, sin errores, todo marcado como demo', () => {
  const contexto = { modelo, prod, operarios: prod.operarios };
  const uno = generarDemo(datos, contexto, { hoy: '2026-10-28' });
  const dos = generarDemo(datos, contexto, { hoy: '2026-10-28' });
  assert.equal(uno.notas.length, datos.sucursales.length * 50);
  assert.deepEqual(uno.notas.map((n) => n.renglones.map((r) => [r.plantillaId, r.largoCm, r.cantidad])), dos.notas.map((n) => n.renglones.map((r) => [r.plantillaId, r.largoCm, r.cantidad])));
  assert.equal(uno.resumen.renglonesConError, 0);
  assert.ok(uno.notas.every((n) => n.demo && String(n.numero).startsWith('D-')));
  assert.ok(uno.notas.every((n) => n.renglones.every((r) => r.calculado?.cantidad)), 'cada renglón con su cantidad de chapas');
  assert.equal(crearAzar(1).numero(), crearAzar(1).numero());
  // Hay familias repetidas: el agrupamiento ahorra setup.
  const trabajos = P.armarTrabajos(uno.notas, uno.registros, { datos, modelo, prod }).filter((t) => !t.hecha);
  const { lotes } = A.proponerLotesProtegidos(trabajos, prod.agrupamiento, { plegadora: 2 });
  assert.ok(A.totalesDeLotes(lotes).lotesAgrupados > 5);
});

// ---------- almacenamiento ----------

beforeEach(() => {
  almacenamiento.configurarAlmacenamiento({ motor: crearMotorEnMemoria(), leerArchivo: async (nombre) => leerDatos(nombre) });
});

test('almacenamiento: la demo no toca las notas reales ni los contadores y se borra sola', async () => {
  const sucursales = datos.sucursales;
  const real = await almacenamiento.emitirNota(await almacenamiento.crearNotaVacia({ sucursalId: 'colon', vendedorId: 'v01' }), sucursales);
  const contadores = await almacenamiento.leerContadores(sucursales);
  const demo = generarDemo(datos, { modelo, prod, operarios: prod.operarios }, { hoy: '2026-10-28', porLocal: 2 });
  await almacenamiento.cargarDemo(demo);
  await assert.rejects(() => almacenamiento.cargarDemo(demo), /Ya hay datos de demostración/);
  assert.equal((await almacenamiento.listarNotas()).length, 1 + demo.notas.length);
  assert.deepEqual(await almacenamiento.leerContadores(sucursales), contadores);
  assert.equal(await almacenamiento.borrarDemo(), demo.notas.length);
  const quedan = await almacenamiento.listarNotas();
  assert.deepEqual(quedan.map((n) => n.id), [real.id]);
  assert.equal(Object.keys(await almacenamiento.leerRegistros()).length, 0);
});

test('almacenamiento: migración de notas emitidas viejas (agrega cantidad de chapas y campos nuevos)', async () => {
  const sucursales = datos.sucursales;
  const nota = await almacenamiento.crearNotaVacia({ sucursalId: 'colon', vendedorId: 'v01' });
  delete nota.fechaEntrega; delete nota.prioridad; delete nota.mostrar3d;
  const r = renglonCanaletaNotaReal();
  nota.renglones = [{ ...r, cantidad: 3, calculado: { descripcion: 'vieja', codigo: 'CG05P60', desarrolloCm: 60, banda: { numero: 60 }, porUnidad: false, avisos: [] } }];
  await almacenamiento.emitirNota(nota, sucursales);
  assert.deepEqual(await almacenamiento.migrarDatos(datos), { migradas: 1 });
  const migrada = (await almacenamiento.listarNotas())[0];
  assert.equal(migrada.renglones[0].calculado.cantidad.valor, 3);
  assert.equal(migrada.renglones[0].calculado.codigo, 'CG05P60');
  assert.equal(migrada.prioridad, 'normal');
  assert.deepEqual(await almacenamiento.migrarDatos(datos), { migradas: 0 }, 'una sola vez');
});

test('almacenamiento: lotes con deshacer, incidencias con causa obligatoria y parámetros descartables', async () => {
  await almacenamiento.guardarLotes([{ id: 'L1', claves: ['a/1', 'b/2'] }]);
  await almacenamiento.guardarLotes([{ id: 'L1', claves: ['a/1'] }, { id: 'L2', claves: ['b/2'] }]);
  assert.equal((await almacenamiento.deshacerLotes()).length, 1);
  await assert.rejects(() => almacenamiento.agregarIncidencia({ tipo: 'retrabajo' }), /Elegí el tipo y la causa/);
  await almacenamiento.agregarIncidencia({ tipo: 'retrabajo', causa: 'Medida mal tomada', notaId: 'n1', minutosPerdidos: 15 });
  assert.equal((await almacenamiento.leerIncidencias()).length, 1);
  assert.equal((await almacenamiento.leerRegistros()).n1.historial[0].accion, 'incidencia: retrabajo');
  await almacenamiento.guardarCambiosTiempos({ parametros: { p_setup_pleg_std_s: 120 } });
  assert.equal((await almacenamiento.leerCambiosTiempos()).parametros.p_setup_pleg_std_s, 120);
  await almacenamiento.descartarCambiosTiempos();
  assert.equal(await almacenamiento.leerCambiosTiempos(), null);
});

// ---------- exportar ----------

test('exportar: CSV para Excel en español e importación de PARAMETROS_API', () => {
  const csv = armarCsv(['Nota', 'Minutos'], [['NP "1"; A', 12.345], [null, 3]]);
  assert.ok(csv.startsWith('﻿Nota;Minutos\r\n'));
  assert.match(csv, /"NP ""1""; A";12,35/);
  const { valores, errores } = leerCsvParametros('Clave,Valor,Unidad,Origen\np_setup_pleg_std_s,"120,5",s,X\np_tipo_plegadora,MANUAL,lista,X\np_vacio,,s,X\nact01_np,155,TMU,X\n');
  assert.deepEqual(valores, { p_setup_pleg_std_s: 120.5, p_tipo_plegadora: 'MANUAL' });
  assert.deepEqual(errores, ['p_vacio: sin valor']);
  assert.match(leerCsvParametros('a,b\n1,2').errores[0], /PARAMETROS_API/);
});
