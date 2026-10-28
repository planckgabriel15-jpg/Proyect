// =============================================================
// agrupamiento.js
// Agrupa renglones de distintas notas en LOTES que comparten preparación de máquina
// (setup), para hacer el setup una sola vez. Justificación y alternativas descartadas:
// docs/AGRUPAMIENTO.md.
//
// Método (tecnología de grupos + agrupamiento "por líder" con restricciones):
//  1. Cada renglón pendiente es un TRABAJO con atributos: perfil, desarrollo, material,
//     producto, largo, pliegues y herramental (ver atributosDeTrabajo en produccion.js).
//  2. Similitud entre dos trabajos = coeficiente ponderado de coincidencias
//     Σ peso·coincide / Σ peso, sobre los criterios activos (generaliza el coeficiente de
//     Jaccard / "simple matching" de la tecnología de grupos).
//  3. Se recorren los trabajos por prioridad y fecha de entrega (urgentes primero, después
//     la entrega más cercana: regla EDD). Cada uno entra al lote donde más setup ahorra, si
//     se parece a TODOS los integrantes al menos "similitudMinima" (enlace completo) y si
//     cumple las restricciones: misma máquina, entregas dentro de la ventana de días,
//     urgentes solo con urgentes, tope de minutos y de renglones por lote. Si no, abre uno nuevo.
//  4. Dentro del lote se ordena por "vecino más cercano" (el siguiente es el que más setup
//     ahorra respecto del anterior): con setups que dependen de la secuencia, el ahorro
//     se da entre trabajos CONSECUTIVOS.
//  5. Ahorro = setup de cada componente que no hace falta repetir (chapa, guillotina,
//     plegadora, herramental, control, interpretación). El traslado y atado no se ahorra.
// =============================================================

export const CRITERIOS = [
  { id: 'perfil', nombre: 'Perfil (mismo dibujo: mismo programa de plegadora)' },
  { id: 'desarrollo', nombre: 'Desarrollo (mismo tope de guillotina, ± tolerancia)' },
  { id: 'material', nombre: 'Material, calibre, terminación y color' },
  { id: 'producto', nombre: 'Tipo de producto (misma plantilla)' },
  { id: 'largo', nombre: 'Largo (± tolerancia)' },
  { id: 'pliegues', nombre: 'Cantidad y tipo de pliegues' },
  { id: 'herramental', nombre: 'Herramental (matriz y punzón)' },
];

/** ¿Coincide el criterio entre dos trabajos? */
export function coincide(criterio, a, b, criterios) {
  const x = a.atributos;
  const y = b.atributos;
  switch (criterio) {
    case 'perfil': return x.perfil === y.perfil;
    case 'desarrollo': return Number.isFinite(x.desarrolloMm) && Number.isFinite(y.desarrolloMm)
      && Math.abs(x.desarrolloMm - y.desarrolloMm) <= (criterios.desarrollo?.toleranciaMm ?? 0) + 1e-9;
    case 'material': return x.material === y.material;
    case 'producto': return x.producto === y.producto;
    case 'largo': return Math.abs((x.largoCm || 0) - (y.largoCm || 0)) <= (criterios.largo?.toleranciaCm ?? 0) + 1e-9;
    case 'pliegues': return x.pliegues === y.pliegues;
    case 'herramental': return x.herramental === y.herramental;
    default: return false;
  }
}

/** Coeficiente de similitud ponderado (0 a 1) sobre los criterios activos. */
export function similitud(a, b, criterios) {
  let suma = 0;
  let total = 0;
  for (const { id } of CRITERIOS) {
    const c = criterios[id];
    if (!c?.activo) continue;
    const peso = Number(c.peso) || 0;
    total += peso;
    if (coincide(id, a, b, criterios)) suma += peso;
  }
  return total > 0 ? suma / total : 0;
}

/**
 * Setup (min) que se AHORRA si b se hace inmediatamente después de a.
 * Un componente no se repite cuando la máquina queda preparada igual:
 *   chapa → mismo material; guillotina → mismo espesor y desarrollo (± tolerancia);
 *   plegadora, control e interpretación → mismo perfil; herramental → mismo herramental.
 */
