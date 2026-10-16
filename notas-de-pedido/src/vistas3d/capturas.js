// =============================================================
// capturas.js
// "Fotos" 3D chicas para las tarjetas de renglón y para la impresión.
// Se usa UN SOLO dibujador escondido para todas las fotos, porque los
// navegadores permiten pocos dibujos 3D (contextos WebGL) abiertos a la vez.
// =============================================================

import * as THREE from 'three';
import { construirModelo } from './modelo.js';
import { encuadrar, DIRECCIONES_VISTA } from './encuadre.js';

let renderer = null;
let escena = null;
let camara = null;

function preparar() {
  if (renderer) return;
  renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true, logarithmicDepthBuffer: true });
  escena = new THREE.Scene();
  escena.background = new THREE.Color('#ffffff');
  escena.add(new THREE.HemisphereLight(0xffffff, 0x8899aa, 1.6));
  const luz = new THREE.DirectionalLight(0xffffff, 1.6);
  luz.position.set(1, 2, 1.5);
  escena.add(luz);
  camara = new THREE.PerspectiveCamera(30, 1, 0.1, 50000);
}

/**
 * @returns {string} imagen PNG como texto "data:image/png;base64,…"
 */
export function capturarRenglon(renglon, datos, ancho = 320, alto = 220) {
  preparar();
  renderer.setSize(ancho, alto, false);
  camara.aspect = ancho / alto;

  const modelo = construirModelo(renglon, datos);
  escena.add(modelo);

  encuadrar(camara, modelo, DIRECCIONES_VISTA.iso, 1.05);

  renderer.render(escena, camara);
  const imagen = renderer.domElement.toDataURL('image/png');

  escena.remove(modelo);
  modelo.traverse((o) => {
    if (o.geometry) o.geometry.dispose();
    if (o.material) (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => { m.map?.dispose(); m.dispose(); });
  });
  return imagen;
}
