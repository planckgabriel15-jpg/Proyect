// =============================================================
// tiemposRenglon.js
// Pasa un renglón de la nota a las ENTRADAS del modelo MTM (tiempos.js) y suma la nota.
//
// La planilla pide cargar a mano: tipo de perfil, pliegues por tipo y detalles. Acá se
// leen del dibujo con reglas explícitas (parámetros q_… de datos/tiempos-mtm.json, [SUPUESTO]):
//  - pliegues: cada pliegue del perfil es SIMPLE (90° ± tolerancia), ANGULO (otro ángulo),
//    CIERRE180 (dobladillo) o INVERSO (gira al revés que el pliegue anterior);
//  - tipo de perfil: ESTANDAR si es un producto estándar o el perfil del catálogo sin cambios
//    ("programa guardado" en la plegadora); si no, ESPECIAL. Con pendiente: ESPECIAL;
//  - detalles: tapas (TAPA), boquetas (corte con tijera + soldadura), cortes (tijera y, si
//    llevan pared, soldadura), uniones de empalme (remaches + sellado);
//  - empalme: cada tramo de chapa se corta y pliega aparte (mismo setup para todos);
//  - caños: redondo = curvado + engrafe; cuadrado o rectangular = 3 pliegues + 2 cierres + engrafe
//    (como el ejemplo EJ3 de la planilla);
//  - productos sin perfil (boquetas sueltas, sombreros, codos, artículos): tiempo propio por grupo.
// =============================================================

import { leerNumero } from './numeros.js';
import { giroEnTramo } from './geometria.js';
import { tramosDeChapa } from './empalme.js';
import { tienePendiente } from './pendiente.js';
import { buscarPlantilla } from './renglones.js';
import { normalizarBoqueta, tipoDeTapa } from './accesoriosCanaleta.js';
import { calcularItem, tiempoDelPedido, COMPONENTES_SETUP } from './tiempos.js';
import { calcularRenglon } from './calculoRenglon.js';

/** Cuenta los pliegues del perfil por tipo. */
export function contarPliegues(perfil, modelo, config) {
  const cuenta = { SIMPLE: 0, ANGULO: 0, CIERRE180: 0, INVERSO: 0, ESPECIAL: 0 };
  const tramos = perfil?.tramos || [];
  const tolerancia = modelo.p.q_tolerancia_angulo_recto_grados ?? 1;
  let sentidoAnterior = null;
  for (let i = 1; i < tramos.length; i++) {
    const giro = giroEnTramo(tramos, i, config);
    if (giro.esVuelta) { cuenta.CIERRE180++; continue; }
    if (sentidoAnterior && giro.sentido !== sentidoAnterior) cuenta.INVERSO++;
    else if (Math.abs(giro.anguloInterior - 90) <= tolerancia) cuenta.SIMPLE++;
    else cuenta.ANGULO++;
    sentidoAnterior = giro.sentido;
  }
  return cuenta;
}

/** ¿Perfil igual al de la plantilla del catálogo? (mismas medidas, ángulos, sentidos y tipos) */
function perfilSinCambios(renglon, plantilla) {
  const a = plantilla?.perfil?.tramos || [];
  const b = renglon.perfil?.tramos || [];
  if (!a.length || a.length !== b.length) return false;
  return a.every((t, i) => leerNumero(t.medidaCm) === leerNumero(b[i].medidaCm)
    && leerNumero(t.anguloPliegue) === leerNumero(b[i].anguloPliegue)
    && (t.sentido || 'izquierda') === (b[i].sentido || 'izquierda') && (t.tipo || 'normal') === (b[i].tipo || 'normal'));
}