export function ahorroEntre(a, b, toleranciaMm = 0) {
  const x = a.atributos;
  const y = b.atributos;
  const c = b.setupComponentesMin || {};
  let ahorro = 0;
  const mismoPerfil = x.perfil === y.perfil && x.tipoPerfil === y.tipoPerfil;
  if (x.material === y.material) ahorro += c.chapa || 0;
  if (x.espesorMm === y.espesorMm && Number.isFinite(x.desarrolloMm) && Math.abs(x.desarrolloMm - y.desarrolloMm) <= toleranciaMm + 1e-9) ahorro += c.guillotina || 0;
  if (mismoPerfil) ahorro += (c.plegadora || 0) + (c.control || 0) + (c.interpretacion || 0);
  if (x.herramental === y.herramental) ahorro += c.herramental || 0;
  return ahorro;
}

/** Orden dentro del lote: arranca por la entrega más cercana y sigue por el vecino que más ahorra. */
export function secuenciarLote(trabajos, toleranciaMm = 0) {
  const quedan = [...trabajos].sort(compararPorUrgencia);
  if (!quedan.length) return [];
  const orden = [quedan.shift()];
  while (quedan.length) {
    const ultimo = orden[orden.length - 1];
    let mejor = 0;
    for (let i = 1; i < quedan.length; i++) {
      if (ahorroEntre(ultimo, quedan[i], toleranciaMm) > ahorroEntre(ultimo, quedan[mejor], toleranciaMm) + 1e-9) mejor = i;
    }
    orden.push(quedan.splice(mejor, 1)[0]);
  }
  return orden;
}

/** Urgentes primero, después la entrega más cercana, después el número de nota. */
export function compararPorUrgencia(a, b) {
  const urgente = (t) => (t.prioridad === 'urgente' ? 0 : 1);
  return urgente(a) - urgente(b)
    || String(a.fechaEntrega).localeCompare(String(b.fechaEntrega))
    || String(a.numeroNota ?? '').localeCompare(String(b.numeroNota ?? ''), 'es', { numeric: true })
    || String(a.clave).localeCompare(String(b.clave));
}

/** Diferencia en días corridos entre dos fechas 'aaaa-mm-dd'. */
export function diasEntre(desde, hasta) {
  return Math.round((Date.parse(`${hasta}T00:00:00Z`) - Date.parse(`${desde}T00:00:00Z`)) / 86400000);
}

/**
 * Resumen de un lote ya secuenciado.
 * @returns {{trabajos, minutosSinAgrupar, setupSinAgruparMin, setupConLoteMin, unitarioMin,
 *   minutosConLote, ahorroMin, ahorroPorcentaje, fechaEntrega, prioridad, maquina, ahorros}}
 */
export function resumirLote(trabajos, toleranciaMm = 0) {
  const ahorros = trabajos.map((t, i) => (i === 0 ? 0 : ahorroEntre(trabajos[i - 1], t, toleranciaMm)));
  const setupSinAgruparMin = trabajos.reduce((s, t) => s + t.setupMin, 0);
  const ahorroMin = ahorros.reduce((s, a) => s + a, 0);
  const minutosSinAgrupar = trabajos.reduce((s, t) => s + t.minutos, 0);
  return {
    trabajos,
    ahorros,
    minutosSinAgrupar,
    setupSinAgruparMin,
    setupConLoteMin: setupSinAgruparMin - ahorroMin,
    unitarioMin: minutosSinAgrupar - setupSinAgruparMin,
    minutosConLote: minutosSinAgrupar - ahorroMin,
    ahorroMin,
    ahorroPorcentaje: minutosSinAgrupar > 0 ? ahorroMin / minutosSinAgrupar : 0,
    ahorroSetupPorcentaje: setupSinAgruparMin > 0 ? ahorroMin / setupSinAgruparMin : 0,
    fechaEntrega: trabajos.map((t) => t.fechaEntrega).sort()[0] || null,
    prioridad: trabajos.some((t) => t.prioridad === 'urgente') ? 'urgente' : 'normal',
    maquina: trabajos[0]?.maquina || null,
  };
}

/** ¿El trabajo puede entrar al lote? Devuelve el motivo si no puede (sirve para explicar). */
export function motivoParaNoEntrar(trabajo, lote, opciones) {
  const lider = lote.trabajos[0];
  if (opciones.respetarMaquina && trabajo.maquina !== lider.maquina) return 'otra máquina';
  if (opciones.urgentesSolas && (trabajo.prioridad === 'urgente') !== (lider.prioridad === 'urgente')) return 'las urgentes van solas';
  const fechas = lote.trabajos.map((t) => t.fechaEntrega).concat(trabajo.fechaEntrega).sort();
  if (diasEntre(fechas[0], fechas[fechas.length - 1]) > opciones.ventanaDias) return `entregas separadas por más de ${opciones.ventanaDias} días`;
  if (lote.trabajos.length >= opciones.maxRenglonesPorLote) return 'lote lleno (renglones)';
  const minutos = lote.trabajos.reduce((s, t) => s + t.minutos, 0) + trabajo.minutos;
  if (minutos > opciones.maxMinutosPorLote) return 'lote lleno (minutos)';
  const minima = Math.min(...lote.trabajos.map((t) => similitud(trabajo, t, opciones.criterios)));
  if (minima + 1e-9 < opciones.similitudMinima) return 'poco parecido';
  return null;
}

