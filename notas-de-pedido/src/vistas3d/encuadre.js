// =============================================================
// encuadre.js
// Ubica la cámara para que la pieza entre justa en el dibujo, mirando
// desde una dirección dada. Mide las 8 esquinas de la "caja" de la pieza,
// así una canaleta larga y finita no queda chiquita en el medio.
// =============================================================

import * as THREE from 'three';

/**
 * @param {THREE.PerspectiveCamera} camara
 * @param {THREE.Object3D} objeto
 * @param {THREE.Vector3} direccion  desde dónde se mira (se normaliza)
 * @param {number} margen  1.1 = 10 % de aire alrededor
 * @returns {THREE.Vector3} el centro de la pieza (para apuntar los controles)
 */
export function encuadrar(camara, objeto, direccion, margen = 1.12) {
  const caja = new THREE.Box3().setFromObject(objeto);
  const centro = caja.getCenter(new THREE.Vector3());
  const adelante = direccion.clone().normalize();               // de la pieza hacia la cámara
  let arriba = new THREE.Vector3(0, 1, 0);
  if (Math.abs(adelante.dot(arriba)) > 0.99) arriba = new THREE.Vector3(0, 0, -1);
  const derecha = new THREE.Vector3().crossVectors(arriba, adelante).normalize();
  arriba = new THREE.Vector3().crossVectors(adelante, derecha).normalize();

  const tanVertical = Math.tan(THREE.MathUtils.degToRad(camara.fov / 2));
  const tanHorizontal = tanVertical * camara.aspect;
  let distancia = 1;
  for (const x of [caja.min.x, caja.max.x]) {
    for (const y of [caja.min.y, caja.max.y]) {
      for (const z of [caja.min.z, caja.max.z]) {
        const esquina = new THREE.Vector3(x, y, z).sub(centro);
        const r = Math.abs(esquina.dot(derecha));
        const u = Math.abs(esquina.dot(arriba));
        const f = esquina.dot(adelante); // las esquinas más cerca de la cámara piden más distancia
        distancia = Math.max(distancia, (r * margen) / tanHorizontal + f, (u * margen) / tanVertical + f);
      }
    }
  }
  camara.position.copy(centro).addScaledVector(adelante, distancia);
  camara.near = Math.max(distancia / 1000, 0.05);
  camara.far = distancia * 50;
  camara.lookAt(centro);
  camara.updateProjectionMatrix();
  return centro;
}

/** Direcciones de las vistas rápidas. */
export const DIRECCIONES_VISTA = {
  frente: new THREE.Vector3(0, 0, 1),          // se ve el perfil (de punta)
  lateral: new THREE.Vector3(-1, 0.001, 0),    // se ve el largo (la punta izquierda queda a la izquierda)
  iso: new THREE.Vector3(-1, 0.7, 0.8),        // de costado y un poco de arriba
};