/** ESTANDAR o ESPECIAL (ver arriba). */
export function tipoDePerfil(renglon, datos, modelo) {
  if (tienePendiente(renglon) && modelo.p.q_pendiente_es_especial) return 'ESPECIAL';
  const plantilla = datos.catalogo ? buscarPlantilla(datos.catalogo, renglon.plantillaId) : null;
  if (plantilla?.grupo === 'estandar' || perfilSinCambios(renglon, plantilla)) return 'ESTANDAR';
  return 'ESPECIAL';
}

/**
 * Fila de materiales del modelo para el material, la terminación y el calibre del renglón.
 * Toma la del espesor más parecido; el peso y el ciclo se calculan con el espesor REAL del calibre.
 * @returns {{fila: object|null, espesorMm: number|null, aviso: string|null}}
 */
export function materialDelModelo(renglon, materiales, modelo) {
  const calibre = materiales.calibres.find((c) => c.id === renglon.calibreId);
  const terminacion = renglon.terminacion === 'P' ? 'P' : 'N';
  let candidatos = modelo.materiales.filter((m) => m.materialId === renglon.materialId && m.terminacion === terminacion);
  if (!candidatos.length) candidatos = modelo.materiales.filter((m) => m.materialId === renglon.materialId);
  if (!candidatos.length || !calibre) return { fila: null, espesorMm: null, aviso: `El material "${renglon.materialId}" no tiene datos en el modelo de tiempos` };
  const fila = candidatos.reduce((mejor, m) => (Math.abs(m.espesorMm - calibre.espesorMm) < Math.abs(mejor.espesorMm - calibre.espesorMm) ? m : mejor));
  const aviso = Math.abs(fila.espesorMm - calibre.espesorMm) > 0.001
    ? `Factores de ${fila.codigo} (espesor más parecido a ${calibre.espesorMm} mm)` : null;
  return { fila, espesorMm: calibre.espesorMm, aviso };
}

/** Detalles (código + cantidad por pieza) que salen de los accesorios, cortes y empalme. */
export function detallesDelRenglon(renglon, resultado, modelo, config, tramos) {
  const p = modelo.p;
  const lista = [];
  const sumar = (codigo, cantidad) => {
    if (!(cantidad > 0)) return;
    const existente = lista.find((d) => d.codigo === codigo);
    if (existente) existente.cantidad += cantidad;
    else lista.push({ codigo, cantidad });
  };
  const acc = renglon.accesorios;
  if (acc) {
    const tapas = ['izquierda', 'derecha'].filter((lado) => tipoDeTapa(acc, lado) !== 'ninguna').length;
    sumar('TAPA', tapas * p.q_tapas_por_tapa);
    const boquetas = (acc.boquetas || []).map((b) => normalizarBoqueta(b, config)).length;
    sumar('SOLDADURA', boquetas * p.q_soldaduras_por_boqueta);
    sumar('ENCASTRE', boquetas * p.q_encastres_por_corte);
  }
  for (const corte of renglon.cortes || []) {
    sumar('ENCASTRE', p.q_encastres_por_corte);
    if (leerNumero(corte.paredAlturaCm) > 0) sumar('SOLDADURA', p.q_soldaduras_por_pared);
  }
  const uniones = Math.max(0, tramos.length - 1);
  if (uniones) {
    sumar('REMACHE', uniones * p.q_remaches_por_union);
    if (p.q_sellado_por_union) sumar('SELLADO', (uniones * (resultado.desarrolloCm || 0)) / 100);
  }
  return lista;
}

function pliegesDeCano(forma) {
  return forma === 'redonda' || forma === 'circular'
    ? { SIMPLE: 0, ANGULO: 0, CIERRE180: 0, INVERSO: 0, ESPECIAL: 0 }
    : { SIMPLE: 3, ANGULO: 0, CIERRE180: 2, INVERSO: 0, ESPECIAL: 0 };
}

