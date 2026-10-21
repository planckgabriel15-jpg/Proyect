// =============================================================
// cotas3d.js
// Cotas del 3D: líneas de cota (Three.js) + la lista de textos que el visor
// pone encima como etiquetas HTML (se leen nítidas, se tocan con el dedo y
// se pueden editar en el lugar, como en un programa de CAD).
//
// - Pieza plegada (o tapa con perfil): una cota por tramo, del lado de afuera,
//   el ángulo de cada pliegue, el largo de la pieza y la posición de cada
//   boqueta. En las puntas libres del perfil, un "+" para agregar un tramo.
// - Pieza especial: las medidas principales dibujadas sobre la pieza
//   (diámetro, lados, largo, alto…) y el resto de los datos en una ficha.
//
// Cada etiqueta dice qué cambia si se edita (campo "editar"):
//   {tipo:'medida', indice}  {tipo:'angulo', indice}  {tipo:'largo'}
//   {tipo:'parametro', id}   {tipo:'boqueta-posicion', indice}
//   {tipo:'agregar', extremo}  {tipo:'seleccionar', seleccion}
// =============================================================

import * as THREE from 'three';
import { leerNumero, formatearNumero, formatearCorto } from '../logica/numeros.js';
import { cotasDelPerfil } from '../logica/cotas.js';
import { calcularLimites, calcularGeometria, ladoExteriorDelPerfil } from '../logica/geometria.js';
import { parametrosVisibles } from '../logica/piezasEspeciales.js';
import { buscarPlantilla } from '../logica/renglones.js';
import { normalizarBoqueta, nombreDeBoqueta, centroDeBoquetaEnTapa, tipoDeTapa, medidasDeTapa } from '../logica/accesoriosCanaleta.js';
import { medidaDeCorte, centroDelCorte } from '../logica/cortes.js';
import { tramosDeChapa, posicionesDeUniones } from '../logica/empalme.js';
import { num, medidaReferencia } from './piezasEspeciales3d.js';
import { fondoEn } from './modelo.js';
import { tienePendiente, perfilFinal, calcularPendiente } from '../logica/pendiente.js';

const COLOR_COTAS = 0x0b3d91;

const v3 = (x, y, z) => new THREE.Vector3(x, y, z);

/** Junta segmentos sueltos y los convierte en un solo objeto de líneas. */
class Trazos {
  constructor() { this.puntos = []; }
  linea(a, b) { this.puntos.push(a.clone(), b.clone()); }
  objeto() {
    const geometria = new THREE.BufferGeometry().setFromPoints(this.puntos);
    const material = new THREE.LineBasicMaterial({ color: COLOR_COTAS, depthTest: false, transparent: true, opacity: 0.9 });
    const lineas = new THREE.LineSegments(geometria, material);
    lineas.renderOrder = 20; // siempre encima de la pieza
    return lineas;
  }
}

/**
 * Cota lineal entre a y b, corrida `separacion` hacia `normal`.
 * Dibuja las líneas de extensión, la línea de cota y dos marcas a 45° en las puntas.
 * @returns {THREE.Vector3} dónde va el texto
 */
function cotaLineal(trazos, a, b, normal, separacion) {
  const n = normal.clone().normalize();
  const desdeA = a.clone().addScaledVector(n, separacion * 0.15);
  const desdeB = b.clone().addScaledVector(n, separacion * 0.15);
  const pa = a.clone().addScaledVector(n, separacion);
  const pb = b.clone().addScaledVector(n, separacion);
  trazos.linea(desdeA, pa.clone().addScaledVector(n, separacion * 0.2));
  trazos.linea(desdeB, pb.clone().addScaledVector(n, separacion * 0.2));
  trazos.linea(pa, pb);
  marcas(trazos, pa, pb, n, separacion);
  return pa.clone().add(pb).multiplyScalar(0.5);
}

/** Marcas a 45° en las dos puntas de una línea de cota (como en los planos de arquitectura). */
function marcas(trazos, pa, pb, n, separacion) {
  const u = pb.clone().sub(pa);
  if (u.lengthSq() < 1e-12) return;
  u.normalize();
  const diagonal = u.clone().add(n).normalize().multiplyScalar(separacion * 0.18);
  for (const p of [pa, pb]) trazos.linea(p.clone().sub(diagonal), p.clone().add(diagonal));
}

