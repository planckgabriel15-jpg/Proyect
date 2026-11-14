// =============================================================
// preferencias.js
// Lo que el programa RECUERDA de cada vendedor para que no cargue dos veces lo mismo:
// - el último material, calibre, terminación, color y lado de pintura que usó;
// - las piezas que usó último ("recientes") y las que más usa ("frecuentes");
// - la última boqueta que cargó (forma y medidas);
// - si le gusta ver la tabla de tramos completa y el 3D abierto.
// Y los clientes de notas anteriores, para sugerirlos al escribir.
//
// Es lógica pura: recibe y devuelve objetos. Guardar y leer es de almacenamiento.js.
// Un valor recordado es solo un punto de partida: siempre se ve y se puede cambiar.
// =============================================================

export const MAXIMO_RECIENTES = 12;

export function preferenciasVacias() {
  return { material: null, recientes: [], usos: {}, boqueta: null, tablaCompleta: false, ver3d: null };
}

const CAMPOS_MATERIAL = ['materialId', 'calibreId', 'terminacion', 'colorId', 'ladoPintura'];
const CAMPOS_BOQUETA = ['tipo', 'forma', 'diametroCm', 'ladoACm', 'ladoBCm', 'largoBocaCm'];

/**
 * Anota que el vendedor agregó esa pieza a una nota. No modifica el objeto recibido.
 * @returns {object} preferencias nuevas
 */
export function registrarUso(preferencias, renglon) {
  const nuevas = { ...preferenciasVacias(), ...preferencias, usos: { ...(preferencias?.usos || {}) } };
  if (renglon.plantillaId) {
    nuevas.recientes = [renglon.plantillaId, ...(preferencias?.recientes || []).filter((id) => id !== renglon.plantillaId)].slice(0, MAXIMO_RECIENTES);
    nuevas.usos[renglon.plantillaId] = (nuevas.usos[renglon.plantillaId] || 0) + 1;
  }
  if (!renglon.sinMaterial) {
    nuevas.material = Object.fromEntries(CAMPOS_MATERIAL.map((campo) => [campo, renglon[campo] ?? null]));
  }
  const ultimaBoqueta = renglon.accesorios?.boquetas?.at(-1);
  if (ultimaBoqueta) {
    nuevas.boqueta = Object.fromEntries(CAMPOS_BOQUETA.filter((campo) => ultimaBoqueta[campo] !== undefined).map((campo) => [campo, ultimaBoqueta[campo]]));
  }
  return nuevas;
}

/** ¿El material recordado sigue existiendo en datos/materiales.json? (pudo cambiar la lista) */
function materialValido(material, materiales) {
  if (!material) return false;
  const fila = materiales.materiales.find((m) => m.id === material.materialId);
  if (!fila || !fila.terminaciones.includes(material.terminacion)) return false;
  if (!materiales.calibres.some((c) => c.id === material.calibreId)) return false;
  return material.terminacion !== 'P' || materiales.colores.some((c) => c.id === material.colorId);
}

/**
 * Material con el que arranca una pieza nueva. En orden: el de la última pieza con chapa de
 * ESTA nota (mismo trabajo, casi siempre el mismo material), el último que usó el vendedor y,
 * si no hay ninguno, null (queda el de datos/config.json).
 * @returns {{materialId, calibreId, terminacion, colorId, ladoPintura, origen: 'nota'|'vendedor'}|null}
 */
export function materialPorDefecto(nota, preferencias, materiales) {
  const anterior = [...(nota?.renglones || [])].reverse().find((r) => !r.sinMaterial);
  if (anterior) {
    const deLaNota = Object.fromEntries(CAMPOS_MATERIAL.map((campo) => [campo, anterior[campo] ?? null]));
    if (materialValido(deLaNota, materiales)) return { ...deLaNota, origen: 'nota' };
  }
  return materialValido(preferencias?.material, materiales) ? { ...preferencias.material, origen: 'vendedor' } : null;
}

/** Pone ese material en un renglón nuevo (los artículos y servicios no llevan). Devuelve el mismo renglón. */
export function aplicarMaterial(renglon, material) {
  if (!material || renglon.sinMaterial) return renglon;
  for (const campo of CAMPOS_MATERIAL) if (material[campo] !== undefined && material[campo] !== null) renglon[campo] = material[campo];
  if (renglon.terminacion !== 'P') renglon.colorId = material.colorId ?? renglon.colorId;
  return renglon;
}

/**
 * Piezas para mostrar arriba de la galería: las últimas usadas y las más usadas (sin repetir).
 * Solo las que el vendedor puede ver ahora (la lista que se le pasa).
 * @returns {{recientes: Array, frecuentes: Array}}
 */
export function recientesYFrecuentes(preferencias, plantillas, maximo = 6) {
  const porId = new Map(plantillas.map((p) => [p.id, p]));
  const recientes = (preferencias?.recientes || []).map((id) => porId.get(id)).filter(Boolean).slice(0, maximo);
  const yaEstan = new Set(recientes.map((p) => p.id));
  const frecuentes = Object.entries(preferencias?.usos || {})
    .filter(([id, veces]) => veces >= 2 && porId.has(id) && !yaEstan.has(id))
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, maximo)
    .map(([id]) => porId.get(id));
  return { recientes, frecuentes };
}

/**
 * Clientes de notas anteriores, del más reciente al más viejo y sin repetir
 * (no distingue mayúsculas ni espacios de más). Para sugerir al escribir.
 */
export function clientesConocidos(notas, maximo = 300) {
  const vistos = new Set();
  const lista = [];
  const ordenadas = [...(notas || [])].sort((a, b) => String(b.fechaEmision || b.fechaCreacion || '').localeCompare(String(a.fechaEmision || a.fechaCreacion || '')));
  for (const nota of ordenadas) {
    const nombre = String(nota.cliente || '').replace(/\s+/g, ' ').trim();
    const clave = nombre.toLowerCase();
    if (!nombre || vistos.has(clave)) continue;
    vistos.add(clave);
    lista.push(nombre);
    if (lista.length >= maximo) break;
  }
  return lista;
}
