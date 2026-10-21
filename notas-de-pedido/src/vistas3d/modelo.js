// =============================================================
// modelo.js
// Arma el objeto 3D completo de un renglón: la pieza (con sus cortes), las
// tapas y boquetas puestas en la canaleta (renglon.accesorios), la pared de
// cada corte, las uniones del empalme y la regla del largo.
// =============================================================

import * as THREE from 'three';
import { leerNumero, formatearNumero } from '../logica/numeros.js';
import { materialesDelRenglon } from './materiales3d.js';
import { construirPlegada } from './extrusion.js';
import { construirTapa, construirBoqueta, tubo, tuboRectangular, GENERADORES } from './piezasEspeciales3d.js';
import { tienePendiente, perfilFinal } from '../logica/pendiente.js';
import { buscarFondo as buscarFondoEnSegmentos, calcularGeometria, ladoExteriorDelPerfil } from '../logica/geometria.js';
import { huecosEnCaras, huellaDeCorte, centroDelCorte } from '../logica/cortes.js';
import { normalizarBoqueta, huellaDeBoqueta, tipoDeTapa, medidasDeTapa, ubicarTapa, centroDeBoquetaEnTapa } from '../logica/accesoriosCanaleta.js';
import { tramosDeChapa, posicionesDeUniones } from '../logica/empalme.js';

/**
 * @param {object} renglon
 * @param {{config, materiales}} datos
 * @param {{regla?: boolean}} opciones  regla: false cuando el visor ya muestra las cotas (traen el largo)
 * @returns {THREE.Group}
 */