/** Texto de un número en cm: 12.5 → "12,5". */
const cm = (valor) => (Number.isFinite(valor) ? formatearCorto(valor) : '?');

/**
 * @param {object} renglon
 * @param {{config, materiales, catalogo}} datos
 * @param {THREE.Object3D} modelo  lo que devolvió construirModelo (para medir la pieza)
 * @returns {{
 *   grupo: THREE.Group,               // líneas de cota (se agrega a la escena)
 *   grupoPerfil: THREE.Group|null,    // la parte que se pasa a la punta de la pieza más cercana a la cámara
 *   largoCm: number,
 *   etiquetas: Array<object>,         // textos anclados en 3D
 *   ficha: Array<object>,             // datos que no se dibujan (van en una lista en la esquina)
 * }}
 */
export function construirCotas(renglon, datos, modelo) {
  const { config } = datos;
  const grupo = new THREE.Group();
  grupo.userData.esCotas = true;
  const etiquetas = [];
  const ficha = [];
  const largoCm = leerNumero(renglon.largoCm) > 0 ? leerNumero(renglon.largoCm) : 100;
  let grupoPerfil = null;

  const usaPerfil = (renglon.tipoPieza === 'plegada' || renglon.usaPerfil) && renglon.perfil?.tramos?.length;
  const conPendiente = tienePendiente(renglon);
  if (usaPerfil && conPendiente) {
    // Con pendiente: cada punta con sus cotas (la final se edita aparte).
    const inicio = cotasDePerfil(renglon.perfil, config, etiquetas, false);
    const final = cotasDePerfil(perfilFinal(renglon.perfil), config, etiquetas, true);
    final.position.z = largoCm;
    grupo.add(inicio, final);
    const pendiente = calcularPendiente(renglon, config);
    ficha.push({ texto: `Pendiente: ${pendiente.texto}`, editar: null, titulo: 'Se cambia con las medidas de la punta final' });
  } else if (usaPerfil) {
    grupoPerfil = cotasDePerfil(renglon.perfil, config, etiquetas, false);
    grupo.add(grupoPerfil);
  }

  if (renglon.tipoPieza === 'plegada') {
    const puntos = calcularGeometria(renglon.perfil, config).puntos
      .concat(conPendiente ? calcularGeometria(perfilFinal(renglon.perfil), config).puntos : []);
    const limites = calcularLimites(puntos);
    const separacion = Math.max(Math.max(limites.ancho, limites.alto, 1) * 0.12, 1);
    if (renglon.usaLargo !== false) {
      grupo.add(cotaDelLargo(limites, largoCm, separacion, etiquetas));
      const tramos = tramosDeChapa(renglon, config);
      if (tramos.length > 1) grupo.add(cotasDelEmpalme(limites, tramos, separacion, etiquetas, config));
    }
    if (renglon.accesorios) {
      grupo.add(cotasDeAccesorios(renglon, modelo, limites, largoCm, separacion, etiquetas, config));
    }
    if (renglon.cortes?.length) {
      grupo.add(cotasDeCortes(renglon, config, largoCm, separacion, etiquetas));
    }
  } else {
    grupo.add(cotasDeEspecial(renglon, datos, modelo, largoCm, etiquetas, ficha));
  }

  return { grupo, grupoPerfil, largoCm, etiquetas, ficha };
}

// -------------------------------------------------------------
// Perfil por tramos
// -------------------------------------------------------------

