// =============================================================
// produccion.js
// Lógica de PRODUCCIÓN (sin pantalla, se prueba con node --test):
// trabajos pendientes, estados, asignación a operarios por día y turno, tiempo real
// (cronómetro o casilla HECHA), eficiencia, alertas, carga, material y KPIs.
//
// Dónde vive cada dato (una sola fuente):
// - La NOTA (emitida, no cambia): cliente, renglones, fecha de entrega y prioridad pedidas.
// - El REGISTRO de producción (uno por nota, en almacenamiento.js): a quién y cuándo se
//   asignó cada renglón, orden en la cola, HECHA, eventos del cronómetro, tiempo estándar
//   congelado al terminar e historial.
// - El ESTADO (pendiente / programada / en curso / hecha / demorada) NO se guarda: se calcula.
// =============================================================

import { leerNumero, redondear } from './numeros.js';
import { tiempoDeNota, materialDelModelo } from './tiemposRenglon.js';
import { datosDeMaterial } from './tiempos.js';
import { calcularRenglon } from './calculoRenglon.js';
import { cantidadDeLaNota, consumoFisico } from './chapas.js';
import { ahorroEntre } from './agrupamiento.js';

export const PRIORIDADES = [
  { valor: 'normal', texto: 'Normal' },
  { valor: 'urgente', texto: 'Urgente' },
];

export const ESTADOS = [
  { valor: 'pendiente', texto: 'Pendiente', ayuda: 'Emitida, todavía sin asignar a un operario' },
  { valor: 'programada', texto: 'Programada', ayuda: 'Todos los renglones tienen operario y día' },
  { valor: 'en_curso', texto: 'En curso', ayuda: 'Algún renglón empezado o terminado' },
  { valor: 'hecha', texto: 'Hecha', ayuda: 'Todos los renglones terminados' },
  { valor: 'demorada', texto: 'Demorada', ayuda: 'Pasó la fecha de entrega o lo programado termina después' },
];

// ---------- fechas ----------

/** 'aaaa-mm-dd' de una fecha (hora local). */
export function diaDe(fecha) {
  const f = fecha instanceof Date ? fecha : new Date(fecha);
  return `${f.getFullYear()}-${String(f.getMonth() + 1).padStart(2, '0')}-${String(f.getDate()).padStart(2, '0')}`;
}

function fechaLocal(dia) {
  const [a, m, d] = dia.split('-').map(Number);
  return new Date(a, m - 1, d);
}

export function esHabil(dia, diasHabiles = [1, 2, 3, 4, 5]) {
  return diasHabiles.includes(fechaLocal(dia).getDay());
}

/** Suma n días hábiles a 'aaaa-mm-dd' (n = 0 → el mismo día si es hábil, si no el siguiente). */
export function sumarDiasHabiles(dia, n, diasHabiles = [1, 2, 3, 4, 5]) {
  const f = fechaLocal(dia);
  while (!diasHabiles.includes(f.getDay())) f.setDate(f.getDate() + 1);
  let quedan = n;
  while (quedan > 0) {
    f.setDate(f.getDate() + 1);
    if (diasHabiles.includes(f.getDay())) quedan -= 1;
  }
  return diaDe(f);
}

/** Días hábiles desde hoy hasta la fecha (negativo si ya pasó). */
export function diasHabilesHasta(hoy, dia, diasHabiles = [1, 2, 3, 4, 5]) {
  if (dia === hoy) return 0;
  const signo = dia > hoy ? 1 : -1;
  const f = fechaLocal(hoy);
  let cuenta = 0;
  while (diaDe(f) !== dia) {
    f.setDate(f.getDate() + signo);
    if (diasHabiles.includes(f.getDay())) cuenta += signo;
    if (Math.abs(cuenta) > 4000) break;
  }
  return cuenta;
}

/** Semana ISO 'aaaa-Sss' y mes 'aaaa-mm' (para la eficiencia por período). */
export function claveDePeriodo(dia, periodo) {
  if (periodo === 'mes') return dia.slice(0, 7);
  if (periodo === 'semana') {
    const f = fechaLocal(dia);
    const jueves = new Date(f);
    jueves.setDate(f.getDate() + 3 - ((f.getDay() + 6) % 7));
    const primero = new Date(jueves.getFullYear(), 0, 4);
    const semana = 1 + Math.round(((jueves - primero) / 86400000 - 3 + ((primero.getDay() + 6) % 7)) / 7);
    return `${jueves.getFullYear()}-S${String(semana).padStart(2, '0')}`;
  }
  return dia;
}

