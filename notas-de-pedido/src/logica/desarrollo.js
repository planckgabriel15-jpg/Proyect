// =============================================================
// desarrollo.js
// Desarrollo = ancho de chapa que hay que cortar para fabricar la pieza.
// REGLA CONFIRMADA (sección 5.2): es la SUMA SIMPLE de las medidas
// EXTERIORES de todos los tramos, en cm. No se descuenta nada por pliegue.
// Los dobladillos también suman: 1 + 20 + 32 + 7 = 60.
// =============================================================

import { leerNumero, redondear } from './numeros.js';

/**
 * Suma las medidas de los tramos.
 * Los tramos con medida vacía o inválida no suman (la validación los marca como error aparte).
 * @param {Array<{medidaCm: number|string}>} tramos
 * @returns {number} desarrollo en cm, redondeado a 2 decimales
 */
export function calcularDesarrollo(tramos) {
  let desarrolloCm = 0;
  for (const tramo of tramos || []) {
    const medidaCm = leerNumero(tramo.medidaCm);
    if (Number.isFinite(medidaCm) && medidaCm > 0) {
      desarrolloCm += medidaCm;
    }
  }
  return redondear(desarrolloCm, 2);
}
