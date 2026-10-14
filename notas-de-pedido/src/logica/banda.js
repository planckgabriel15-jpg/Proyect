// =============================================================
// banda.js
// Banda de cotización: qué parte de la chapa de 1,22 × 2,44 m se usa
// según el desarrollo (sección 5.3).
//
//   0 < D ≤ 30   → 1/4 de chapa    → número 30
//  30 < D ≤ 60   → 1/2 chapa       → número 60
//  60 < D ≤ 120  → chapa completa  → número 120
//  D > 120       → no entra        → sin código + "Requiere soldar piezas"
//
// Si el desarrollo pasa el límite aunque sea por 0,1 cm, sube de banda.
// Los límites vienen de datos/config.json (limiteChapaCompletaCm es SUPUESTO).
// =============================================================

import { redondear } from './numeros.js';

export const AVISO_REQUIERE_SOLDAR = 'Requiere soldar piezas';

/**
 * @param {number} desarrolloCm
 * @param {object} config  contenido de datos/config.json
 * @returns {{numero: number|null, nombre: string, requiereSoldar: boolean, aviso: string|null}}
 */
export function calcularBanda(desarrolloCm, config) {
  const limites = config.bandas;
  // Redondeamos a 2 decimales para que 30,000000001 (error de la compu) no suba de banda.
  const desarrollo = redondear(Number(desarrolloCm), 2);

  if (!Number.isFinite(desarrollo) || desarrollo <= 0) {
    return { numero: null, nombre: 'sin desarrollo', requiereSoldar: false, aviso: 'Cargá al menos un tramo con medida' };
  }
  if (desarrollo <= limites.limiteCuartoChapaCm) {
    return { numero: limites.numeroCuartoChapa, nombre: '1/4 de chapa', requiereSoldar: false, aviso: null };
  }
  if (desarrollo <= limites.limiteMediaChapaCm) {
    return { numero: limites.numeroMediaChapa, nombre: '1/2 chapa', requiereSoldar: false, aviso: null };
  }
  if (desarrollo <= limites.limiteChapaCompletaCm) {
    return { numero: limites.numeroChapaCompleta, nombre: 'chapa completa', requiereSoldar: false, aviso: null };
  }
  return { numero: null, nombre: 'no entra en la chapa', requiereSoldar: true, aviso: AVISO_REQUIERE_SOLDAR };
}
