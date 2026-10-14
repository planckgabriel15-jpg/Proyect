// =============================================================
// numeracion.js
// Número de nota de pedido (NP): correlativo POR SUCURSAL (sección 5.1).
// Cada sucursal tiene su "último número usado" (configurable, para seguir
// desde el talonario de papel). El número se asigna al EMITIR la nota.
//
// "contadores" es un objeto { idSucursal: últimoNúmeroUsado }.
// =============================================================

/** Número que le tocaría a la próxima nota de esa sucursal (sin reservarlo). */
export function siguienteNumeroNP(contadores, sucursalId) {
  const ultimo = Number(contadores?.[sucursalId] ?? 0);
  return (Number.isFinite(ultimo) ? ultimo : 0) + 1;
}

/**
 * Asigna el número a una nota: devuelve el número y los contadores actualizados.
 * No modifica el objeto original.
 * @returns {{numero: number, contadores: object}}
 */
export function asignarNumeroNP(contadores, sucursalId) {
  const numero = siguienteNumeroNP(contadores, sucursalId);
  return { numero, contadores: { ...contadores, [sucursalId]: numero } };
}

/** Arma los contadores iniciales a partir de datos/sucursales.json. */
export function contadoresDesdeSucursales(sucursales) {
  const contadores = {};
  for (const sucursal of sucursales) {
    contadores[sucursal.id] = Number(sucursal.ultimoNumeroNP) || 0;
  }
  return contadores;
}
