// =============================================================
// tiempos.js
// TIEMPO ESTÁNDAR de fabricación por ítem y por nota (modelo MTM de la zinguería).
//
// Réplica exacta de la hoja CALCULO de la planilla "Modelo MTM Zinguería"
// (pseudocódigo de la hoja PARAMETROS_API). Todos los números salen de
// datos/tiempos-mtm.json (editable desde Producción > Parámetros de tiempos):
// acá no hay constantes del negocio.
//
//   T_nota  = T_pedido·(1+S) + Σ ítems [ T_setup·(1+S) + Q · T_std_pieza ]
//   T_std_pieza = T_manual·(1+S) + T_máquina·(1 + S·k_máq)
//
// Respecto de la fórmula pedida (setup + Σ cantidad × (fijo + corte + n·pliegue + manipulación
// + detalles) × (1 + suplementos)) el estudio hace 4 ajustes, que se mantienen:
//  a) el corte se cuenta por chapa y por tira (traer y escuadrar la chapa se reparte entre las
//     tiras que salen de ella);
//  b) el pliegue se separa en golpes, volteos y un factor de ajuste por tipo (un cierre a 180°
//     son 2 golpes; un pliegue inverso obliga a voltear);
//  c) el tiempo de máquina va aparte del manual (se decide si lleva suplementos);
//  d) con dos operarios el trabajo manual lleva un factor de coordinación y las horas-hombre se
//     cuentan aparte del tiempo de reloj.
// Y el setup se separa en COMPONENTES (interpretación, chapa, guillotina, plegadora, herramental,
// control, traslado y atado), para saber cuáles se ahorran al agrupar (ver agrupamiento.js).
// =============================================================

/** Componentes del setup de un ítem (tiempo normal, en segundos). */
export const COMPONENTES_SETUP = [
  { id: 'interpretacion', nombre: 'Interpretación del ítem' },
  { id: 'chapa', nombre: 'Selección y verificación de chapa' },
  { id: 'guillotina', nombre: 'Ajuste de guillotina (tope al desarrollo)' },
  { id: 'plegadora', nombre: 'Preparación de plegadora' },
  { id: 'herramental', nombre: 'Cambio de herramental' },
  { id: 'control', nombre: 'Control de primera pieza' },
  { id: 'trasladoAtado', nombre: 'Traslado del carro y atado del lote' },
];

export const TIPOS_PLIEGUE = ['SIMPLE', 'ANGULO', 'CIERRE180', 'INVERSO', 'ESPECIAL'];

/**
 * Arma el modelo listo para calcular: tablas del archivo + cambios guardados + valores derivados.
 * @param {object} tabla    datos/tiempos-mtm.json
 * @param {object} config   datos/config.json (medida de la chapa)
 * @param {{parametros?: object, productosSinPerfil?: Array}|null} cambios  lo editado en la pantalla
 */
export function prepararModelo(tabla, config, cambios = null) {
  const p = {};
  for (const parametro of tabla.parametros) p[parametro.clave] = parametro.valor;
  for (const [clave, valor] of Object.entries(cambios?.parametros || {})) {
    if (clave in p && Number.isFinite(Number(valor))) p[clave] = typeof p[clave] === 'string' ? valor : Number(valor);
    else if (clave in p) p[clave] = valor;
  }
  // Valores derivados: se calculan, no se guardan (una sola fuente).
  p.p_supl_total = ['np', 'fb', 'pie', 'postura', 'fuerza', 'ruido', 'atencion', 'monotonia', 'tedio', 'demoras']
    .reduce((suma, nombre) => suma + (Number(p[`p_supl_${nombre}`]) || 0), 0);
  p.p_t_golpe_guill_s = 60 / p.p_guill_gpm;
  p.p_ancho_chapa_mm = config.anchoChapaCm * 10;
  p.p_margen_escuadre_mm = (config.cantidadDeChapas?.margenEscuadreCm ?? 0) * 10;
  p.p_d_max_mm = p.p_ancho_chapa_mm - p.p_margen_escuadre_mm;
  p.p_l_max_m = Math.min(p.p_guill_largo_max_m, p.p_pleg_largo_max_m);
  const act = {};
  for (const a of tabla.actividades) act[a.id] = a;
  p.p_t_ciclo_manual = act.A21.tmuSinPeso * p.p_tmu_s;

  const tipos = {};
  for (const t of tabla.tiposPliegue) tipos[t.codigo] = t;
  const detalles = {};
  for (const d of tabla.detalles) detalles[d.codigo] = d;
  return {
    version: tabla.version,
    p,
    act,
    tipos,
    detalles,
    materiales: tabla.materiales,
    factorPeso: tabla.factorPeso,
    productosSinPerfil: cambios?.productosSinPerfil || tabla.productosSinPerfil || [],
  };
}

