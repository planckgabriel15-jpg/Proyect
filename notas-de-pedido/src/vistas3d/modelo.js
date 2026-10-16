// =============================================================
// modelo.js
// Arma el objeto 3D completo de un renglón: la pieza, las tapas y boquetas
// puestas en la canaleta (renglon.accesorios) y la regla del largo.
// =============================================================

import * as THREE from 'three';
import { leerNumero, formatearNumero } from '../logica/numeros.js';
import { materialesDelRenglon } from './materiales3d.js';
import { construirPlegada } from './extrusion.js';
import { GENERADORES, construirTapa } from './piezasEspeciales3d.js';

/**
 * @param {object} renglon
 * @param {{config, materiales}} datos
 * @returns {THREE.Group}
 */
export function construirModelo(renglon, datos) {
  const { config, materiales } = datos;
  const grupo = new THREE.Group();
  const mats = materialesDelRenglon(renglon, materiales);
  const largoCm = leerNumero(renglon.largoCm) > 0 ? leerNumero(renglon.largoCm) : 100;

  let pieza;
  if (renglon.tipoPieza === 'plegada') {
    pieza = construirPlegada(renglon.perfil, largoCm, mats, renglon.ladoPintura, config);
  } else {
    const generador = GENERADORES[renglon.generador3d];
    pieza = generador ? generador(renglon.parametros || {}, renglon, mats, config) : new THREE.Group();
  }
  pieza.userData.esPiezaPrincipal = true;
  grupo.add(pieza);

  // Tapas y boquetas puestas en la canaleta.
  if (renglon.tipoPieza === 'plegada' && renglon.accesorios) {
    grupo.add(montarAccesorios(renglon, pieza, largoCm, mats, datos));
  }

  // Regla del largo.
  if (renglon.usaLargo !== false) {
    const eje = renglon.tipoPieza === 'plegada' || renglon.generador3d === 'mediaCana' ? 'z' : 'y';
    grupo.add(crearRegla(pieza, largoCm, eje));
  }
  return grupo;
}

/**
 * Pone las tapas (en las puntas) y las boquetas (abajo, en el fondo) sobre la canaleta.
 * Tapa izquierda en Z = 0 (punta izquierda mirando la canaleta de frente), derecha en Z = largo.
 * Soldada: la pestaña queda hacia adentro de la canaleta. Engrampada: la pestaña abraza por afuera.
 */
function montarAccesorios(canaleta, pieza, largoCm, mats, datos) {
  const grupo = new THREE.Group();
  const acc = canaleta.accesorios;
  const tapaComoRenglon = { perfil: canaleta.perfil, parametros: { pestanaApoyoCm: 1.5 }, ladoPintura: canaleta.ladoPintura };
  if (acc.tapaIzquierda !== 'ninguna') {
    grupo.add(construirTapa(tapaComoRenglon, mats, datos.config, 0, acc.tapaIzquierda === 'soldada' ? 1 : -1));
  }
  if (acc.tapaDerecha !== 'ninguna') {
    grupo.add(construirTapa(tapaComoRenglon, mats, datos.config, largoCm, acc.tapaDerecha === 'soldada' ? -1 : 1));
  }
  const fondo = buscarFondo(pieza.userData.geometria2d);
  for (const b of acc.boquetas || []) {
    const boqueta = GENERADORES.boquetaSuelta({ pestanaCm: 2, ...b }, canaleta, mats, datos.config);
    const posicion = Math.min(Math.max(leerNumero(b.posicionCm) || 0, 0), largoCm);
    boqueta.position.set(fondo.x, fondo.y, posicion);
    grupo.add(boqueta);
  }
  return grupo;
}

/** Punto medio del tramo más bajo y más horizontal del perfil (el fondo de la canaleta). */
function buscarFondo(geometria2d) {
  let mejor = null;
  for (const s of geometria2d?.segmentos || []) {
    const dx = Math.abs(s.fin.x - s.inicio.x);
    const dy = Math.abs(s.fin.y - s.inicio.y);
    if (dx < dy) continue; // no es horizontal
    const yMedio = (s.inicio.y + s.fin.y) / 2;
    if (!mejor || yMedio < mejor.y) {
      mejor = { x: (s.inicio.x + s.fin.x) / 2, y: yMedio };
    }
  }
  return mejor || { x: 0, y: 0 };
}

/** Texto como "cartelito" que siempre mira a la cámara. */
export function crearEtiqueta(texto, alturaCm) {
  const lienzo = document.createElement('canvas');
  lienzo.width = 512;
  lienzo.height = 128;
  const contexto = lienzo.getContext('2d');
  contexto.fillStyle = 'rgba(255,255,255,0.9)';
  contexto.fillRect(0, 0, 512, 128);
  contexto.strokeStyle = '#111';
  contexto.lineWidth = 6;
  contexto.strokeRect(3, 3, 506, 122);
  contexto.fillStyle = '#111';
  contexto.font = 'bold 72px system-ui, sans-serif';
  contexto.textAlign = 'center';
  contexto.textBaseline = 'middle';
  contexto.fillText(texto, 256, 68);
  const textura = new THREE.CanvasTexture(lienzo);
  const etiqueta = new THREE.Sprite(new THREE.SpriteMaterial({ map: textura, depthTest: false }));
  etiqueta.scale.set(alturaCm * 4, alturaCm, 1);
  etiqueta.renderOrder = 10;
  return etiqueta;
}

/** Regla con el largo de la pieza, al costado. */
function crearRegla(pieza, largoCm, eje) {
  const grupo = new THREE.Group();
  const caja = new THREE.Box3().setFromObject(pieza);
  const tamano = caja.getSize(new THREE.Vector3());
  const separacion = Math.max(tamano.x, tamano.y, 10) * 0.25;
  const material = new THREE.LineBasicMaterial({ color: 0x111111 });
  const puntos = [];
  let inicio;
  let fin;
  if (eje === 'z') {
    inicio = new THREE.Vector3(caja.min.x - separacion, caja.min.y, 0);
    fin = new THREE.Vector3(caja.min.x - separacion, caja.min.y, largoCm);
  } else {
    inicio = new THREE.Vector3(caja.min.x - separacion, 0, 0);
    fin = new THREE.Vector3(caja.min.x - separacion, largoCm, 0);
  }
  puntos.push(inicio, fin);
  // Marcas en las puntas.
  const marca = eje === 'z' ? new THREE.Vector3(separacion * 0.3, 0, 0) : new THREE.Vector3(separacion * 0.3, 0, 0);
  puntos.push(inicio.clone().sub(marca), inicio.clone().add(marca), fin.clone().sub(marca), fin.clone().add(marca));
  const geometria = new THREE.BufferGeometry().setFromPoints([puntos[0], puntos[1], puntos[2], puntos[3], puntos[4], puntos[5]]);
  grupo.add(new THREE.LineSegments(geometria, material));
  const etiqueta = crearEtiqueta(`${formatearNumero(largoCm / 100, 2)} m`, Math.max(Math.max(tamano.x, tamano.y) * 0.3, largoCm * 0.05));
  etiqueta.position.copy(inicio.clone().add(fin).multiplyScalar(0.5)).add(new THREE.Vector3(-separacion * 0.6, 0, 0));
  grupo.add(etiqueta);
  grupo.userData.esRegla = true;
  return grupo;
}