/** @param {boolean} esFinal  true = punta final de un plegado con pendiente */
function cotasDePerfil(perfil, config, etiquetas, esFinal) {
  const grupo = new THREE.Group();
  grupo.userData.cotasDePerfil = true;
  const cotas = cotasDelPerfil(perfil, config);
  const punta = esFinal ? 'Punta final · ' : '';
  const sep = cotas.separacionCm;
  const trazos = new Trazos();

  for (const m of cotas.medidas) {
    const a = v3(m.desde.x, m.desde.y, 0);
    const b = v3(m.hasta.x, m.hasta.y, 0);
    const posicion = cotaLineal(trazos, a, b, v3(m.normal.x, m.normal.y, 0), sep);
    etiquetas.push({
      ancla: grupo, posicion, texto: m.texto, clase: `cota-medida${esFinal ? ' cota-final' : ''}`, prioridad: 3, indiceTramo: m.indice,
      editar: { tipo: 'medida', indice: m.indice, final: esFinal }, valor: m.valor, unidad: 'cm',
      titulo: `${punta}Tramo ${m.indice + 1}: tocá para cambiar la medida`,
    });
  }

  for (const angulo of cotas.angulos) {
    const vertice = v3(angulo.vertice.x, angulo.vertice.y, 0);
    const radio = sep * 0.8;
    const pasos = 16;
    let anterior = null;
    for (let i = 0; i <= pasos; i++) {
      const grados = angulo.desdeGrados + (angulo.barridoGrados * i) / pasos;
      const r = (grados * Math.PI) / 180;
      const punto = vertice.clone().add(v3(Math.cos(r) * radio, Math.sin(r) * radio, 0));
      if (anterior) trazos.linea(anterior, punto);
      anterior = punto;
    }
    etiquetas.push({
      ancla: grupo, posicion: vertice.clone().add(v3(angulo.bisectriz.x, angulo.bisectriz.y, 0).multiplyScalar(sep * 1.7)),
      texto: angulo.texto, clase: `cota-angulo${esFinal ? ' cota-final' : ''}`, prioridad: 1, indiceTramo: angulo.indice,
      editar: { tipo: 'angulo', indice: angulo.indice, final: esFinal }, valor: angulo.valor, unidad: '°',
      titulo: `${punta}Pliegue antes del tramo ${angulo.indice + 1}: tocá para cambiar el ángulo`,
    });
  }

  // Botones "+" en las puntas libres (solo se ven en el editor 3D).
  for (const extremo of cotas.extremos) {
    const punto = v3(extremo.punto.x, extremo.punto.y, 0).add(v3(extremo.direccion.x, extremo.direccion.y, 0).multiplyScalar(sep * 1.3));
    etiquetas.push({
      ancla: grupo, posicion: punto, texto: '+', clase: 'cota-mas', prioridad: 2, soloEdicion: true,
      editar: { tipo: 'agregar', extremo: extremo.extremo },
      titulo: extremo.extremo === 'inicio' ? 'Agregar un tramo al principio' : 'Agregar un tramo al final',
    });
  }

  grupo.add(trazos.objeto());
  return grupo;
}

/** Cota del largo: a lo largo de la pieza (eje Z), abajo a la izquierda del perfil. */
function cotaDelLargo(limites, largoCm, separacion, etiquetas) {
  const grupo = new THREE.Group();
  const trazos = new Trazos();
  const x = limites.minX - separacion * 1.6;
  const y = limites.minY - separacion * 1.6;
  const a = v3(x, y, 0);
  const b = v3(x, y, largoCm);
  trazos.linea(a, b);
  marcas(trazos, a, b, v3(-1, 0, 0), separacion * 1.5);
  grupo.add(trazos.objeto());
  etiquetas.push({
    ancla: grupo, posicion: a.clone().add(b).multiplyScalar(0.5), texto: `${formatearNumero(largoCm / 100, 2)} m`,
    clase: 'cota-largo', prioridad: 5, editar: { tipo: 'largo' }, valor: largoCm / 100, unidad: 'm',
    titulo: 'Largo de la pieza: tocá para cambiarlo',
  });
  return grupo;
}

/** Empalme: cuánto mide cada tramo de chapa (al costado de la cota del largo; se pueden cambiar). */
function cotasDelEmpalme(limites, tramos, separacion, etiquetas, config) {
  const grupo = new THREE.Group();
  const trazos = new Trazos();
  const x = limites.minX - separacion * 2.8;
  const y = limites.minY - separacion * 1.6;
  const uniones = [0, ...posicionesDeUniones(tramos, config.empalme?.solapeCm ?? 0)];
  tramos.forEach((t, i) => {
    const a = v3(x, y, uniones[i]);
    const b = v3(x, y, uniones[i] + t);
    trazos.linea(a, b);
    marcas(trazos, a, b, v3(-1, 0, 0), separacion * 1.2);
    etiquetas.push({
      ancla: grupo, posicion: a.clone().add(b).multiplyScalar(0.5), texto: `chapa ${i + 1}: ${formatearNumero(t / 100, 2)} m`,
      clase: 'cota-medida cota-empalme', prioridad: 4, editar: { tipo: 'empalme-tramo', indice: i }, valor: t / 100, unidad: 'm',
      titulo: `Tramo de chapa ${i + 1} del empalme: tocá para cambiarlo (el último se ajusta solo)`,
    });
  });
  grupo.add(trazos.objeto());
  return grupo;
}