/** Fecha de entrega de la nota: la pedida o, si no tiene, la emisión + plazo por defecto (días hábiles). */
export function fechaEntregaDe(nota, prod) {
  if (nota.fechaEntrega) return nota.fechaEntrega;
  const base = diaDe(nota.fechaEmision || nota.fechaCreacion || new Date());
  return sumarDiasHabiles(base, prod.plazoPorDefectoDiasHabiles ?? 5, prod.diasHabiles);
}

// ---------- registro de producción ----------

export function registroVacio(notaId, demo = false) {
  return { notaId, demo: Boolean(demo), orden: null, renglones: {}, historial: [] };
}

function copiar(registro) {
  return JSON.parse(JSON.stringify(registro));
}

function anotar(registro, quien, accion, detalle, hora) {
  registro.historial.push({ hora, rol: quien?.rol || null, usuario: quien?.nombre || null, accion, detalle });
}

function renglonDe(registro, renglonId) {
  registro.renglones[renglonId] ||= { operarioId: null, fecha: null, turno: null, loteId: null, hecha: false, horaHecha: null, eventos: [] };
  return registro.renglones[renglonId];
}

/** Asigna (o desasigna con operarioId null) un renglón a un operario, día y turno. */
export function asignarRenglon(registro, renglonId, { operarioId, fecha, turno, loteId }, quien, hora = new Date().toISOString()) {
  const nuevo = copiar(registro);
  const r = renglonDe(nuevo, renglonId);
  if (r.hecha) throw new Error('Ese renglón ya está HECHO: primero hay que desmarcarlo');
  r.operarioId = operarioId || null;
  r.fecha = operarioId ? fecha || null : null;
  r.turno = operarioId ? turno || null : null;
  if (loteId !== undefined) r.loteId = loteId;
  anotar(nuevo, quien, operarioId ? 'asignado' : 'desasignado', operarioId ? `${renglonId} → ${operarioId} ${fecha || ''} ${turno || ''}`.trim() : renglonId, hora);
  return nuevo;
}

/** Tiempo real (min) a partir del cronómetro: suma de los tramos inicio/reanudar → pausa/fin. */
export function tiempoRealDeEventos(eventos) {
  let total = 0;
  let desde = null;
  for (const e of eventos || []) {
    if ((e.tipo === 'inicio' || e.tipo === 'reanudar') && desde === null) desde = Date.parse(e.hora);
    if ((e.tipo === 'pausa' || e.tipo === 'fin') && desde !== null) { total += Date.parse(e.hora) - desde; desde = null; }
  }
  return redondear(total / 60000, 2);
}

/** Estado del cronómetro del renglón: 'sin_empezar' | 'corriendo' | 'pausado' | 'terminado'. */
export function estadoDelCronometro(renglonRegistro) {
  const eventos = renglonRegistro?.eventos || [];
  if (renglonRegistro?.hecha) return 'terminado';
  const ultimo = eventos[eventos.length - 1];
  if (!ultimo) return 'sin_empezar';
  if (ultimo.tipo === 'pausa') return 'pausado';
  if (ultimo.tipo === 'fin') return 'terminado';
  return 'corriendo';
}

/** Botones del cronómetro: inicio → pausa ⇄ reanudar → fin. Error claro si la secuencia no corresponde. */
export function registrarEvento(registro, renglonId, tipo, quien, hora = new Date().toISOString()) {
  const nuevo = copiar(registro);
  const r = renglonDe(nuevo, renglonId);
  const estado = estadoDelCronometro(r);
  const permitido = { inicio: ['sin_empezar'], pausa: ['corriendo'], reanudar: ['pausado'], fin: ['corriendo', 'pausado'] };
  if (!permitido[tipo]) throw new Error(`Acción desconocida: ${tipo}`);
  if (!permitido[tipo].includes(estado)) {
    const textos = { sin_empezar: 'todavía no empezó', corriendo: 'ya está corriendo', pausado: 'está en pausa', terminado: 'ya está terminado' };
    throw new Error(`No se puede "${tipo}": el trabajo ${textos[estado]}`);
  }
  // Fin estando en pausa: se cierra sin sumar el tiempo de la pausa.
  r.eventos.push({ tipo: tipo === 'fin' && estado === 'pausado' ? 'fin_en_pausa' : tipo, hora, operarioId: quien?.operarioId || r.operarioId });
  anotar(nuevo, quien, `cronómetro: ${tipo}`, renglonId, hora);
  return nuevo;
}

