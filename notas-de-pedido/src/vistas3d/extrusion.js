// =============================================================
// extrusion.js
// Pieza plegada en 3D: cada tramo del perfil se "estira" a lo largo de la
// pieza (eje Z) como una chapa fina. Cada tramo es un objeto aparte, así se
// puede resaltar cuando se toca en la tabla.
//
// Coordenadas: el perfil está en el plano X-Y (en cm, igual que en 2D) y el
// largo de la pieza va de Z = 0 a Z = largoCm.
// Documentación de Three.js: https://threejs.org/docs/
// =============================================================

import * as THREE from 'three';
import { calcularGeometria, ladoPintadoDelPerfil } from '../logica/geometria.js';
import { generarBordeOndulado } from '../logica/corteLaser.js';

const ESPESOR_VISUAL_CM = 0.25; // espesor dibujado (no es el real: es para que se vea)

/**
 * Construye una chapa plana para un tramo.
 * La forma se arma en coordenadas locales: u = a lo ancho del tramo (0 → medida),
 * v = a lo largo de la pieza (0 → largo). Si el tramo tiene corte láser en su
 * borde libre, ese borde sale ondulado.
 */
function formaDelTramo(medidaCm, largoCm, corteLaser, bordeLibre, config) {
  const forma = new THREE.Shape();
  if (corteLaser && bordeLibre) {
    const borde = generarBordeOndulado(largoCm, corteLaser, config, 24);
    if (bordeLibre === 'inicio') {
      // El borde ondulado está en u = 0 y entra hacia u positivo.
      forma.moveTo(Math.min(borde[0].h, medidaCm), 0);
      for (const p of borde) forma.lineTo(Math.min(p.h, medidaCm * 0.98), p.a);
      forma.lineTo(medidaCm, largoCm);
      forma.lineTo(medidaCm, 0);
    } else {
      // El borde ondulado está en u = medida y entra hacia u negativo.
      forma.moveTo(0, 0);
      forma.lineTo(0, largoCm);
      for (const p of [...borde].reverse()) forma.lineTo(Math.max(medidaCm - p.h, medidaCm * 0.02), p.a);
    }
    forma.closePath();
    return forma;
  }
  forma.moveTo(0, 0);
  forma.lineTo(medidaCm, 0);
  forma.lineTo(medidaCm, largoCm);
  forma.lineTo(0, largoCm);
  forma.closePath();
  return forma;
}

/**
 * Arma la pieza a partir de segmentos 2D.
 * @param {Array<{indice, inicio:{x,y}, fin:{x,y}, corteLaser?, bordeLibre?}>} segmentos
 * @param {number} largoCm
 * @param {{izquierda: THREE.Material, derecha: THREE.Material}} materialesPorLado
 *        material de la cara que queda a la izquierda / derecha del recorrido
 * @returns {THREE.Group}
 */
export function construirDesdeSegmentos(segmentos, largoCm, materialesPorLado, config) {
  const grupo = new THREE.Group();
  for (const segmento of segmentos) {
    const dx = segmento.fin.x - segmento.inicio.x;
    const dy = segmento.fin.y - segmento.inicio.y;
    const medida = Math.hypot(dx, dy);
    if (medida < 1e-6) continue;

    const ejeU = new THREE.Vector3(dx / medida, dy / medida, 0); // a lo ancho del tramo
    const ejeV = new THREE.Vector3(0, 0, 1);                      // a lo largo de la pieza
    const normalDerecha = new THREE.Vector3(dy / medida, -dx / medida, 0); // = ejeU × ejeV

    const geometria = new THREE.ShapeGeometry(formaDelTramo(medida, largoCm, segmento.corteLaser, segmento.bordeLibre, config));
    const grupoTramo = new THREE.Group();
    grupoTramo.userData.tramo = segmento.indice;

    // Dos caras separadas por el espesor visual: la de la izquierda y la de la derecha del recorrido.
    for (const lado of ['izquierda', 'derecha']) {
      const material = materialesPorLado[lado].clone(); // copia propia: se puede resaltar solo este tramo
      const malla = new THREE.Mesh(geometria, material);
      const corrimiento = (lado === 'derecha' ? 1 : -1) * ESPESOR_VISUAL_CM / 2;
      const origen = new THREE.Vector3(segmento.inicio.x, segmento.inicio.y, 0).addScaledVector(normalDerecha, corrimiento);
      const matriz = new THREE.Matrix4().makeBasis(ejeU, ejeV, normalDerecha).setPosition(origen);
      malla.applyMatrix4(matriz);
      malla.userData.tramo = segmento.indice;
      grupoTramo.add(malla);
    }

    // Contorno oscuro para que se vean bien los bordes.
    const bordes = new THREE.LineSegments(
      new THREE.EdgesGeometry(geometria),
      new THREE.LineBasicMaterial({ color: 0x333333, transparent: true, opacity: 0.55 }),
    );
    bordes.applyMatrix4(new THREE.Matrix4().makeBasis(ejeU, ejeV, normalDerecha).setPosition(new THREE.Vector3(segmento.inicio.x, segmento.inicio.y, 0)));
    bordes.userData.esBorde = true;
    grupoTramo.add(bordes);

    grupo.add(grupoTramo);
  }
  return grupo;
}