const valorDe = (modelo, numeroOClave) => (typeof numeroOClave === 'string' ? Number(modelo.p[numeroOClave]) : Number(numeroOClave ?? 0));

/** Tiempo normal por unidad y fijo por pieza de un detalle (hoja TIPOS_PLIEGUE_Y_DETALLES). */
export function tiempoDeDetalle(modelo, codigo) {
  const d = modelo.detalles[codigo];
  if (!d) return null;
  const tmu = modelo.p.p_tmu_s;
  const proceso = valorDe(modelo, d.proceso?.numerador) / (d.proceso?.denominador ? valorDe(modelo, d.proceso.denominador) : 1);
  return {
    porUnidad: (d.actividadPorUnidad ? modelo.act[d.actividadPorUnidad].tmuSinPeso * tmu : 0) + proceso,
    fijoPorPieza: d.actividadFijaPorPieza ? modelo.act[d.actividadFijaPorPieza].tmuSinPeso * tmu : 0,
  };
}

/**
 * Datos de cálculo de un material (columnas grises de la hoja MATERIALES).
 * @param {object} fila  fila de modelo.materiales; espesorMm se puede reemplazar por el del calibre real
 */
export function datosDeMaterial(modelo, fila, espesorMm = fila.espesorMm) {
  const p = modelo.p;
  const pesoM2 = (espesorMm / 1000) * fila.densidadKgM3 + fila.recubrimientoKgM2;
  const aberturaV = Math.max(p.p_v_min_mm, p.p_factor_v * espesorMm);
  const toneladasPorMetro = (p.p_coef_flexion * fila.rmMpa * espesorMm ** 2) / aberturaV / p.p_g;
  const cicloHidraulico = p.p_carrera_aprox_mm / p.p_v_aprox_mm_s
    + (aberturaV / 2 + espesorMm) / p.p_v_trabajo_mm_s
    + (p.p_carrera_aprox_mm + aberturaV / 2 + espesorMm) / p.p_v_retorno_mm_s
    + p.p_t_dwell_s + p.p_t_topes_s;
  return {
    pesoM2,
    aberturaV,
    toneladasPorMetro,
    aptoGuillotina: espesorMm * fila.factorCorte <= p.p_guill_esp_max_mm,
    cicloPlegado: p.p_tipo_plegadora === 'HIDRAULICA' ? cicloHidraulico : p.p_t_ciclo_manual,
    factorManipulacion: fila.factorManipulacion,
    factorPlegado: fila.factorPlegado,
  };
}

/** Constante estática y factor dinámico de MTM-1 según el peso por mano (MATCH aproximado de la planilla). */
export function factorDePeso(modelo, pesoPorManoKg) {
  const buscado = Math.max(0, pesoPorManoKg - 0.000001);
  let elegido = modelo.factorPeso[0];
  for (const fila of modelo.factorPeso) if (fila.desdeKg <= buscado) elegido = fila;
  return elegido;
}

/**
 * Tiempo de un ítem de la planilla (fila de NOTA_PEDIDO → fila de CALCULO).
 * @param {{tipoPerfil?: 'ESTANDAR'|'ESPECIAL', largoM: number, desarrolloMm: number, material: object|null,
 *   espesorMm?: number, cantidad: number, pliegues?: object, detalles?: Array<{codigo: string, cantidad: number}>}} item
 * @returns {object} estado ('OK' | 'AVISO: …' | 'ERROR: …'), tiempos normales y estándar (s), etc.
 */