/** Tiempo de los productos que no son un perfil plegado: tabla productosSinPerfil por grupo. */
function tiempoSinPerfil(renglon, datos, modelo) {
  const plantilla = datos.catalogo ? buscarPlantilla(datos.catalogo, renglon.plantillaId) : null;
  const grupo = plantilla?.grupo || 'especial';
  const fila = modelo.productosSinPerfil.find((f) => f.grupo === grupo) || modelo.productosSinPerfil.find((f) => f.grupo === '*');
  const S = modelo.p.p_supl_total;
  const Q = Math.max(0, leerNumero(renglon.cantidad) || 0);
  const setupEstandarS = fila.setupS * (1 + S);
  const piezaEstandarS = fila.piezaS * (1 + S);
  return {
    fuente: 'porUnidad',
    estado: 'OK',
    mensajes: [`Tiempo por unidad del grupo "${fila.grupo}" ${fila.estado}`],
    maquina: fila.maquina,
    tipoPerfil: 'ESPECIAL',
    operarios: 1,
    cantidad: Q,
    setupEstandarS,
    setupComponentesS: { interpretacion: 0, chapa: 0, guillotina: 0, plegadora: 0, herramental: 0, control: 0, trasladoAtado: setupEstandarS },
    piezaEstandarS,
    totalEstandarS: setupEstandarS + Q * piezaEstandarS,
    horasHombre: (setupEstandarS + Q * piezaEstandarS) / 3600,
    pliegues: null,
    items: [],
  };
}

/**
 * Tiempo estándar de un renglón.
 * @returns {{fuente: 'mtm'|'porUnidad'|'error', estado: string, mensajes: string[], maquina: string,
 *   tipoPerfil, operarios, cantidad, setupEstandarS, setupComponentesS, piezaEstandarS, totalEstandarS,
 *   horasHombre, pliegues, items}}
 */
export function tiempoDeRenglon(renglon, datos, modelo, resultado = calcularRenglon(renglon, datos)) {
  const { config, materiales } = datos;
  const esCano = renglon.calculoDesarrollo === 'perimetroSegunForma' && renglon.usaLargo !== false;
  const conPerfil = renglon.tipoPieza === 'plegada' || esCano;
  if (!conPerfil || renglon.sinMaterial || resultado.porUnidad) return tiempoSinPerfil(renglon, datos, modelo);

  const mensajes = [];
  const { fila, espesorMm, aviso } = materialDelModelo(renglon, materiales, modelo);
  if (aviso) mensajes.push(aviso);
  const tramos = renglon.tipoPieza === 'plegada' ? tramosDeChapa(renglon, config) : [leerNumero(renglon.largoCm)];
  const tipoPerfil = esCano ? 'ESTANDAR' : tipoDePerfil(renglon, datos, modelo);
  const pliegues = esCano ? pliegesDeCano(renglon.parametros?.forma) : contarPliegues(renglon.perfil, modelo, config);
  const detalles = detallesDelRenglon(renglon, resultado, modelo, config, tramos);
  if (esCano) {
    const metros = leerNumero(renglon.largoCm) / 100;
    if (renglon.parametros?.forma === 'redonda' || renglon.parametros?.forma === 'circular') detalles.push({ codigo: 'CURVADO', cantidad: metros });
    detalles.push({ codigo: 'ENGRAFE', cantidad: metros });
  }
  const cantidad = leerNumero(renglon.cantidad);
  const desarrolloMm = resultado.desarrolloCm ? resultado.desarrolloCm * 10 : null;

  // Cada tramo de chapa distinto es un ítem del modelo; el setup se cuenta una sola vez (el del primero)
  // y los detalles del renglón (tapas, uniones…) van con el primer tramo.
  const largos = [...new Set(tramos.map((t) => Math.round(t * 100) / 100))];
  const items = largos.map((largoCm, i) => {
    const veces = tramos.filter((t) => Math.round(t * 100) / 100 === largoCm).length;
    return calcularItem({
      tipoPerfil, largoM: largoCm / 100, desarrolloMm, material: fila, espesorMm,
      cantidad: Number.isFinite(cantidad) ? cantidad * veces : cantidad,
      pliegues, detalles: i === 0 ? detalles.map((d) => ({ ...d, cantidad: d.cantidad / veces })) : [],
    }, modelo);
  });
  const conError = items.find((it) => !it.calcula);
  if (conError || !items.length) {
    return {
      fuente: 'error', estado: conError?.estado || 'ERROR: sin largo', mensajes, maquina: 'plegadora', tipoPerfil, operarios: 0, cantidad,
      setupEstandarS: 0, setupComponentesS: {}, piezaEstandarS: 0, totalEstandarS: 0, horasHombre: 0, pliegues, items,
    };
  }
  const S = modelo.p.p_supl_total;
  const primero = items[0];
  const canoRedondo = esCano && (renglon.parametros?.forma === 'redonda' || renglon.parametros?.forma === 'circular');
  const hayPliegues = Object.values(pliegues).some((n) => n > 0);
  const setupComponentesS = {};
  for (const c of COMPONENTES_SETUP) setupComponentesS[c.id] = primero.setupNormal[c.id] * (1 + S);
  const piezasTotalesS = items.reduce((s, it) => s + it.itemEstandarS - it.setupEstandarS, 0);
  // Un caño redondo no se pliega: se cilindra (el aviso "sin pliegues" no corresponde).
  const avisos = items.map((it) => it.estado).filter((e) => e !== 'OK' && !(canoRedondo && e.includes('sin pliegues')));
  return {
    fuente: 'mtm',
    estado: avisos[0] || 'OK',
    mensajes: mensajes.concat(avisos.slice(1)),
    maquina: canoRedondo ? 'cilindradora' : (hayPliegues ? 'plegadora' : 'guillotina'),
    tipoPerfil,
    operarios: Math.max(...items.map((it) => it.operarios)),
    cantidad,
    setupEstandarS: primero.setupEstandarS,
    setupComponentesS,
    piezaEstandarS: cantidad > 0 ? piezasTotalesS / cantidad : 0,
    totalEstandarS: primero.setupEstandarS + piezasTotalesS,
    horasHombre: primero.setupEstandarS / 3600 + items.reduce((s, it) => s + (it.horasHombre - it.setupEstandarS / 3600), 0),
    pliegues,
    detalles,
    items,
  };
}