/**
 * Tiempo real estimado SOLO con la casilla HECHA (sin cronómetro): desde la HECHA anterior
 * del mismo operario ese día (o el inicio del turno) hasta esta. LIMITACIÓN (se muestra en
 * pantalla): incluye pausas, esperas, consultas y cualquier tarea no registrada; si se marcan
 * varias juntas al final, la primera se lleva todo el tiempo y las otras casi nada.
 * @param {string} horaHecha  ISO
 * @param {string[]} horasAnteriores  HECHAS anteriores del mismo operario ese día (ISO)
 * @param {string} inicioTurno 'hh:mm'
 */
export function tiempoRealPorCasilla(horaHecha, horasAnteriores, inicioTurno) {
  const fin = Date.parse(horaHecha);
  const dia = new Date(fin);
  const [h, m] = String(inicioTurno || '07:00').split(':').map(Number);
  const inicio = new Date(dia.getFullYear(), dia.getMonth(), dia.getDate(), h, m).getTime();
  const anteriores = horasAnteriores.map((x) => Date.parse(x)).filter((x) => x < fin && x >= inicio);
  const desde = anteriores.length ? Math.max(...anteriores) : inicio;
  return redondear(Math.max(0, fin - desde) / 60000, 2);
}

/**
 * Marca o desmarca HECHA (con la hora automática). Al marcar congela el tiempo estándar del
 * renglón (el del momento, con el ahorro del lote) y calcula el real: con el cronómetro si se
 * usó; si no, por la casilla (ver la limitación en tiempoRealPorCasilla).
 */
export function marcarHecha(registro, renglonId, { hecha, tiempoEstandarMin, ahorroLoteMin = 0, horasAnterioresDelOperario = [], inicioTurno }, quien, hora = new Date().toISOString()) {
  const nuevo = copiar(registro);
  const r = renglonDe(nuevo, renglonId);
  if (!hecha) {
    Object.assign(r, { hecha: false, horaHecha: null, tiempoEstandarMin: null, ahorroLoteMin: null, tiempoRealMin: null, origenReal: null });
    r.eventos = r.eventos.filter((e) => e.tipo !== 'fin' && e.tipo !== 'fin_en_pausa');
    anotar(nuevo, quien, 'desmarcado HECHA', renglonId, hora);
    return nuevo;
  }
  if (!r.operarioId && !quien?.operarioId) throw new Error('Antes de marcar HECHA el renglón tiene que tener un operario');
  if (!r.operarioId) r.operarioId = quien.operarioId;
  if (!r.fecha) r.fecha = diaDe(hora);
  const cronometro = estadoDelCronometro(r);
  if (cronometro === 'corriendo') r.eventos.push({ tipo: 'fin', hora, operarioId: r.operarioId });
  const usoCronometro = r.eventos.some((e) => e.tipo === 'inicio');
  r.hecha = true;
  r.horaHecha = hora;
  r.tiempoEstandarMin = redondear(tiempoEstandarMin, 2);
  r.ahorroLoteMin = redondear(ahorroLoteMin, 2);
  r.tiempoRealMin = usoCronometro ? tiempoRealDeEventos(r.eventos) : tiempoRealPorCasilla(hora, horasAnterioresDelOperario, inicioTurno);
  r.origenReal = usoCronometro ? 'cronometro' : 'casilla';
  anotar(nuevo, quien, 'HECHA', `${renglonId} (estándar ${r.tiempoEstandarMin} min, real ${r.tiempoRealMin} min por ${r.origenReal})`, hora);
  return nuevo;
}

// ---------- trabajos (renglones de notas emitidas) ----------

/** Firma del perfil: dos renglones con la misma firma usan el mismo programa de plegadora. */
export function firmaDePerfil(renglon) {
  if (renglon.tipoPieza === 'plegada' || renglon.usaPerfil) {
    const tramos = (renglon.perfil?.tramos || []).map((t) => [redondear(leerNumero(t.medidaCm), 1), redondear(leerNumero(t.anguloPliegue), 0), t.sentido || 'izquierda', t.tipo || 'normal'].join(':'));
    const finales = renglon.conPendiente ? (renglon.perfil?.tramos || []).map((t) => `${t.medidaFinalCm ?? ''}/${t.anguloPliegueFinal ?? ''}`).join(',') : '';
    return `P|${tramos.join(';')}${finales ? `|${finales}` : ''}`;
  }
  return `U|${renglon.plantillaId}|${JSON.stringify(renglon.parametros || {})}`;
}