/** Materiales de la cara izquierda y derecha del recorrido según el lado pintado. */
function materialesSegunLado(perfil, materiales, ladoPintura, config) {
  const ladoPintado = materiales.esPrepintada ? ladoPintadoDelPerfil(perfil, ladoPintura || 'afuera', config) : 'izquierda';
  if (ladoPintado === 'ambos') return { izquierda: materiales.pintado, derecha: materiales.pintado };
  if (ladoPintado === 'izquierda') return { izquierda: materiales.pintado, derecha: materiales.sinPintar };
  return { izquierda: materiales.sinPintar, derecha: materiales.pintado };
}

/**
 * Pieza plegada completa (perfil por tramos extruido al largo).
 * @param {object} perfil
 * @param {number} largoCm
 * @param {{pintado, sinPintar, esPrepintada}} materiales  de materiales3d.js
 * @param {string|null} ladoPintura 'afuera' | 'adentro'
 * @param {object|null} perfilFin  con pendiente: el perfil de la punta final (Z = largo)
 */
export function construirPlegada(perfil, largoCm, materiales, ladoPintura, config, perfilFin = null) {
  if (perfilFin) return construirConPendiente(perfil, perfilFin, largoCm, materiales, ladoPintura, config);
  const geometria = calcularGeometria(perfil, config);
  const ultimo = geometria.segmentos.length - 1;
  const segmentos = geometria.segmentos.map((s) => ({
    indice: s.indice,
    inicio: s.inicio,
    fin: s.fin,
    corteLaser: s.tramo.corteLaser || null,
    // El corte va en el borde libre: el comienzo del primer tramo o el final del último.
    bordeLibre: s.indice === 0 ? 'inicio' : (s.indice === ultimo ? 'fin' : null),
  }));

  const grupo = construirDesdeSegmentos(segmentos, largoCm, materialesSegunLado(perfil, materiales, ladoPintura, config), config);
  grupo.userData.geometria2d = geometria;
  return grupo;
}

/**
 * Plegado con pendiente: cada tramo es una chapa que va del tramo del perfil inicial
 * (Z = 0) al mismo tramo del perfil final (Z = largo), como el "lofted flange" de los
 * programas de CAD. Los dos perfiles tienen los mismos tramos (ver logica/pendiente.js).
 * La chapa se arma en fajas a lo largo, así se ve bien aunque el tramo quede alabeado.
 * El corte láser no se dibuja ondulado en estas piezas (queda marcado en el 2D).
 */
export function construirConPendiente(perfil, perfilFin, largoCm, materiales, ladoPintura, config) {
  const inicio = calcularGeometria(perfil, config);
  const fin = calcularGeometria(perfilFin, config);
  const materialesPorLado = materialesSegunLado(perfil, materiales, ladoPintura, config);
  const grupo = new THREE.Group();
  const fajas = 12;

  inicio.segmentos.forEach((s0, i) => {
    const s1 = fin.segmentos[i];
    if (!s1) return;
    const grupoTramo = new THREE.Group();
    grupoTramo.userData.tramo = s0.indice;
    // Normal "a la derecha del recorrido" de cada punta (para separar las dos caras).
    const normal = (s) => {
      const dx = s.fin.x - s.inicio.x;
      const dy = s.fin.y - s.inicio.y;
      const largo = Math.hypot(dx, dy) || 1;
      return { x: dy / largo, y: -dx / largo };
    };
    const n0 = normal(s0);
    const n1 = normal(s1);

    for (const lado of ['izquierda', 'derecha']) {
      const signo = (lado === 'derecha' ? 1 : -1) * ESPESOR_VISUAL_CM / 2;
      const posiciones = [];
      const punto = (t, enFin) => {
        // t = 0 → Z = 0 (inicio), t = 1 → Z = largo (final)
        const a = enFin ? s0.fin : s0.inicio;
        const b = enFin ? s1.fin : s1.inicio;
        const nx = n0.x + (n1.x - n0.x) * t;
        const ny = n0.y + (n1.y - n0.y) * t;
        return [a.x + (b.x - a.x) * t + nx * signo, a.y + (b.y - a.y) * t + ny * signo, largoCm * t];
      };
      for (let k = 0; k < fajas; k++) {
        const t0 = k / fajas;
        const t1 = (k + 1) / fajas;
        const p00 = punto(t0, false);
        const p01 = punto(t0, true);
        const p10 = punto(t1, false);
        const p11 = punto(t1, true);
        posiciones.push(...p00, ...p01, ...p11, ...p00, ...p11, ...p10);
      }
      const geometria = new THREE.BufferGeometry();
      geometria.setAttribute('position', new THREE.Float32BufferAttribute(posiciones, 3));
      geometria.computeVertexNormals();
      const malla = new THREE.Mesh(geometria, materialesPorLado[lado].clone());
      malla.userData.tramo = s0.indice;
      grupoTramo.add(malla);
    }

    // Contorno: los dos bordes de las puntas y los dos pliegues a lo largo.
    const v = (p, z) => new THREE.Vector3(p.x, p.y, z);
    const bordes = new THREE.LineSegments(
      new THREE.BufferGeometry().setFromPoints([
        v(s0.inicio, 0), v(s0.fin, 0), v(s1.inicio, largoCm), v(s1.fin, largoCm),
        v(s0.inicio, 0), v(s1.inicio, largoCm), v(s0.fin, 0), v(s1.fin, largoCm),
      ]),
      new THREE.LineBasicMaterial({ color: 0x333333, transparent: true, opacity: 0.55 }),
    );
    bordes.userData.esBorde = true;
    grupoTramo.add(bordes);
    grupo.add(grupoTramo);
  });

  grupo.userData.geometria2d = inicio;
  grupo.userData.geometria2dFinal = fin;
  return grupo;
}
