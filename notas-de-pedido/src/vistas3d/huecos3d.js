// =============================================================
// huecos3d.js
// Contorno de un agujero (corte o boca de boqueta) para restarlo de una
// chapa plana de Three.js (los "holes" de una forma).
// =============================================================

import * as THREE from 'three';

/**
 * @param {number} cx  centro (en el plano de la chapa)
 * @param {number} cy
 * @param {{forma: 'circulo', diametro} | {forma: 'rect', ancho, alto}} huella
 */
export function caminoDeHueco(cx, cy, huella) {
  const camino = new THREE.Path();
  if (huella.forma === 'circulo') {
    camino.absarc(cx, cy, huella.diametro / 2, 0, Math.PI * 2, true);
    return camino;
  }
  const w = huella.ancho / 2;
  const h = huella.alto / 2;
  camino.moveTo(cx - w, cy - h);
  camino.lineTo(cx - w, cy + h);
  camino.lineTo(cx + w, cy + h);
  camino.lineTo(cx + w, cy - h);
  camino.lineTo(cx - w, cy - h);
  return camino;
}