/** Atributos para agrupar (ver agrupamiento.js). */
export function atributosDeTrabajo(renglon, resultado, tiempo, datos, modelo) {
  const calibre = datos.materiales.calibres.find((c) => c.id === renglon.calibreId);
  const espesorMm = renglon.sinMaterial ? null : calibre?.espesorMm ?? null;
  const pl = tiempo.pliegues;
  let herramental = 'sin plegado';
  if (pl && espesorMm) {
    const fila = materialDelModelo(renglon, datos.materiales, modelo).fila;
    const v = fila ? datosDeMaterial(modelo, fila, espesorMm).aberturaV : null;
    herramental = `V${v}${pl.ESPECIAL ? '+especial' : ''}${pl.CIERRE180 ? '+dobladillo' : ''}`;
  }
  return {
    producto: renglon.plantillaId,
    perfil: firmaDePerfil(renglon),
    tipoPerfil: tiempo.tipoPerfil,
    desarrolloMm: resultado.desarrolloCm ? redondear(resultado.desarrolloCm * 10, 1) : null,
    material: renglon.sinMaterial ? 'sin material' : [renglon.materialId, renglon.calibreId, renglon.terminacion, renglon.terminacion === 'P' ? renglon.colorId : ''].join('|'),
    espesorMm,
    largoCm: leerNumero(renglon.largoCm) || 0,
    pliegues: pl ? `S${pl.SIMPLE} A${pl.ANGULO} C${pl.CIERRE180} I${pl.INVERSO} E${pl.ESPECIAL}` : 'sin pliegues',
    herramental,
  };
}

/**
 * Un trabajo por renglón de cada nota emitida, con su tiempo estándar y lo registrado en producción.
 * El tiempo propio del pedido (leer la nota, llevarla a depósito) se suma al primer renglón de cada nota.
 * @param {Array} notas  notas emitidas
 * @param {object} registros  { notaId: registro }
 * @param {{datos, modelo, prod}} contexto
 */
export function armarTrabajos(notas, registros, { datos, modelo, prod }) {
  const trabajos = [];
  for (const nota of notas) {
    if (nota.estado !== 'emitida') continue;
    const registro = registros[nota.id] || registroVacio(nota.id, nota.demo);
    const tiempoNota = tiempoDeNota(nota, datos, modelo);
    const fechaEntrega = fechaEntregaDe(nota, prod);
    nota.renglones.forEach((renglon, i) => {
      const resultado = calcularRenglon(renglon, datos);
      const tiempo = tiempoNota.renglones[i];
      const r = registro.renglones[renglon.id] || {};
      const pedidoMin = i === 0 ? tiempoNota.pedidoEstandarS / 60 : 0;
      const setupComponentesMin = {};
      for (const [id, s] of Object.entries(tiempo.setupComponentesS || {})) setupComponentesMin[id] = s / 60;
      trabajos.push({
        clave: `${nota.id}/${renglon.id}`,
        notaId: nota.id,
        renglonId: renglon.id,
        indice: i,
        numeroNota: nota.numero,
        cliente: nota.cliente,
        sucursalId: nota.sucursalId,
        demo: Boolean(nota.demo),
        descripcion: renglon.calculado?.descripcion || resultado.descripcion,
        piezas: leerNumero(renglon.cantidad) || 0,
        cantidad: cantidadDeLaNota(renglon, resultado, datos.config),
        fechaEntrega,
        prioridad: nota.prioridad || 'normal',
        orden: registro.orden,
        maquina: tiempo.maquina,
        tiempoValido: tiempo.fuente !== 'error',
        estadoTiempo: tiempo.estado,
        operarios: tiempo.operarios,
        minutos: tiempo.totalEstandarS / 60 + pedidoMin,
        setupMin: tiempo.setupEstandarS / 60,
        setupComponentesMin,
        pedidoMin,
        atributos: atributosDeTrabajo(renglon, resultado, tiempo, datos, modelo),
        renglon,
        resultado,
        // lo registrado
        operarioId: r.operarioId || null,
        fecha: r.fecha || null,
        turno: r.turno || null,
        loteId: r.loteId || null,
        hecha: Boolean(r.hecha),
        horaHecha: r.horaHecha || null,
        cronometro: estadoDelCronometro(r),
        tiempoEstandarMin: r.tiempoEstandarMin ?? null,
        tiempoRealMin: r.tiempoRealMin ?? null,
        origenReal: r.origenReal || null,
      });
    });
  }
  return trabajos;
}