/** Cortes: cartel de cada corte y su posición desde la punta izquierda. */
function cotasDeCortes(renglon, config, largoCm, separacion, etiquetas) {
  const grupo = new THREE.Group();
  const trazos = new Trazos();
  const geometria = calcularGeometria(renglon.perfil, config);
  const exteriorDerecha = ladoExteriorDelPerfil(renglon.perfil, config) === 'derecha';
  renglon.cortes.forEach((corte, i) => {
    const s = geometria.segmentos[corte.tramo];
    if (!s) return;
    const dx = s.fin.x - s.inicio.x;
    const dy = s.fin.y - s.inicio.y;
    const medida = Math.hypot(dx, dy) || 1;
    const u = v3(dx / medida, dy / medida, 0);
    const n = v3(dy / medida, -dx / medida, 0).multiplyScalar(exteriorDerecha ? 1 : -1); // hacia afuera
    const centro = v3(s.inicio.x, s.inicio.y, 0).addScaledVector(u, centroDelCorte(corte, medida));
    const posicionCm = Math.min(Math.max(leerNumero(corte.posicionCm) || 0, 0), largoCm);
    const linea = centro.clone().addScaledVector(n, separacion * (0.9 + i * 0.5));
    const a = linea.clone().setZ(0);
    const b = linea.clone().setZ(posicionCm);
    trazos.linea(a, b);
    trazos.linea(b, centro.clone().setZ(posicionCm));
    marcas(trazos, a, b, n, separacion);
    etiquetas.push({
      ancla: grupo, posicion: a.clone().add(b).multiplyScalar(0.5), texto: `corte ${i + 1}: ${cm(leerNumero(corte.posicionCm))}`,
      clase: 'cota-medida', prioridad: 2, editar: { tipo: 'corte-posicion', indice: i }, valor: leerNumero(corte.posicionCm), unidad: 'cm',
      titulo: `Posición del corte ${i + 1} (desde la punta izquierda hasta el centro)`,
    });
    etiquetas.push({
      ancla: grupo, posicion: centro.clone().addScaledVector(n, separacion * 0.4).setZ(posicionCm), texto: `corte ${medidaDeCorte(corte)}`,
      clase: 'cota-dato', prioridad: 1, editar: { tipo: 'seleccionar', seleccion: { tipo: 'corte', indice: i } },
      titulo: 'Tocá para cambiar la forma, la medida, la cara o la pared del corte',
    });
  });
  grupo.add(trazos.objeto());
  return grupo;
}

/** Cuánto baja la boqueta desde el fondo (aproximado, como se dibuja en piezasEspeciales3d.js). */
function profundidadDeBoqueta(b) {
  if (b.tipo === 'tronera') return num(b.altoCm, 12) + num(b.diametroSalidaCm, 10);
  if (b.tipo === 'colector_recto') return 15;
  if (b.tipo === 'embudo_colector_moldura') return 10 + Math.min(num(b.ladoACm, 20), num(b.ladoBCm, 10)) * 0.8;
  return num(b.pestanaCm, 2) * 0.6 + num(b.largoBocaCm, 10);
}