export function construirModelo(renglon, datos, opciones = {}) {
  const { config, materiales } = datos;
  const grupo = new THREE.Group();
  const mats = materialesDelRenglon(renglon, materiales);
  const largoCm = leerNumero(renglon.largoCm) > 0 ? leerNumero(renglon.largoCm) : 100;

  let pieza;
  if (renglon.tipoPieza === 'plegada') {
    const conPendiente = tienePendiente(renglon);
    // Los agujeros se recortan en la chapa (con pendiente la chapa no es plana: no se recortan).
    const huecos = conPendiente ? [] : huecosEnCaras(renglon, config);
    pieza = construirPlegada(renglon.perfil, largoCm, mats, renglon.ladoPintura, config, conPendiente ? perfilFinal(renglon.perfil) : null, huecos);
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

  // Pared (cuello o aletas) alrededor de cada corte.
  if (renglon.tipoPieza === 'plegada' && renglon.cortes?.length && !tienePendiente(renglon)) {
    grupo.add(montarParedesDeCortes(renglon, pieza, mats, config));
  }

  // Uniones del empalme (dónde termina cada tramo de chapa).
  if (renglon.tipoPieza === 'plegada') {
    const tramos = tramosDeChapa(renglon, config);
    if (tramos.length > 1) grupo.add(dibujarUniones(pieza, tramos, largoCm, config));
  }

  // Regla del largo.
  if (renglon.usaLargo !== false && opciones.regla !== false) {
    const eje = renglon.tipoPieza === 'plegada' || renglon.generador3d === 'mediaCana' ? 'z' : 'y';
    grupo.add(crearRegla(pieza, largoCm, eje));
  }
  return grupo;
}

/**
 * Pone las tapas (en las puntas) y las boquetas (en el fondo o en una tapa) sobre la canaleta.
 * Tapa izquierda en Z = 0 (punta izquierda mirando la canaleta de frente), derecha en Z = largo.
 * Soldada: la pestaña queda hacia adentro de la canaleta. Engrampada: la pestaña abraza por afuera.
 * Una tapa a medida se apoya en el fondo; si lleva una boqueta, la tapa queda agujereada.
 */
function montarAccesorios(canaleta, pieza, largoCm, mats, datos) {
  const { config } = datos;
  const grupo = new THREE.Group();
  const acc = canaleta.accesorios;
  const boquetas = (acc.boquetas || []).map((b) => normalizarBoqueta(b, config));

  for (const lado of ['izquierda', 'derecha']) {
    const tipo = tipoDeTapa(acc, lado);
    if (tipo === 'ninguna') continue;
    const ubicacion = ubicarTapa(canaleta, lado, config);
    const medidas = medidasDeTapa(acc, lado, config);
    const enEstaTapa = lado === 'izquierda' ? 'tapaIzquierda' : 'tapaDerecha';
    const huecos = boquetas.filter((b) => b.ubicacion === enEstaTapa)
      .map((b) => ({ ...centroDeBoquetaEnTapa(canaleta, b, config), huella: huellaDeBoqueta(b) }));
    const tapa = { perfil: ubicacion.perfil, parametros: { pestanaApoyoCm: medidas.pestanaCm }, ladoPintura: canaleta.ladoPintura };
    const z = lado === 'izquierda' ? 0 : largoCm;
    const sentido = lado === 'izquierda' ? (tipo === 'soldada' ? 1 : -1) : (tipo === 'soldada' ? -1 : 1);
    grupo.add(marcarAccesorio(construirTapa(tapa, mats, config, z, sentido, { dy: ubicacion.dy, huecos }), `tapa:${lado}`));
  }

  boquetas.forEach((b, i) => {
    const boqueta = construirBoqueta(b, canaleta, mats, config);
    if (b.ubicacion === 'fondo') {
      const posicion = Math.min(Math.max(leerNumero(b.posicionCm) || 0, 0), largoCm);
      const fondo = fondoEn(pieza, posicion / largoCm);
      boqueta.position.set(fondo.x, fondo.y, posicion);
    } else {
      // En una tapa: la boqueta sale hacia afuera de la canaleta, por la punta.
      const centro = centroDeBoquetaEnTapa(canaleta, b, config);
      const izquierda = b.ubicacion === 'tapaIzquierda';
      boqueta.rotation.x = izquierda ? Math.PI / 2 : -Math.PI / 2;
      boqueta.position.set(centro.x, centro.y, izquierda ? 0 : largoCm);
    }
    grupo.add(marcarAccesorio(boqueta, `boqueta:${i}`));
  });
  return grupo;
}

/** Pared (cuello) de cada corte: un caño corto, redondo o rectangular, para afuera o para adentro. */
function montarParedesDeCortes(renglon, pieza, mats, config) {
  const grupo = new THREE.Group();
  const geometria = pieza.userData.geometria2d || calcularGeometria(renglon.perfil, config);
  const exteriorDerecha = ladoExteriorDelPerfil(renglon.perfil, config) === 'derecha';
  renglon.cortes.forEach((corte, i) => {
    const altura = leerNumero(corte.paredAlturaCm);
    const s = geometria.segmentos[corte.tramo];
    if (!(altura > 0) || !s) return;
    const dx = s.fin.x - s.inicio.x;
    const dy = s.fin.y - s.inicio.y;
    const medida = Math.hypot(dx, dy);
    if (medida < 1e-6) return;
    const ejeU = new THREE.Vector3(dx / medida, dy / medida, 0);
    const derecha = new THREE.Vector3(dy / medida, -dx / medida, 0);
    const haciaAfuera = exteriorDerecha ? derecha : derecha.clone().negate();
    const normal = corte.paredLado === 'adentro' ? haciaAfuera.clone().negate() : haciaAfuera;
    const huella = huellaDeCorte(corte);
    const pared = huella.forma === 'circulo'
      ? tubo(huella.diametro / 2, altura, mats, renglon.ladoPintura)
      : tuboRectangular(huella.ancho, huella.alto, altura, mats, renglon.ladoPintura);
    const centroU = centroDelCorte(corte, medida);
    const origen = new THREE.Vector3(s.inicio.x, s.inicio.y, leerNumero(corte.posicionCm) || 0).addScaledVector(ejeU, centroU);
    // El caño crece en +Y: se lo gira para que crezca hacia la normal de la cara.
    const ejeZ = new THREE.Vector3().crossVectors(ejeU, normal);
    pared.applyMatrix4(new THREE.Matrix4().makeBasis(ejeU, normal, ejeZ).setPosition(origen));
    grupo.add(marcarAccesorio(pared, `corte:${i}`));
  });
  return grupo;
}

/** Líneas en cada unión del empalme, alrededor del perfil (con pendiente, el perfil de ese punto). */
function dibujarUniones(pieza, tramos, largoCm, config) {
  const grupo = new THREE.Group();
  const inicio = pieza.userData.geometria2d;
  const final = pieza.userData.geometria2dFinal || inicio;
  if (!inicio) return grupo;
  const material = new THREE.LineBasicMaterial({ color: 0xb00020 });
  for (const z of posicionesDeUniones(tramos, config.empalme?.solapeCm ?? 0)) {
    const t = z / largoCm;
    const puntos = inicio.puntos.map((p, i) => {
      const q = final.puntos[i] || p;
      return new THREE.Vector3(p.x + (q.x - p.x) * t, p.y + (q.y - p.y) * t, z);
    });
    for (const desplazamiento of [-0.3, 0.3]) {
      grupo.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(puntos.map((p) => p.clone().setZ(z + desplazamiento))), material));
    }
  }
  grupo.userData.esEmpalme = true;
  return grupo;
}

/** Marca todas las partes de una tapa o boqueta (para elegirla con un toque en el editor 3D). */
function marcarAccesorio(objeto, clave) {
  objeto.traverse((o) => { o.userData.accesorio = clave; });
  return objeto;
}

/**
 * Fondo de la canaleta a una altura del largo (t = 0 punta izquierda, t = 1 punta derecha).
 * Sin pendiente es siempre el mismo; con pendiente se interpola entre las dos puntas.
 */
export function fondoEn(pieza, t) {
  const inicio = buscarFondo(pieza?.userData.geometria2d);
  const final = pieza?.userData.geometria2dFinal ? buscarFondo(pieza.userData.geometria2dFinal) : inicio;
  return { x: inicio.x + (final.x - inicio.x) * t, y: inicio.y + (final.y - inicio.y) * t };
}

/** Punto medio del tramo más bajo y más horizontal del perfil (el fondo de la canaleta). */
export function buscarFondo(geometria2d) {
  return buscarFondoEnSegmentos(geometria2d?.segmentos).punto;
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