export function calcularItem(item, modelo) {
  const p = modelo.p;
  const S = p.p_supl_total;
  const tmu = p.p_tmu_s;
  const a = (id, parte = 'tmuSinPeso') => modelo.act[id][parte];

  const error = validarItem(item, modelo);
  if (error) return { estado: `ERROR: ${error}`, error, calcula: false, setupEstandarS: 0, piezaEstandarS: 0, itemEstandarS: 0, horasHombre: 0 };

  const L = Number(item.largoM);
  const D = Number(item.desarrolloMm);
  const Q = Number(item.cantidad);
  const especial = item.tipoPerfil === 'ESPECIAL';
  const mat = datosDeMaterial(modelo, item.material, item.espesorMm ?? item.material.espesorMm);

  const peso = (L * D / 1000) * mat.pesoM2;
  const operarios = L > p.p_l_umbral_2op_m || peso > p.p_peso_max_1op_kg ? 2 : 1;
  const { sc, df } = factorDePeso(modelo, peso / (2 * operarios));
  const fman = mat.factorManipulacion;
  const fpl = mat.factorPlegado;
  const ksin = operarios === 2 ? p.p_k_sinc_2op : 1;
  const excedente = operarios === 1 ? Math.max(0, L - p.p_l_ref_manip_m) : 0;
  const tiras = Math.max(1, Math.floor(p.p_d_max_mm / D));
  const chapas = Math.ceil(Q / tiras);

  const n = item.pliegues || {};
  let pliegues = 0; let golpes = 0; let golpesPonderados = 0; let volteos = 0; let herramental = 0;
  for (const codigo of TIPOS_PLIEGUE) {
    const cantidad = Number(n[codigo]) || 0;
    const tipo = modelo.tipos[codigo];
    pliegues += cantidad;
    golpes += cantidad * tipo.golpes;
    golpesPonderados += cantidad * tipo.golpes * tipo.factor;
    volteos += cantidad * tipo.volteos;
    if (cantidad > 0) herramental += tipo.herramental;
  }
  const cotas = pliegues + 1;
  const tonelaje = mat.toneladasPorMetro * L;

  // ---- Setup del ítem (tiempo normal), por componentes ----
  const setup = {
    interpretacion: a('A02') * tmu + (especial ? p.p_t_interp_item_esp_s : p.p_t_interp_item_std_s),
    chapa: a('A03') * tmu,
    guillotina: p.p_setup_corte_s,
    plegadora: pliegues > 0 ? (especial ? p.p_setup_pleg_esp_base_s + pliegues * p.p_setup_pleg_esp_pliegue_s : p.p_setup_pleg_std_s) : 0,
    herramental: pliegues > 0 ? herramental * p.p_cambio_herr_s : 0,
    control: (a('A11') + cotas * a('A12')) * tmu,
    trasladoAtado: a('A06') * tmu + p.p_t_atado_item_s,
  };
  const setupNormalS = Object.values(setup).reduce((s, v) => s + v, 0);

  // ---- Por pieza (tiempo normal) ----
  let detallesS = 0;
  for (const d of item.detalles || []) {
    const t = tiempoDeDetalle(modelo, d.codigo);
    if (t && Number(d.cantidad) > 0) detallesS += Number(d.cantidad) * t.porUnidad + t.fijoPorPieza;
  }
  const pieza = {
    corteManual: ((chapas * a('A04') + Q * a('A05')) * tmu * fman * ksin) / Q,
    corteMaquina: ((chapas * (1 + p.p_corte_largo_en_planta) + Q) * p.p_t_golpe_guill_s) / Q,
    cargaDescarga: (a('A07') + a('A13')) * tmu * fman * ksin,
    plegadoManual: golpesPonderados * (a('A08') + df * a('A08', 'tmuConPeso') + sc * a('A08', 'movimientosConPeso')) * tmu * fpl * ksin,
    plegadoMaquina: golpes * mat.cicloPlegado * fpl,
    volteos: volteos * (a('A09') + df * a('A09', 'tmuConPeso') + sc * a('A09', 'movimientosConPeso')) * tmu * fman * ksin,
    lateral: excedente * a('A10') * tmu * (golpes * p.p_recorridos_lat_pliegue + volteos),
    control: p.p_frec_control * (a('A11') + cotas * a('A12')) * tmu,
    detalles: detallesS,
    deposito: a('A14') * tmu * fman * ksin,
  };
  const manualS = pieza.corteManual + pieza.cargaDescarga + pieza.plegadoManual + pieza.volteos + pieza.lateral + pieza.control + pieza.detalles + pieza.deposito;
  const maquinaS = pieza.corteMaquina + pieza.plegadoMaquina;
  const piezaEstandarS = manualS * (1 + S) + maquinaS * (1 + S * p.p_supl_en_maquina);
  const setupEstandarS = setupNormalS * (1 + S);
  const itemEstandarS = setupEstandarS + Q * piezaEstandarS;

  let estado = 'OK';
  if (!mat.aptoGuillotina) estado = 'AVISO: el espesor supera la capacidad de la guillotina';
  else if (tonelaje > p.p_pleg_tonelaje_t) estado = 'AVISO: el tonelaje requerido supera la capacidad de la plegadora';
  else if (peso / operarios > p.p_peso_max_1op_kg) estado = 'AVISO: peso por operario mayor al límite, usar ayuda mecánica';
  else if (pliegues === 0) estado = 'AVISO: ítem sin pliegues (solo corte)';

  return {
    estado,
    calcula: true,
    operarios,
    pesoKg: peso,
    tiras,
    chapas,
    aprovechamiento: (Q * D) / (chapas * p.p_ancho_chapa_mm),
    pliegues,
    golpes,
    volteos,
    cambiosHerramental: herramental,
    tonelaje,
    setupNormal: setup,
    setupNormalS,
    setupEstandarS,
    pieza,
    manualS,
    maquinaS,
    piezaNormalS: manualS + maquinaS,
    piezaEstandarS,
    itemEstandarS,
    horasHombre: (setupEstandarS + Q * piezaEstandarS * operarios) / 3600,
    segundosPorGolpe: golpes > 0 ? ((pieza.plegadoManual + pieza.plegadoMaquina) / golpes) * (1 + S) : 0,
  };
}