/** Canaleta: posición de cada boqueta (desde la punta izquierda) y cartel de cada tapa. */
function cotasDeAccesorios(renglon, modelo, limites, largoCm, separacion, etiquetas, config) {
  const grupo = new THREE.Group();
  const trazos = new Trazos();
  const acc = renglon.accesorios;
  const pieza = modelo.children.find((o) => o.userData.esPiezaPrincipal);

  acc.boquetas.forEach((original, i) => {
    const b = normalizarBoqueta(original, config);
    if (b.ubicacion !== 'fondo') {
      // En una tapa: el cartel va en la boca, sobre la tapa.
      const centro = centroDeBoquetaEnTapa(renglon, b, config);
      etiquetas.push({
        ancla: grupo, posicion: v3(centro.x, centro.y, b.ubicacion === 'tapaIzquierda' ? -separacion : largoCm + separacion),
        texto: `${nombreDeBoqueta(b)} (en la tapa)`, clase: 'cota-dato', prioridad: 1,
        editar: { tipo: 'seleccionar', seleccion: { tipo: 'boqueta', indice: i } },
        titulo: 'Tocá para cambiar la boqueta, su altura o su corrimiento',
      });
      return;
    }
    const posicionCm = Math.min(Math.max(leerNumero(b.posicionCm) || 0, 0), largoCm);
    const fondo = fondoEn(pieza, posicionCm / largoCm);
    const y = limites.minY - separacion * (2.4 + i * 0.9);
    const a = v3(fondo.x, y, 0);
    const fin = v3(fondo.x, y, posicionCm);
    trazos.linea(a, fin);
    trazos.linea(fin, v3(fondo.x, fondo.y, posicionCm)); // baja hasta el centro de la boqueta
    marcas(trazos, a, fin, v3(0, -1, 0), separacion);
    etiquetas.push({
      ancla: grupo, posicion: a.clone().add(fin).multiplyScalar(0.5), texto: `boq. ${i + 1}: ${cm(leerNumero(b.posicionCm))}`,
      clase: 'cota-medida', prioridad: 2, editar: { tipo: 'boqueta-posicion', indice: i }, valor: leerNumero(b.posicionCm), unidad: 'cm',
      titulo: `Posición de la boqueta ${i + 1} (desde la punta izquierda hasta el centro)`,
    });
    etiquetas.push({
      // El cartel va en la punta de abajo de la boqueta, así no se pisa con la cota de la posición.
      ancla: grupo, posicion: v3(fondo.x, fondo.y - profundidadDeBoqueta(b) - separacion * 0.4, posicionCm), texto: nombreDeBoqueta(b),
      clase: 'cota-dato', prioridad: 1, editar: { tipo: 'seleccionar', seleccion: { tipo: 'boqueta', indice: i } },
      titulo: 'Tocá para cambiar la forma o la medida de la boqueta',
    });
  });

  const arriba = limites.maxY + separacion * 0.8;
  for (const [lado, z] of [['izquierda', 0], ['derecha', largoCm]]) {
    const tipo = tipoDeTapa(acc, lado);
    const aMedida = medidasDeTapa(acc, lado, config).aMedida ? ' a medida' : '';
    etiquetas.push({
      ancla: grupo, posicion: v3((limites.minX + limites.maxX) / 2, arriba, z),
      texto: tipo === 'ninguna' ? `sin tapa ${lado === 'izquierda' ? 'izq.' : 'der.'}` : `tapa ${tipo}${aMedida}`,
      clase: 'cota-dato', prioridad: 0, soloEdicion: tipo === 'ninguna',
      editar: { tipo: 'seleccionar', seleccion: { tipo: 'tapa', lado } },
      titulo: `Tapa ${lado}: tocá para elegir soldada, engrampada o ninguna`,
    });
  }
  grupo.add(trazos.objeto());
  return grupo;
}

// -------------------------------------------------------------
// Piezas especiales
// -------------------------------------------------------------

/**
 * Cotas dibujadas de cada generador, con las mismas proporciones que piezasEspeciales3d.js.
 * Cada una: {a, b, normal, parametro} (lineal) o {punto, parametro} (solo texto).
 * parametro 'largo' = el largo del renglón.
 */
