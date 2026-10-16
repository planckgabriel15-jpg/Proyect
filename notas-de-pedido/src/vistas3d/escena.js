// =============================================================
// escena.js
// Visor 3D interactivo: girar arrastrando, zoom con la rueda o pellizcando,
// botones de vista (inicial, frente, lateral, isométrica), resaltado de tramos
// y clic sobre un tramo (para sincronizar con la tabla).
// Usa Three.js + OrbitControls (cargados desde el CDN, ver index.html).
// =============================================================

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { construirModelo } from './modelo.js';
import { COLOR_RESALTADO } from './materiales3d.js';
import { encuadrar, DIRECCIONES_VISTA } from './encuadre.js';

/**
 * @param {HTMLElement} contenedor
 * @param {{alPasarSobreTramo?: (i|null) => void, alTocarTramo?: (i) => void}} opciones
 */
export function crearVisor3d(contenedor, opciones = {}) {
  // preserveDrawingBuffer: permite sacar una "foto" del dibujo para imprimir.
  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true, logarithmicDepthBuffer: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.domElement.classList.add('lienzo-3d');
  contenedor.append(renderer.domElement);

  const escena = new THREE.Scene();
  escena.background = new THREE.Color('#eef1f4');
  escena.add(new THREE.HemisphereLight(0xffffff, 0x8899aa, 1.6));
  const luz = new THREE.DirectionalLight(0xffffff, 1.6);
  luz.position.set(1, 2, 1.5);
  escena.add(luz);
  const luz2 = new THREE.DirectionalLight(0xffffff, 0.7);
  luz2.position.set(-1.5, -0.5, -1);
  escena.add(luz2);

  const camara = new THREE.PerspectiveCamera(35, 1, 0.5, 50000);
  const controles = new OrbitControls(camara, renderer.domElement);
  controles.enableDamping = true;

  let modelo = null;
  let tramoResaltado = null;
  let ultimaVista = 'iso';
  let encuadrado = false;

  // ---- tamaño: se ajusta solo cuando cambia el contenedor ----
  function ajustarTamano() {
    const ancho = contenedor.clientWidth || 300;
    const alto = contenedor.clientHeight || 260;
    renderer.setSize(ancho, alto, false);
    camara.aspect = ancho / alto;
    camara.updateProjectionMatrix();
  }
  const observador = new ResizeObserver(ajustarTamano);
  observador.observe(contenedor);
  ajustarTamano();

  // ---- bucle de dibujo ----
  let activo = true;
  function dibujar() {
    if (!activo) return;
    controles.update();
    renderer.render(escena, camara);
    requestAnimationFrame(dibujar);
  }
  requestAnimationFrame(dibujar);

  // ---- elegir tramo con el mouse o el dedo ----
  const rayo = new THREE.Raycaster();
  const puntero = new THREE.Vector2();
  function tramoBajoPuntero(evento) {
    if (!modelo) return null;
    const rect = renderer.domElement.getBoundingClientRect();
    puntero.x = ((evento.clientX - rect.left) / rect.width) * 2 - 1;
    puntero.y = -((evento.clientY - rect.top) / rect.height) * 2 + 1;
    rayo.setFromCamera(puntero, camara);
    const tocados = rayo.intersectObjects(modelo.children[0] ? [modelo.children[0]] : [], true);
    const tocado = tocados.find((t) => t.object.isMesh && t.object.userData.tramo !== undefined);
    return tocado ? tocado.object.userData.tramo : null;
  }
  let inicioToque = null;
  renderer.domElement.addEventListener('pointerdown', (e) => { inicioToque = { x: e.clientX, y: e.clientY }; });
  renderer.domElement.addEventListener('pointerup', (e) => {
    // Si casi no se movió, fue un "clic" (no un giro).
    if (inicioToque && Math.hypot(e.clientX - inicioToque.x, e.clientY - inicioToque.y) < 5) {
      const indice = tramoBajoPuntero(e);
      if (indice !== null && opciones.alTocarTramo) opciones.alTocarTramo(indice);
    }
    inicioToque = null;
  });
  renderer.domElement.addEventListener('pointermove', (e) => {
    if (e.buttons || !opciones.alPasarSobreTramo) return;
    opciones.alPasarSobreTramo(tramoBajoPuntero(e));
  });

  // ---- vistas ----
  function vista(nombre) {
    if (!modelo) return;
    ultimaVista = nombre === 'inicial' ? 'iso' : nombre;
    const direccion = DIRECCIONES_VISTA[ultimaVista] || DIRECCIONES_VISTA.iso;
    // Frente y lateral con "teleobjetivo" (ángulo chico): casi sin perspectiva, como un plano.
    camara.fov = ultimaVista === 'iso' ? 35 : 8;
    const centro = encuadrar(camara, modelo, direccion);
    controles.target.copy(centro);
    controles.update();
  }

  function aplicarResaltado() {
    if (!modelo) return;
    modelo.traverse((objeto) => {
      if (objeto.isMesh && objeto.userData.tramo !== undefined && objeto.material.emissive) {
        objeto.material.emissive.copy(objeto.userData.tramo === tramoResaltado ? COLOR_RESALTADO : new THREE.Color(0x000000));
        objeto.material.emissiveIntensity = objeto.userData.tramo === tramoResaltado ? 0.6 : 0;
      }
    });
  }

  function liberar(objeto) {
    objeto.traverse((o) => {
      if (o.geometry) o.geometry.dispose();
      if (o.material) (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => { m.map?.dispose(); m.dispose(); });
    });
  }

  return {
    /** Muestra un renglón (con sus tapas y boquetas). Mantiene la cámara salvo la primera vez. */
    mostrar(renglon, datos, { reencuadrar = false } = {}) {
      if (modelo) {
        escena.remove(modelo);
        liberar(modelo);
      }
      modelo = construirModelo(renglon, datos);
      escena.add(modelo);
      aplicarResaltado();
      if (!encuadrado || reencuadrar) {
        vista(ultimaVista);
        encuadrado = true;
      }
    },
    resaltarTramo(indice) {
      tramoResaltado = indice;
      aplicarResaltado();
    },
    vista,
    /** Foto del dibujo actual (PNG en texto "data:image/png;base64,…"). */
    capturar() {
      renderer.render(escena, camara);
      return renderer.domElement.toDataURL('image/png');
    },
    destruir() {
      activo = false;
      observador.disconnect();
      if (modelo) liberar(modelo);
      controles.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    },
  };
}