/** Estado de un trabajo (renglón). */
export function estadoDeTrabajo(t) {
  if (t.hecha) return 'hecha';
  if (t.cronometro === 'corriendo' || t.cronometro === 'pausado') return 'en_curso';
  if (t.operarioId && t.fecha) return 'programada';
  return 'pendiente';
}

/**
 * Estado de la nota a partir de sus trabajos. "demorada" (calculado, no se guarda): no terminada y
 * pasó la entrega, o algún renglón está programado para después de la entrega.
 */
export function estadoDeNota(trabajosDeLaNota, hoy) {
  const estados = trabajosDeLaNota.map(estadoDeTrabajo);
  const entrega = trabajosDeLaNota[0]?.fechaEntrega;
  let base = 'pendiente';
  if (estados.every((e) => e === 'hecha')) base = 'hecha';
  else if (estados.some((e) => e === 'hecha' || e === 'en_curso')) base = 'en_curso';
  else if (estados.every((e) => e === 'programada')) base = 'programada';
  if (base !== 'hecha' && entrega) {
    const programadoDespues = trabajosDeLaNota.some((t) => !t.hecha && t.fecha && t.fecha > entrega);
    if (entrega < hoy || programadoDespues) return 'demorada';
  }
  return base;
}

/** Notas con sus trabajos, estado y tiempos (para el tablero). */
export function notasConEstado(trabajos, hoy) {
  const porNota = new Map();
  for (const t of trabajos) {
    if (!porNota.has(t.notaId)) porNota.set(t.notaId, []);
    porNota.get(t.notaId).push(t);
  }
  return [...porNota.values()].map((lista) => {
    const hechos = lista.filter((t) => t.hecha);
    return {
      notaId: lista[0].notaId,
      numeroNota: lista[0].numeroNota,
      cliente: lista[0].cliente,
      sucursalId: lista[0].sucursalId,
      fechaEntrega: lista[0].fechaEntrega,
      prioridad: lista[0].prioridad,
      orden: lista[0].orden,
      demo: lista[0].demo,
      trabajos: lista,
      estado: estadoDeNota(lista, hoy),
      minutos: lista.reduce((s, t) => s + t.minutos, 0),
      minutosPendientes: lista.filter((t) => !t.hecha).reduce((s, t) => s + t.minutos, 0),
      avance: lista.length ? hechos.length / lista.length : 0,
      operarios: [...new Set(lista.map((t) => t.operarioId).filter(Boolean))],
      ultimaFecha: lista.map((t) => t.fecha).filter(Boolean).sort().pop() || null,
      terminada: hechos.length === lista.length ? hechos.map((t) => t.horaHecha).sort().pop() : null,
    };
  });
}

/** Orden de la cola del jefe: primero el orden manual (arrastrar), después urgentes y entrega. */
export function ordenarCola(notas) {
  return [...notas].sort((a, b) => {
    const oa = Number.isFinite(a.orden) ? a.orden : Infinity;
    const ob = Number.isFinite(b.orden) ? b.orden : Infinity;
    if (oa !== ob) return oa - ob;
    return (a.prioridad === 'urgente' ? 0 : 1) - (b.prioridad === 'urgente' ? 0 : 1)
      || String(a.fechaEntrega).localeCompare(String(b.fechaEntrega))
      || String(a.numeroNota).localeCompare(String(b.numeroNota), 'es', { numeric: true });
  });
}

// ---------- carga y asignación automática ----------

/** Capacidad (min) de un operario en un turno. */
export function capacidadDeOperario(operario, prod) {
  return prod.turnos.find((t) => t.id === operario.turno)?.minutosDisponibles ?? 450;
}

/** Minutos asignados por operario y día: { operarioId: { dia: minutos } } (sin los HECHOS si se pide). */
export function cargaPorOperarioYDia(trabajos, { soloPendientes = false } = {}) {
  const carga = {};
  for (const t of trabajos) {
    if (!t.operarioId || !t.fecha || (soloPendientes && t.hecha)) continue;
    carga[t.operarioId] ||= {};
    carga[t.operarioId][t.fecha] = (carga[t.operarioId][t.fecha] || 0) + (t.minutosEnLote ?? t.minutos);
  }
  return carga;
}