const COTAS_ESPECIALES = {
  canoSegunForma: (p, r) => [...seccion(p, num(r.largoCm, 100), 1), largoVertical(p, 0, num(r.largoCm, 100), 'largo')],
  canoRedondo: (p, r) => COTAS_ESPECIALES.canoSegunForma({ ...p, forma: 'redonda' }, r),
  canoRectangular: (p, r) => COTAS_ESPECIALES.canoSegunForma({ ...p, forma: 'rectangular' }, r),

  boquetaSuelta(p) {
    const pestana = num(p.pestanaCm, 2);
    const boca = num(p.largoBocaCm, 10);
    const arriba = -pestana * 0.6;
    const ancho = anchoSeccion(p) / 2;
    return [
      ...seccion(p, arriba - boca, -1),
      largoVertical(p, arriba, arriba - boca, 'largoBocaCm'),
      { a: v3(ancho, 0, 0), b: v3(ancho + pestana, 0, 0), normal: v3(0, 1, 0), parametro: 'pestanaCm' },
    ];
  },

  codoRedondo(p) {
    const radio = num(p.diametroCm, 10) / 2;
    const angulo = (num(p.anguloGrados, 90) * Math.PI) / 180;
    const radioCurva = Math.max(num(p.radioCurvaCm, radio * 3), radio * 1.05);
    return [
      { a: v3(-radio, 0, 0), b: v3(radio, 0, 0), normal: v3(0, -1, 0), parametro: 'diametroCm' },
      { punto: v3(radioCurva, 0, 0), parametro: 'anguloGrados' },
      { punto: v3(radioCurva * 0.5, -radio * 0.6, 0), parametro: 'radioCurvaCm' },
      { punto: v3(radioCurva - radioCurva * Math.cos(angulo / 2) - radio * 1.6, radioCurva * Math.sin(angulo / 2) + radio * 0.6, 0), parametro: 'gajos' },
    ];
  },

  codoRectangular(p) {
    const a = num(p.ladoACm, 10);
    const b = num(p.ladoBCm, 5);
    return [
      { a: v3(-a / 2, 0, b / 2), b: v3(a / 2, 0, b / 2), normal: v3(0, -1, 0), parametro: 'ladoACm' },
      { a: v3(-a / 2, 0, -b / 2), b: v3(-a / 2, 0, b / 2), normal: v3(-1, 0, 0), parametro: 'ladoBCm' },
      { punto: v3(Math.max(num(p.radioCurvaCm, Math.max(a, b) * 1.6), Math.max(a, b) / 2), 0, 0), parametro: 'anguloGrados' },
      { punto: v3(Math.max(a, b) * 0.8, -b * 0.8, 0), parametro: 'radioCurvaCm' },
    ];
  },

  ramal(p) {
    const radio = num(p.diametroCm, 10) / 2;
    const radioRamal = num(p.diametroRamalCm, radio * 2) / 2;
    const angulo = (num(p.anguloGrados, 45) * Math.PI) / 180;
    const direccion = v3(Math.sin(angulo), Math.cos(angulo), 0);
    const perpendicular = v3(Math.cos(angulo), -Math.sin(angulo), 0);
    const largo = num(p.largoPrincipalCm, radio * 8);
    const largoRamal = num(p.largoRamalCm, radio * 5);
    const base = v3(0, largo * (3 / 8), 0);
    const punta = base.clone().addScaledVector(direccion, largoRamal);
    return [
      { a: v3(-radio, 0, 0), b: v3(radio, 0, 0), normal: v3(0, -1, 0), parametro: 'diametroCm' },
      { a: v3(-radio, 0, 0), b: v3(-radio, largo, 0), normal: v3(-1, 0, 0), parametro: 'largoPrincipalCm' },
      { a: punta.clone().addScaledVector(perpendicular, -radioRamal), b: punta.clone().addScaledVector(perpendicular, radioRamal), normal: direccion, parametro: 'diametroRamalCm' },
      { a: base.clone().addScaledVector(perpendicular, radioRamal), b: punta.clone().addScaledVector(perpendicular, radioRamal), normal: perpendicular, parametro: 'largoRamalCm' },
      { punto: base.clone().addScaledVector(direccion.clone().add(v3(0, 1, 0)).normalize(), radio * 2.6), parametro: 'anguloGrados' },
    ];
  },

  embudo(p) {
    const a = num(p.bocaACm, 30);
    const b = num(p.bocaBCm, 15);
    const radioSalida = num(p.diametroSalidaCm, 10) / 2;
    const alto = num(p.altoCm, 20);
    return [
      { a: v3(-a / 2, alto, b / 2), b: v3(a / 2, alto, b / 2), normal: v3(0, 1, 0), parametro: 'bocaACm' },
      { a: v3(a / 2, alto, -b / 2), b: v3(a / 2, alto, b / 2), normal: v3(1, 0, 0), parametro: 'bocaBCm' },
      { a: v3(-radioSalida, -radioSalida * 2, 0), b: v3(radioSalida, -radioSalida * 2, 0), normal: v3(0, -1, 0), parametro: 'diametroSalidaCm' },
      { a: v3(-a / 2, 0, 0), b: v3(-a / 2, alto, 0), normal: v3(-1, 0, 0), parametro: 'altoCm' },
    ];
  },

  reduccion(p) {
    const mayor = num(p.diametroMayorCm, 15) / 2;
    const menor = num(p.diametroMenorCm, 10) / 2;
    const alto = num(p.altoCm, 10);
    return [
      { a: v3(-mayor, alto, 0), b: v3(mayor, alto, 0), normal: v3(0, 1, 0), parametro: 'diametroMayorCm' },
      { a: v3(-menor, 0, 0), b: v3(menor, 0, 0), normal: v3(0, -1, 0), parametro: 'diametroMenorCm' },
      { a: v3(-mayor, 0, 0), b: v3(-mayor, alto, 0), normal: v3(-1, 0, 0), parametro: 'altoCm' },
    ];
  },

  sombreroChino: (p) => cotasDeSombrero(p, { ala: 0.9, techo: 1.1, alTecho: (r, cano) => cano + num(p.separacionCm, r * 0.8) }),
  sombreroCanadiense: (p) => cotasDeSombrero(p, { ala: 1, techo: 1.2, alTecho: (r, cano) => cano + r * 0.2 + num(p.altoFaldonCm, r * 0.9) }),
  sombreroSpiro: (p) => cotasDeSombrero(p, { ala: 0.9, techo: 1, alTecho: (r, cano) => cano + r * 1.8 }),
  sombreroH(p) {
    const r = medidaReferencia(p);
    const cano = num(p.altoCanoCm, r * 4);
    const separacion = num(p.separacionCm, r * 7);
    const yTravesano = cano + r * 0.6;
    const altoPatas = num(p.altoPatasCm, r * 3.2);
    return [
      ...seccion(p, 0, -1),
      largoVertical(p, 0, cano, 'altoCanoCm'),
      { a: v3(-separacion / 2, yTravesano + altoPatas / 2, 0), b: v3(separacion / 2, yTravesano + altoPatas / 2, 0), normal: v3(0, 1, 0), parametro: 'separacionCm' },
      { a: v3(separacion / 2 + r, yTravesano - altoPatas / 2, 0), b: v3(separacion / 2 + r, yTravesano + altoPatas / 2, 0), normal: v3(1, 0, 0), parametro: 'altoPatasCm' },
    ];
  },
};