/** Los controles de error de la planilla (columna "Error de datos"), con mensajes claros. */
export function validarItem(item, modelo) {
  const p = modelo.p;
  const vacio = (v) => v === null || v === undefined || v === '' || Number.isNaN(v);
  if (vacio(item.largoM) || vacio(item.desarrolloMm) || !item.material || vacio(item.cantidad)) {
    const faltan = [vacio(item.largoM) && 'largo', vacio(item.desarrolloMm) && 'desarrollo', !item.material && 'material', vacio(item.cantidad) && 'cantidad'].filter(Boolean);
    return `faltan datos obligatorios (${faltan.join(', ')})`;
  }
  if (![item.largoM, item.desarrolloMm, item.cantidad].every((v) => Number.isFinite(Number(v)))) return 'largo, desarrollo y cantidad deben ser números';
  if (item.largoM < p.p_l_min_m || item.largoM > p.p_l_max_m) return `largo fuera de rango (de ${p.p_l_min_m} a ${p.p_l_max_m} m)`;
  if (item.desarrolloMm < p.p_d_min_mm || item.desarrolloMm > p.p_d_max_mm) return `desarrollo fuera de rango (de ${p.p_d_min_mm} a ${p.p_d_max_mm} mm)`;
  if (item.cantidad < 1 || !Number.isInteger(Number(item.cantidad))) return 'la cantidad debe ser un entero mayor o igual a 1';
  return null;
}

/** Tiempo propio del pedido (lectura de la nota, traslado a depósito, planificación y registro). */
export function tiempoDelPedido(modelo) {
  const p = modelo.p;
  const normalS = (modelo.act.A01.tmuSinPeso + modelo.act.A15.tmuSinPeso) * p.p_tmu_s + p.p_t_decision_pedido_s + p.p_t_registro_pedido_s;
  return { normalS, estandarS: normalS * (1 + p.p_supl_total) };
}

/**
 * Nota de la planilla: tiempo del pedido + ítems válidos (los ítems con error no se suman).
 * @returns {{pedidoEstandarS, totalEstandarS, totalMin, horasHombre, esperadoMin, items, conError}}
 */
export function calcularNotaMtm(items, modelo) {
  const resultados = items.map((item) => calcularItem(item, modelo));
  const validos = resultados.filter((r) => r.calcula);
  const pedido = validos.length ? tiempoDelPedido(modelo).estandarS : 0;
  const totalEstandarS = pedido + validos.reduce((s, r) => s + r.itemEstandarS, 0);
  return {
    pedidoEstandarS: pedido,
    totalEstandarS,
    totalMin: totalEstandarS / 60,
    horasHombre: pedido / 3600 + validos.reduce((s, r) => s + r.horasHombre, 0),
    esperadoMin: totalEstandarS / 60 / modelo.p.p_eficiencia,
    items: resultados,
    conError: resultados.filter((r) => !r.calcula).length,
  };
}