/** Minutos asignados por máquina y día (cada trabajo en su máquina principal). */
export function cargaPorMaquinaYDia(trabajos) {
  const carga = {};
  for (const t of trabajos) {
    if (!t.fecha) continue;
    carga[t.maquina] ||= {};
    carga[t.maquina][t.fecha] = (carga[t.maquina][t.fecha] || 0) + (t.minutosEnLote ?? t.minutos);
  }
  return carga;
}

/** Capacidad por máquina y día: máquinas iguales × minutos por turno × turnos con operarios. */
export function capacidadDeMaquina(maquina, prod, operarios) {
  const turnos = new Set(operarios.filter((o) => o.activo !== false && o.maquinas.includes(maquina.id)).map((o) => o.turno));
  return (maquina.cantidad || 1) * (maquina.minutosPorTurno || 450) * Math.max(1, turnos.size);
}

/**
 * Minutos de cada trabajo dentro de su lote: el estándar menos el setup que se ahorra por
 * venir después de otro igual (se reparte al que lo ahorra).
 * @param {Array} lotes  [{trabajos (en orden)}]
 * @returns {Map<clave, {loteId, minutosEnLote, ahorroMin}>}
 */
export function minutosEnLotes(lotes, toleranciaMm = 0) {
  const mapa = new Map();
  for (const lote of lotes) {
    lote.trabajos.forEach((t, i) => {
      const ahorro = i === 0 ? 0 : ahorroEntre(lote.trabajos[i - 1], t, toleranciaMm);
      mapa.set(t.clave, { loteId: lote.trabajos.length > 1 ? lote.id : null, minutosEnLote: t.minutos - ahorro, ahorroMin: ahorro });
    });
  }
  return mapa;
}

/**
 * Asignación automática (heurística de lista, la más usada en talleres): los lotes en orden
 * de urgencia y entrega van, enteros, al operario habilitado para esa máquina que los termina
 * antes, el primer día hábil con lugar desde "desde". Respeta lo ya asignado.
 * @returns {Array<{clave, operarioId, fecha, turno, loteId}>}
 */
export function asignarAutomaticamente(lotes, trabajosAsignados, prod, operarios, desde) {
  const activos = operarios.filter((o) => o.activo !== false);
  const carga = cargaPorOperarioYDia(trabajosAsignados.filter((t) => !t.hecha));
  const usado = (op, dia) => carga[op]?.[dia] || 0;
  const sumar = (op, dia, min) => { carga[op] ||= {}; carga[op][dia] = (carga[op][dia] || 0) + min; };
  const asignaciones = [];
  const ordenados = [...lotes].sort((a, b) => ((a.resumen.prioridad === 'urgente' ? 0 : 1) - (b.resumen.prioridad === 'urgente' ? 0 : 1))
    || String(a.resumen.fechaEntrega).localeCompare(String(b.resumen.fechaEntrega)));
  for (const lote of ordenados) {
    const pendientes = lote.trabajos.filter((t) => !t.hecha && !t.operarioId);
    if (!pendientes.length) continue;
    const minutos = pendientes.reduce((s, t) => s + (t.minutosEnLote ?? t.minutos), 0);
    const candidatos = activos.filter((o) => o.maquinas.includes(lote.resumen.maquina));
    if (!candidatos.length) continue;
    let mejor = null;
    for (const op of candidatos) {
      const capacidad = capacidadDeOperario(op, prod);
      let dia = sumarDiasHabiles(desde, 0, prod.diasHabiles);
      for (let intentos = 0; intentos < 60; intentos++) {
        const libre = capacidad - usado(op.id, dia);
        if (libre >= Math.min(minutos, capacidad)) break;
        dia = sumarDiasHabiles(dia, 1, prod.diasHabiles);
      }
      const fin = `${dia}|${String(Math.round((usado(op.id, dia) + minutos) * 100)).padStart(9, '0')}`;
      if (!mejor || fin < mejor.fin) mejor = { op, dia, fin };
    }
    for (const t of pendientes) {
      asignaciones.push({ clave: t.clave, notaId: t.notaId, renglonId: t.renglonId, operarioId: mejor.op.id, fecha: mejor.dia, turno: mejor.op.turno, loteId: lote.trabajos.length > 1 ? lote.id : null });
    }
    sumar(mejor.op.id, mejor.dia, minutos);
  }
  return asignaciones;
}

// ---------- eficiencia ----------