/** Sombreros con caño, ala y techo: Ø o lados del caño, alto del caño, ala y alto del techo. */
function cotasDeSombrero(p, proporciones) {
  const r = medidaReferencia(p);
  const cano = num(p.altoCanoCm, r * 3);
  const ala = num(p.alaCm, r * proporciones.ala);
  const altoTecho = num(p.altoTechoCm, r * proporciones.techo);
  const yTecho = proporciones.alTecho(r, cano);
  return [
    ...seccion(p, 0, -1),
    largoVertical(p, 0, cano, 'altoCanoCm'),
    { a: v3(r, yTecho, 0), b: v3(r + ala, yTecho, 0), normal: v3(0, -1, 0), parametro: 'alaCm' },
    { a: v3(r + ala, yTecho, 0), b: v3(r + ala, yTecho + altoTecho, 0), normal: v3(1, 0, 0), parametro: 'altoTechoCm' },
  ];
}

/** Ancho de la sección (para correr las cotas verticales hacia afuera del caño). */
function anchoSeccion(p) {
  if (p.forma === 'rectangular' || p.forma === 'cuadrada') return num(p.ladoACm, 10);
  if (p.diametroCm === undefined && (p.ladoACm !== undefined)) return num(p.ladoACm, 10);
  return medidaReferencia(p) * 2;
}

/** Cotas de la sección del caño a la altura y: Ø, lado o lados a y b. */
function seccion(p, y, haciaY) {
  const normal = v3(0, haciaY, 0);
  if (p.forma === 'rectangular') {
    const a = num(p.ladoACm, 20);
    const b = num(p.ladoBCm, 10);
    return [
      { a: v3(-a / 2, y, b / 2), b: v3(a / 2, y, b / 2), normal, parametro: 'ladoACm' },
      { a: v3(a / 2, y, -b / 2), b: v3(a / 2, y, b / 2), normal, parametro: 'ladoBCm' },
    ];
  }
  if (p.forma === 'cuadrada') {
    const a = num(p.ladoACm, 10);
    return [{ a: v3(-a / 2, y, a / 2), b: v3(a / 2, y, a / 2), normal, parametro: 'ladoACm' }];
  }
  const radio = num(p.diametroCm, 15) / 2;
  return [{ a: v3(-radio, y, 0), b: v3(radio, y, 0), normal, parametro: 'diametroCm' }];
}