/**
 * Tiempo estándar de una nota: tiempo del pedido + cada renglón.
 * @returns {{pedidoEstandarS, totalEstandarS, totalMin, esperadoMin, horasHombre, renglones: Array, conError: number}}
 */
export function tiempoDeNota(nota, datos, modelo) {
  const renglones = (nota.renglones || []).map((r) => ({ renglonId: r.id, ...tiempoDeRenglon(r, datos, modelo) }));
  const validos = renglones.filter((r) => r.fuente !== 'error');
  const pedido = validos.length ? tiempoDelPedido(modelo).estandarS : 0;
  const totalEstandarS = pedido + validos.reduce((s, r) => s + r.totalEstandarS, 0);
  return {
    pedidoEstandarS: pedido,
    totalEstandarS,
    totalMin: totalEstandarS / 60,
    esperadoMin: totalEstandarS / 60 / modelo.p.p_eficiencia,
    horasHombre: pedido / 3600 + validos.reduce((s, r) => s + r.horasHombre, 0),
    renglones,
    conError: renglones.length - validos.length,
  };
}

/** "1 h 05 min" / "12,5 min" / "45 s" para mostrar. */
export function textoDeTiempo(segundos) {
  if (!Number.isFinite(segundos)) return '—';
  if (segundos < 60) return `${Math.round(segundos)} s`;
  const minutos = segundos / 60;
  if (minutos < 60) return `${String(Math.round(minutos * 10) / 10).replace('.', ',')} min`;
  const horas = Math.floor(minutos / 60);
  return `${horas} h ${String(Math.round(minutos - horas * 60)).padStart(2, '0')} min`;
}