/**
 * Propone lotes para los trabajos pendientes.
 * @param {Array} trabajos  ver armarTrabajos() en produccion.js
 * @param {object} opciones datos/produccion.json → agrupamiento (criterios, similitudMinima, ventanaDias…)
 * @returns {Array<{id: string, trabajos: Array, resumen: object}>}
 */
export function proponerLotes(trabajos, opciones) {
  const tolerancia = opciones.criterios?.desarrollo?.toleranciaMm ?? 0;
  const lotes = [];
  for (const trabajo of [...trabajos].sort(compararPorUrgencia)) {
    let elegido = null;
    let mejorAhorro = -1;
    for (const lote of lotes) {
      if (motivoParaNoEntrar(trabajo, lote, opciones)) continue;
      const ahorro = Math.max(...lote.trabajos.map((t) => ahorroEntre(t, trabajo, tolerancia)));
      if (ahorro > mejorAhorro + 1e-9) { elegido = lote; mejorAhorro = ahorro; }
    }
    if (elegido) elegido.trabajos.push(trabajo);
    else lotes.push({ trabajos: [trabajo] });
  }
  return lotes.map((lote, i) => {
    const ordenados = secuenciarLote(lote.trabajos, tolerancia);
    return { id: `L${String(i + 1).padStart(3, '0')}`, claves: ordenados.map((t) => t.clave), trabajos: ordenados, resumen: resumirLote(ordenados, tolerancia) };
  });
}

/** Totales de una propuesta: minutos con y sin agrupar, ahorro y cantidad de lotes con más de un renglón. */
export function totalesDeLotes(lotes) {
  const sinAgrupar = lotes.reduce((s, l) => s + l.resumen.minutosSinAgrupar, 0);
  const ahorro = lotes.reduce((s, l) => s + l.resumen.ahorroMin, 0);
  const setup = lotes.reduce((s, l) => s + l.resumen.setupSinAgruparMin, 0);
  return {
    lotes: lotes.length,
    lotesAgrupados: lotes.filter((l) => l.trabajos.length > 1).length,
    trabajos: lotes.reduce((s, l) => s + l.trabajos.length, 0),
    minutosSinAgrupar: sinAgrupar,
    minutosConLotes: sinAgrupar - ahorro,
    setupSinAgruparMin: setup,
    ahorroMin: ahorro,
    ahorroPorcentaje: sinAgrupar > 0 ? ahorro / sinAgrupar : 0,
    ahorroSetupPorcentaje: setup > 0 ? ahorro / setup : 0,
  };
}

/**
 * Rearma los lotes a partir de las claves guardadas (después de que el jefe los modificó):
 * respeta el orden que dejó el jefe y recalcula ahorros. Los trabajos que ya no están pendientes
 * se sacan; los pendientes que no están en ningún lote quedan como lotes de uno.
 * @param {Array<{id, claves: string[], aceptado?: boolean, nombre?: string}>} guardados
 */
export function rearmarLotes(guardados, trabajos, toleranciaMm = 0) {
  const porClave = new Map(trabajos.map((t) => [t.clave, t]));
  const usados = new Set();
  const lotes = [];
  for (const g of guardados) {
    const miembros = g.claves.map((c) => porClave.get(c)).filter((t) => t && !usados.has(t.clave));
    miembros.forEach((t) => usados.add(t.clave));
    if (miembros.length) lotes.push({ ...g, claves: miembros.map((t) => t.clave), trabajos: miembros, resumen: resumirLote(miembros, toleranciaMm) });
  }
  let n = lotes.length;
  for (const t of [...trabajos].sort(compararPorUrgencia)) {
    if (usados.has(t.clave)) continue;
    n += 1;
    lotes.push({ id: `S${String(n).padStart(3, '0')}`, claves: [t.clave], trabajos: [t], resumen: resumirLote([t], toleranciaMm), suelto: true });
  }
  return lotes;
}