/**
 * Eficiencia = tiempo estándar de lo terminado ÷ tiempo real, por operario y período.
 * Solo cuenta trabajos HECHOS con tiempo real > 0.
 * @param {'dia'|'semana'|'mes'} periodo
 * @returns {Array<{operarioId, periodo, estandarMin, realMin, eficiencia, trabajos, porCasilla}>}
 */
export function eficienciaPorPeriodo(trabajos, periodo = 'dia') {
  const grupos = new Map();
  for (const t of trabajos) {
    if (!t.hecha || !(t.tiempoRealMin > 0) || !t.operarioId) continue;
    const clave = `${t.operarioId}|${claveDePeriodo(diaDe(t.horaHecha), periodo)}`;
    if (!grupos.has(clave)) grupos.set(clave, { operarioId: t.operarioId, periodo: clave.split('|')[1], estandarMin: 0, realMin: 0, trabajos: 0, porCasilla: 0 });
    const g = grupos.get(clave);
    g.estandarMin += t.tiempoEstandarMin ?? t.minutos;
    g.realMin += t.tiempoRealMin;
    g.trabajos += 1;
    if (t.origenReal === 'casilla') g.porCasilla += 1;
  }
  return [...grupos.values()].map((g) => ({ ...g, eficiencia: g.realMin > 0 ? g.estandarMin / g.realMin : null }))
    .sort((a, b) => a.periodo.localeCompare(b.periodo) || a.operarioId.localeCompare(b.operarioId));
}

/** Desvío estimado vs real de cada nota terminada (para recalibrar el modelo). */
export function desviosPorNota(notas) {
  return notas.filter((n) => n.estado === 'hecha').map((n) => {
    const estandar = n.trabajos.reduce((s, t) => s + (t.tiempoEstandarMin ?? t.minutos), 0);
    const real = n.trabajos.reduce((s, t) => s + (t.tiempoRealMin || 0), 0);
    return { notaId: n.notaId, numeroNota: n.numeroNota, estandarMin: estandar, realMin: real, desvio: estandar > 0 ? (real - estandar) / estandar : null };
  });
}

// ---------- alertas ----------

/**
 * Alertas para el jefe: vencidas, en riesgo, programadas después de la entrega, urgentes sin
 * asignar y operarios sobrecargados.
 */
export function alertas(notas, trabajos, { hoy, prod, operarios }) {
  const lista = [];
  for (const n of notas) {
    if (n.estado === 'hecha') continue;
    const faltan = diasHabilesHasta(hoy, n.fechaEntrega, prod.diasHabiles);
    const sinAsignar = n.trabajos.filter((t) => !t.hecha && !t.operarioId).length;
    if (n.fechaEntrega < hoy) lista.push({ nivel: 'error', notaId: n.notaId, texto: `NP ${n.numeroNota}: entrega vencida (${n.fechaEntrega})` });
    else if (n.ultimaFecha && n.ultimaFecha > n.fechaEntrega) lista.push({ nivel: 'error', notaId: n.notaId, texto: `NP ${n.numeroNota}: programada hasta ${n.ultimaFecha}, después de la entrega (${n.fechaEntrega})` });
    else if (faltan <= (prod.alertaDiasAntes ?? 1) && sinAsignar) lista.push({ nivel: 'aviso', notaId: n.notaId, texto: `NP ${n.numeroNota}: en riesgo, entrega en ${faltan} día(s) hábil(es) y ${sinAsignar} renglón(es) sin asignar` });
    if (n.prioridad === 'urgente' && sinAsignar) lista.push({ nivel: 'aviso', notaId: n.notaId, texto: `NP ${n.numeroNota}: URGENTE con ${sinAsignar} renglón(es) sin asignar` });
  }
  const carga = cargaPorOperarioYDia(trabajos, { soloPendientes: true });
  for (const op of operarios) {
    for (const [dia, minutos] of Object.entries(carga[op.id] || {})) {
      const capacidad = capacidadDeOperario(op, prod);
      if (dia >= hoy && minutos > capacidad) lista.push({ nivel: 'aviso', texto: `${op.nombre}: ${Math.round(minutos)} min asignados el ${dia} (capacidad ${capacidad} min)` });
    }
  }
  return lista.sort((a, b) => (a.nivel === 'error' ? 0 : 1) - (b.nivel === 'error' ? 0 : 1));
}

// ---------- material consolidado ----------

/**
 * Chapa necesaria para los trabajos PENDIENTES, por material, calibre, terminación y color.
 * - chapas: la regla de la nota (piezas × largo ÷ 2,44), en la unidad del código (tira de la banda);
 * - chapasEnteras: lo mismo pasado a chapas de 1,22 × 2,44 según la banda (banda 60 = 1/2 chapa);
 * - fisicasEstimadas: la estimación física (recortes sin reutilizar), ver chapas.js.
 */