/** Cota vertical al costado del caño, de y1 a y2. */
function largoVertical(p, y1, y2, parametro) {
  const x = -anchoSeccion(p) / 2;
  return { a: v3(x, y1, 0), b: v3(x, y2, 0), normal: v3(-1, 0, 0), parametro };
}

function cotasDeEspecial(renglon, datos, modelo, largoCm, etiquetas, ficha) {
  const grupo = new THREE.Group();
  const trazos = new Trazos();
  const p = renglon.parametros || {};
  const plantilla = buscarPlantilla(datos.catalogo, renglon.plantillaId) || {};
  const definiciones = parametrosVisibles(plantilla, p);
  const caja = new THREE.Box3().setFromObject(modelo.children.find((o) => o.userData.esPiezaPrincipal) || modelo);
  const tamano = caja.getSize(new THREE.Vector3());
  const separacion = Math.max(Math.max(tamano.x, tamano.y, tamano.z) * 0.1, 1);
  const dibujadas = new Set();

  const definicionDe = (id) => definiciones.find((d) => d.id === id);
  const textoDe = (id) => {
    if (id === 'largo') return `${formatearNumero(largoCm / 100, 2)} m`;
    const d = definicionDe(id);
    const valor = p[id];
    if (d?.tipo === 'opciones') return d.opciones.find((o) => String(o.valor) === String(valor))?.etiqueta ?? String(valor);
    const n = leerNumero(valor);
    const texto = cm(n);
    if (d?.tipo === 'diametro') return `Ø${texto}`;
    if (id === 'gajos') return `${texto} gajos`;
    return texto;
  };
  const etiquetaDe = (id, posicion, prioridad) => {
    const d = definicionDe(id);
    if (id !== 'largo' && !d) return null;
    dibujadas.add(id);
    return {
      ancla: grupo, posicion, texto: textoDe(id), clase: d?.tipo === 'opciones' ? 'cota-dato' : 'cota-medida', prioridad,
      editar: id === 'largo' ? { tipo: 'largo' } : { tipo: 'parametro', id },
      valor: id === 'largo' ? largoCm / 100 : p[id], unidad: id === 'largo' ? 'm' : (d.unidad || ''),
      opciones: d?.tipo === 'opciones' ? d.opciones : null,
      titulo: `${id === 'largo' ? 'Largo' : d.etiqueta}: tocá para cambiarlo`,
    };
  };

  const generador = COTAS_ESPECIALES[renglon.generador3d];
  for (const cota of generador ? generador(p, renglon) : []) {
    if (cota.parametro !== 'largo' && !definicionDe(cota.parametro)) continue;
    const posicion = cota.punto ? cota.punto.clone() : cotaLineal(trazos, cota.a, cota.b, cota.normal, separacion);
    const etiqueta = etiquetaDe(cota.parametro, posicion, cota.punto ? 1 : 3);
    if (etiqueta) etiquetas.push(etiqueta);
  }

  // El resto de los datos (forma, modelo, pestaña de la tapa…) van en la ficha de la esquina.
  for (const d of definiciones) {
    if (dibujadas.has(d.id)) continue;
    ficha.push({
      texto: `${d.etiqueta}: ${textoDe(d.id)}${d.tipo !== 'opciones' && d.unidad ? ` ${d.unidad}` : ''}`,
      editar: { tipo: 'parametro', id: d.id }, valor: p[d.id], unidad: d.unidad || '',
      opciones: d.tipo === 'opciones' ? d.opciones : null, titulo: `${d.etiqueta}: tocá para cambiarlo`,
    });
  }
  if (renglon.usaLargo && !dibujadas.has('largo')) {
    ficha.push({ texto: `Largo: ${textoDe('largo')}`, editar: { tipo: 'largo' }, valor: largoCm / 100, unidad: 'm', titulo: 'Largo: tocá para cambiarlo' });
  }
  grupo.add(trazos.objeto());
  return grupo;
}