/**
 * ¿Algún trabajo urgente termina más tarde con los lotes que haciéndolo solo (en orden EDD)?
 * Simulación simple por máquina: los lotes se hacen en orden de urgencia y entrega, uno detrás de otro,
 * repartidos en las máquinas iguales. Devuelve las claves urgentes que se atrasan.
 */
export function urgentesDemoradas(lotes, maquinas = {}) {
  const terminaCon = finPorTrabajo(lotes.map((l) => ({ ...l.resumen, trabajos: l.trabajos, minutos: l.resumen.minutosConLote })), maquinas);
  const terminaSolo = finPorTrabajo(lotes.flatMap((l) => l.trabajos).map((t) => ({ ...resumirLote([t]), trabajos: [t], minutos: t.minutos })), maquinas);
  return lotes.flatMap((l) => l.trabajos).filter((t) => t.prioridad === 'urgente' && terminaCon.get(t.clave) > terminaSolo.get(t.clave) + 1e-6).map((t) => t.clave);
}

function finPorTrabajo(bloques, maquinas) {
  const fin = new Map();
  const libres = {};
  const ordenados = [...bloques].sort((a, b) => compararPorUrgencia(
    { prioridad: a.prioridad, fechaEntrega: a.fechaEntrega, clave: a.trabajos[0].clave },
    { prioridad: b.prioridad, fechaEntrega: b.fechaEntrega, clave: b.trabajos[0].clave }));
  for (const bloque of ordenados) {
    const cantidad = Math.max(1, maquinas[bloque.maquina] || 1);
    libres[bloque.maquina] ||= Array(cantidad).fill(0);
    const lista = libres[bloque.maquina];
    const i = lista.indexOf(Math.min(...lista));
    let reloj = lista[i];
    // Dentro del lote cada trabajo termina a medida que avanza.
    const factor = bloque.minutosSinAgrupar > 0 ? bloque.minutos / bloque.minutosSinAgrupar : 1;
    for (const t of bloque.trabajos) {
      reloj += t.minutos * factor;
      fin.set(t.clave, reloj);
    }
    lista[i] = reloj;
  }
  return fin;
}

/**
 * Propuesta "protegida": si con los lotes alguna urgente terminaría más tarde que haciéndolo
 * todo sin agrupar, se separan los integrantes que la "empujan": los que están en un lote que
 * se hace antes que ella pero tienen entrega posterior. Si no hay a quién culpar, la urgente
 * sale de su lote. Se repite hasta que ninguna urgente se atrase.
 * @returns {{lotes: Array, separadas: string[]}} separadas = trabajos que se sacaron de un lote
 */
export function proponerLotesProtegidos(trabajos, opciones, maquinas = {}) {
  const tolerancia = opciones.criterios?.desarrollo?.toleranciaMm ?? 0;
  let lotes = proponerLotes(trabajos, opciones);
  const separadas = [];
  for (let vuelta = 0; vuelta < 30; vuelta++) {
    const demoradas = urgentesDemoradas(lotes, maquinas);
    if (!demoradas.length) break;
    const fuera = new Set();
    for (const clave of demoradas) {
      const urgente = lotes.flatMap((l) => l.trabajos).find((t) => t.clave === clave);
      const culpables = lotes
        .filter((l) => l.trabajos.length > 1 && l.resumen.maquina === urgente.maquina && !l.claves.includes(clave)
          && compararPorUrgencia({ ...l.resumen, clave: l.claves[0] }, urgente) < 0)
        .flatMap((l) => l.trabajos.filter((t) => t.fechaEntrega > urgente.fechaEntrega || (t.prioridad !== 'urgente' && urgente.prioridad === 'urgente')));
      if (culpables.length) culpables.forEach((t) => fuera.add(t.clave));
      else fuera.add(clave);
    }
    separadas.push(...fuera);
    const nuevos = [];
    for (const lote of lotes) {
      const quedan = lote.trabajos.filter((t) => !fuera.has(t.clave));
      if (quedan.length) nuevos.push({ ...lote, claves: quedan.map((t) => t.clave), trabajos: quedan, resumen: resumirLote(quedan, tolerancia) });
      lote.trabajos.filter((t) => fuera.has(t.clave)).forEach((t, i) => nuevos.push({ id: `${lote.id}-S${i + 1}`, claves: [t.clave], trabajos: [t], resumen: resumirLote([t], tolerancia) }));
    }
    lotes = nuevos;
  }
  return { lotes, separadas: [...new Set(separadas)] };
}