export function materialConsolidado(trabajos, datos) {
  const grupos = new Map();
  for (const t of trabajos) {
    if (t.hecha || t.cantidad.unidad !== 'chapas') continue;
    const r = t.renglon;
    const clave = [r.materialId, r.calibreId, r.terminacion, r.terminacion === 'P' ? r.colorId : ''].join('|');
    if (!grupos.has(clave)) {
      const material = datos.materiales.materiales.find((m) => m.id === r.materialId);
      const color = datos.materiales.colores?.find((c) => c.id === r.colorId);
      grupos.set(clave, {
        clave, materialId: r.materialId, calibreId: r.calibreId, terminacion: r.terminacion,
        nombre: `${material?.nombre || r.materialId} ${r.calibreId}${r.terminacion === 'P' ? ` prepintado ${color?.nombre || ''}` : ''}`.trim(),
        chapas: 0, chapasEnteras: 0, fisicasEstimadas: 0, renglones: 0, porBanda: {},
      });
    }
    const g = grupos.get(clave);
    const banda = t.resultado.banda?.numero || datos.config.bandas.numeroChapaCompleta;
    const fisico = consumoFisico(r, t.resultado, datos.config);
    g.chapas += t.cantidad.valor;
    g.chapasEnteras += (t.cantidad.valor * banda) / datos.config.bandas.numeroChapaCompleta;
    g.fisicasEstimadas += fisico ? fisico.fraccionChapa : 0;
    g.porBanda[banda] = (g.porBanda[banda] || 0) + t.cantidad.valor;
    g.renglones += 1;
  }
  return [...grupos.values()].map((g) => ({
    ...g,
    chapas: redondear(g.chapas, 2),
    chapasEnteras: redondear(g.chapasEnteras, 2),
    chapasAComprar: Math.ceil(g.fisicasEstimadas - 1e-9),
    fisicasEstimadas: redondear(g.fisicasEstimadas, 2),
  })).sort((a, b) => b.chapasEnteras - a.chapasEnteras);
}

// ---------- KPIs ----------

/** Indicadores del período [desde, hasta] (fechas 'aaaa-mm-dd'). */
export function indicadores(notas, trabajos, incidencias, { desde, hasta, hoy }) {
  const enRango = (dia) => dia && dia >= desde && dia <= hasta;
  const terminadas = notas.filter((n) => n.terminada && enRango(diaDe(n.terminada)));
  const aTiempo = terminadas.filter((n) => diaDe(n.terminada) <= n.fechaEntrega);
  const hechos = trabajos.filter((t) => t.hecha && enRango(diaDe(t.horaHecha)) && t.tiempoRealMin > 0);
  const estandar = hechos.reduce((s, t) => s + (t.tiempoEstandarMin ?? t.minutos), 0);
  const real = hechos.reduce((s, t) => s + t.tiempoRealMin, 0);
  const abiertas = notas.filter((n) => n.estado !== 'hecha');
  const incid = incidencias.filter((i) => enRango(diaDe(i.hora)));
  const porCausa = {};
  for (const i of incid) porCausa[`${i.tipo}: ${i.causa}`] = (porCausa[`${i.tipo}: ${i.causa}`] || 0) + 1;
  return {
    notasTerminadas: terminadas.length,
    entregasATiempo: terminadas.length ? aTiempo.length / terminadas.length : null,
    eficiencia: real > 0 ? estandar / real : null,
    horasEstandarHechas: estandar / 60,
    horasReales: real / 60,
    pendientesMin: abiertas.reduce((s, n) => s + n.minutosPendientes, 0),
    notasAbiertas: abiertas.length,
    demoradas: abiertas.filter((n) => n.estado === 'demorada').length,
    vencidasHoy: abiertas.filter((n) => n.fechaEntrega < hoy).length,
    ahorroLotesMin: hechos.reduce((s, t) => s + (t.ahorroLoteMin || 0), 0),
    incidencias: incid.length,
    retrabajos: incid.filter((i) => i.tipo === 'retrabajo').length,
    minutosPerdidos: incid.reduce((s, i) => s + (Number(i.minutosPerdidos) || 0), 0),
    porCausa: Object.entries(porCausa).sort((a, b) => b[1] - a[1]),
  };
}
