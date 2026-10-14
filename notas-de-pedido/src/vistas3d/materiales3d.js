// =============================================================
// materiales3d.js
// Colores de la pieza en 3D según el material:
// - galvanizado y otros sin pintar: color metálico en las dos caras;
// - prepintada: el color en la cara pintada y gris claro en la otra.
// =============================================================

import * as THREE from 'three';

/**
 * @returns {{pintado: THREE.Material, sinPintar: THREE.Material, esPrepintada: boolean}}
 */
export function materialesDelRenglon(renglon, materiales) {
  const material = materiales.materiales.find((m) => m.id === renglon.materialId);
  const esPrepintada = renglon.terminacion === 'P';
  if (esPrepintada) {
    const color = materiales.colores.find((c) => c.id === renglon.colorId);
    return {
      esPrepintada,
      pintado: nuevoMaterial(color ? color.hex : '#888888', 0.15, 0.55),
      sinPintar: nuevoMaterial(materiales.colorCaraSinPintarHex, 0.3, 0.6),
    };
  }
  const colorMetal = material ? material.colorHex : '#aeb4ba';
  return {
    esPrepintada,
    pintado: nuevoMaterial(colorMetal, 0.3, 0.45),
    sinPintar: nuevoMaterial(colorMetal, 0.3, 0.45),
  };
}

export function nuevoMaterial(colorHex, metalness, roughness) {
  return new THREE.MeshStandardMaterial({
    color: new THREE.Color(colorHex),
    metalness,
    roughness,
    side: THREE.DoubleSide,
    polygonOffset: true,
    polygonOffsetFactor: 1,
    polygonOffsetUnits: 1,
  });
}

/** Color con el que se resalta el tramo elegido en la tabla. */
export const COLOR_RESALTADO = new THREE.Color('#ff8c00');
