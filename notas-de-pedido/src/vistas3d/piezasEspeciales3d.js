// =============================================================
// piezasEspeciales3d.js
// Piezas que no se arman por tramos: caños, boquetas, codos, ramales,
// reducciones, embudos, sombreros, media caña y tapas.
// Todas en cm. Las piezas verticales (caños, sombreros…) crecen hacia +Y.
// Las formas son aproximadas: sirven como AYUDA VISUAL. La referencia para
// fabricar es el esquema 2D acotado.
// =============================================================

import * as THREE from 'three';
import { leerNumero } from '../logica/numeros.js';
import { calcularGeometria, ladoPintadoDelPerfil } from '../logica/geometria.js';
import { construirDesdeSegmentos } from './extrusion.js';

const num = (valor, porDefecto) => {
  const n = leerNumero(valor);
  return Number.isFinite(n) && n > 0 ? n : porDefecto;
};

/**
 * Agrega una superficie con cara de afuera y cara de adentro (dos mallas):
 * afuera = lado hacia donde apuntan las normales de la geometría.
 */
function superficie(geometria, materiales, ladoPintura) {
  const grupo = new THREE.Group();
  const pintadoAfuera = !materiales.esPrepintada || ladoPintura !== 'adentro';
  const afuera = (pintadoAfuera ? materiales.pintado : materiales.sinPintar).clone();
  const adentro = (pintadoAfuera ? materiales.sinPintar : materiales.pintado).clone();
  afuera.side = THREE.FrontSide;
  adentro.side = THREE.BackSide;
  grupo.add(new THREE.Mesh(geometria, afuera));
  grupo.add(new THREE.Mesh(geometria, adentro));
  return grupo;
}

/** Caño abierto (cilindro sin tapas). Si lados = 4 queda cuadrado (se escala a rectángulo afuera). */
function tubo(radio, alto, materiales, ladoPintura, lados = 48, radioArriba = radio) {
  const geometria = new THREE.CylinderGeometry(radioArriba, radio, alto, lados, 1, true);
  geometria.translate(0, alto / 2, 0); // la base queda en y = 0
  return superficie(geometria, materiales, ladoPintura);
}

/** Caño rectangular a × b de alto dado (base en y = 0). */
function tuboRectangular(a, b, alto, materiales, ladoPintura) {
  const geometria = new THREE.CylinderGeometry(Math.SQRT1_2, Math.SQRT1_2, alto, 4, 1, true);
  geometria.rotateY(Math.PI / 4);
  geometria.scale(a, 1, b);
  geometria.translate(0, alto / 2, 0);
  return superficie(geometria, materiales, ladoPintura);
}

/**
 * Transición entre dos "anillos" de puntos (por ejemplo rectángulo arriba y círculo abajo).
 * Los dos anillos tienen la misma cantidad de puntos.
 */
function transicion(anilloArriba, anilloAbajo, yArriba, yAbajo, materiales, ladoPintura) {
  const posiciones = [];
  const n = anilloArriba.length;
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    const a1 = [anilloArriba[i].x, yArriba, anilloArriba[i].z];
    const a2 = [anilloArriba[j].x, yArriba, anilloArriba[j].z];
    const b1 = [anilloAbajo[i].x, yAbajo, anilloAbajo[i].z];
    const b2 = [anilloAbajo[j].x, yAbajo, anilloAbajo[j].z];
    posiciones.push(...a1, ...b1, ...b2, ...a1, ...b2, ...a2);
  }
  const geometria = new THREE.BufferGeometry();
  geometria.setAttribute('position', new THREE.Float32BufferAttribute(posiciones, 3));
  geometria.computeVertexNormals();
  return superficie(geometria, materiales, ladoPintura);
}

function anilloCircular(radio, cantidad) {
  return Array.from({ length: cantidad }, (_, i) => {
    const angulo = (i / cantidad) * Math.PI * 2;
    return { x: radio * Math.cos(angulo), z: -radio * Math.sin(angulo) };
  });
}

/** Puntos repartidos sobre el contorno de un rectángulo a × b, en el mismo orden angular que el círculo. */
function anilloRectangular(a, b, cantidad) {
  return Array.from({ length: cantidad }, (_, i) => {
    const angulo = (i / cantidad) * Math.PI * 2;
    const cx = Math.cos(angulo);
    const sz = -Math.sin(angulo);
    const factor = Math.min((a / 2) / Math.max(Math.abs(cx), 1e-9), (b / 2) / Math.max(Math.abs(sz), 1e-9));
    return { x: cx * factor, z: sz * factor };
  });
}

/** Cono abierto (para sombreros). La punta en y = alto si haciaArriba. */
function cono(radio, alto, materiales, ladoPintura, haciaArriba = true) {
  const geometria = new THREE.ConeGeometry(radio, alto, 48, 1, true);
  if (!haciaArriba) geometria.rotateX(Math.PI);
  geometria.translate(0, alto / 2, 0);
  return superficie(geometria, materiales, ladoPintura);
}

/** Patitas finas que sostienen el sombrero. */
function patitas(radio, desde, hasta, materiales) {
  const grupo = new THREE.Group();
  for (let i = 0; i < 3; i++) {
    const angulo = (i / 3) * Math.PI * 2;
    const pata = new THREE.Mesh(new THREE.BoxGeometry(0.8, hasta - desde, 0.3), materiales.pintado.clone());
    pata.position.set(radio * Math.cos(angulo), (desde + hasta) / 2, radio * Math.sin(angulo));
    pata.rotation.y = -angulo;
    grupo.add(pata);
  }
  return grupo;
}

/** Caño según la forma: redondo / circular (Ø), cuadrado (a × a) o rectangular (a × b). */
function tuboSegunForma(p, alto, m, lado, escala = 1) {
  if (p.forma === 'rectangular') return tuboRectangular(num(p.ladoACm, 20) * escala, num(p.ladoBCm, 10) * escala, alto, m, lado);
  if (p.forma === 'cuadrada') return tuboRectangular(num(p.ladoACm, 10) * escala, num(p.ladoACm, 10) * escala, alto, m, lado);
  return tubo((num(p.diametroCm, 15) / 2) * escala, alto, m, lado);
}

/** "Techo" del sombrero: cono (circular) o pirámide (rectangular). */
function techoSegunForma(p, factor, alto, m, lado, haciaArriba = true) {
  if (p.forma !== 'rectangular') return cono((num(p.diametroCm, 15) / 2) * factor, alto, m, lado, haciaArriba);
  const geometria = new THREE.ConeGeometry(Math.SQRT1_2, alto, 4, 1, true);
  geometria.rotateY(Math.PI / 4);
  if (!haciaArriba) geometria.rotateX(Math.PI);
  geometria.scale(num(p.ladoACm, 20) * factor, 1, num(p.ladoBCm, 10) * factor);
  geometria.translate(0, alto / 2, 0);
  return superficie(geometria, m, lado);
}

/** Medida de referencia del sombrero (para las proporciones). */
function medidaReferencia(p) {
  return p.forma === 'rectangular' ? Math.max(num(p.ladoACm, 20), num(p.ladoBCm, 10)) / 2 : num(p.diametroCm, 15) / 2;
}

// -------------------------------------------------------------
// Generadores: cada uno recibe (parametros, renglon, materiales, config)
// -------------------------------------------------------------

export const GENERADORES = {
  canoRedondo(p, r, m) {
    return tubo(num(p.diametroCm, 10) / 2, num(r.largoCm, 100), m, r.ladoPintura);
  },

  canoRectangular(p, r, m) {
    return tuboRectangular(num(p.ladoACm, 10), num(p.ladoBCm, 5), num(r.largoCm, 100), m, r.ladoPintura);
  },

  boquetaRedonda(p, r, m) {
    const radio = num(p.diametroCm, 10) / 2;
    const boca = num(p.largoBocaCm, 10);
    const pestana = num(p.pestanaCm, 2);
    const grupo = new THREE.Group();
    // Pestaña: embudito de arriba que apoya en el fondo de la canaleta.
    const embudo = tubo(radio, pestana * 0.6, m, r.ladoPintura, 48, radio + pestana);
    embudo.position.y = -pestana * 0.6;
    grupo.add(embudo);
    const cano = tubo(radio, boca, m, r.ladoPintura);
    cano.position.y = -pestana * 0.6 - boca;
    grupo.add(cano);
    return grupo; // la parte de arriba queda en y = 0 (para montarla bajo la canaleta)
  },

  boquetaRectangular(p, r, m) {
    const a = num(p.ladoACm, 10);
    const b = num(p.ladoBCm, 5);
    const boca = num(p.largoBocaCm, 10);
    const pestana = num(p.pestanaCm, 2);
    const grupo = new THREE.Group();
    const embudo = transicion(anilloRectangular(a + 2 * pestana, b + 2 * pestana, 48), anilloRectangular(a, b, 48), 0, -pestana * 0.6, m, r.ladoPintura);
    grupo.add(embudo);
    const cano = tuboRectangular(a, b, boca, m, r.ladoPintura);
    cano.position.y = -pestana * 0.6 - boca;
    grupo.add(cano);
    return grupo;
  },

  /** Boqueta suelta o puesta en la canaleta: redonda, cuadrada o rectangular. */
  boquetaSuelta(p, r, m) {
    if (p.forma === 'redonda') return GENERADORES.boquetaRedonda(p, r, m);
    const lados = p.forma === 'cuadrada' ? { ...p, ladoBCm: p.ladoACm } : p;
    return GENERADORES.boquetaRectangular(lados, r, m);
  },

  codoRedondo(p, r, m) {
    const radio = num(p.diametroCm, 10) / 2;
    const angulo = (num(p.anguloGrados, 90) * Math.PI) / 180;
    const gajos = Math.max(2, Math.round(num(p.gajos, 4)));
    const radioCurva = radio * 3;
    // Arco que arranca en el origen subiendo (+Y) y dobla hacia +X.
    class Arco extends THREE.Curve {
      getPoint(t, destino = new THREE.Vector3()) {
        const a = t * angulo;
        return destino.set(radioCurva - radioCurva * Math.cos(a), radioCurva * Math.sin(a), 0);
      }
    }
    // tubularSegments = gajos: cada gajo es un tramo recto, como el codo real.
    const geometria = new THREE.TubeGeometry(new Arco(), gajos, radio, 40, false);
    return superficie(geometria, m, r.ladoPintura);
  },

  codoRectangular(p, r, m) {
    // Caño rectangular a × b que sigue un arco, armado por 4 gajos rectos.
    const a = num(p.ladoACm, 10);
    const b = num(p.ladoBCm, 5);
    const angulo = (num(p.anguloGrados, 90) * Math.PI) / 180;
    const radioCurva = Math.max(a, b) * 1.6;
    class Arco extends THREE.Curve {
      getPoint(t, destino = new THREE.Vector3()) {
        const ang = t * angulo;
        return destino.set(radioCurva - radioCurva * Math.cos(ang), radioCurva * Math.sin(ang), 0);
      }
    }
    const seccion = new THREE.Shape();
    seccion.moveTo(-a / 2, -b / 2);
    seccion.lineTo(a / 2, -b / 2);
    seccion.lineTo(a / 2, b / 2);
    seccion.lineTo(-a / 2, b / 2);
    seccion.closePath();
    const geometria = new THREE.ExtrudeGeometry(seccion, { steps: 4, bevelEnabled: false, extrudePath: new Arco() });
    // Grupo 0 = tapas de las puntas (se ocultan: el codo es hueco); grupo 1 = paredes.
    const oculto = new THREE.MeshBasicMaterial({ visible: false });
    const paredes = m.pintado.clone();
    paredes.side = THREE.DoubleSide;
    return new THREE.Mesh(geometria, [oculto, paredes]);
  },

  ramal(p, r, m) {
    const radio = num(p.diametroCm, 10) / 2;
    const radioRamal = num(p.diametroRamalCm, radio * 2) / 2;
    const angulo = (num(p.anguloGrados, 45) * Math.PI) / 180;
    const grupo = new THREE.Group();
    grupo.add(tubo(radio, radio * 8, m, r.ladoPintura));
    const ramal = tubo(radioRamal, radio * 5, m, r.ladoPintura);
    ramal.position.set(0, radio * 3, 0);
    ramal.rotation.z = -angulo;
    grupo.add(ramal);
    return grupo;
  },

  reduccion(p, r, m) {
    const mayor = num(p.diametroMayorCm, 15) / 2;
    const menor = num(p.diametroMenorCm, 10) / 2;
    return tubo(menor, num(p.altoCm, 10), m, r.ladoPintura, 48, mayor);
  },

  embudo(p, r, m) {
    const a = num(p.bocaACm, 30);
    const b = num(p.bocaBCm, 15);
    const radioSalida = num(p.diametroSalidaCm, 10) / 2;
    const alto = num(p.altoCm, 20);
    const grupo = new THREE.Group();
    grupo.add(transicion(anilloRectangular(a, b, 64), anilloCircular(radioSalida, 64), alto, 0, m, r.ladoPintura));
    const salida = tubo(radioSalida, radioSalida * 2, m, r.ladoPintura);
    salida.position.y = -radioSalida * 2;
    grupo.add(salida);
    return grupo;
  },

  sombreroChino(p, r, m) {
    const radio = medidaReferencia(p);
    const grupo = new THREE.Group();
    grupo.add(tuboSegunForma(p, radio * 3, m, r.ladoPintura));
    const techo = techoSegunForma(p, 1.9, radio * 1.1, m, r.ladoPintura);
    techo.position.y = radio * 3.8;
    grupo.add(techo);
    grupo.add(patitas(radio * 0.95, radio * 2.6, radio * 3.9, m));
    return grupo;
  },

  sombreroCanadiense(p, r, m) {
    // Salamandra / canadiense: caño, faldón y techo cónico (forma aproximada, ver PENDIENTES.md).
    const radio = medidaReferencia(p);
    const grupo = new THREE.Group();
    grupo.add(tuboSegunForma(p, radio * 3, m, r.ladoPintura));
    const faldon = tuboSegunForma(p, radio * 0.9, m, r.ladoPintura, 1.8);
    faldon.position.y = radio * 3.2;
    grupo.add(faldon);
    const techo = techoSegunForma(p, 2, radio * 1.2, m, r.ladoPintura);
    techo.position.y = radio * 4.1;
    grupo.add(techo);
    grupo.add(patitas(radio * 0.95, radio * 2.6, radio * 3.3, m));
    return grupo;
  },

  sombreroH(p, r, m) {
    // Sombrero "H": el caño sube hasta un travesaño horizontal que une dos caños verticales abiertos.
    const radio = medidaReferencia(p);
    const grupo = new THREE.Group();
    grupo.add(tuboSegunForma(p, radio * 4, m, r.ladoPintura));
    const travesano = tuboSegunForma(p, radio * 7, m, r.ladoPintura);
    travesano.rotation.z = Math.PI / 2;
    travesano.position.set(radio * 3.5, radio * 4.6, 0);
    grupo.add(travesano);
    // Los dos caños verticales de las puntas (las "patas" de la H), abiertos arriba y abajo.
    for (const x of [-radio * 3.5, radio * 3.5]) {
      const pata = tuboSegunForma(p, radio * 3.2, m, r.ladoPintura);
      pata.position.set(x, radio * 3, 0);
      grupo.add(pata);
    }
    return grupo;
  },

  sombreroSpiro(p, r, m) {
    // Tipo Spiro: caño con varios aros cónicos apilados y techo (forma aproximada).
    const radio = medidaReferencia(p);
    const grupo = new THREE.Group();
    grupo.add(tuboSegunForma(p, radio * 3, m, r.ladoPintura));
    for (let i = 0; i < 3; i++) {
      const aro = techoSegunForma(p, 1.7, radio * 0.45, m, r.ladoPintura, false);
      aro.position.y = radio * (3.2 + i * 0.5);
      grupo.add(aro);
    }
    const techo = techoSegunForma(p, 1.9, radio * 1, m, r.ladoPintura);
    techo.position.y = radio * 4.8;
    grupo.add(techo);
    grupo.add(patitas(radio * 0.95, radio * 2.6, radio * 4.9, m));
    return grupo;
  },

  mediaCana(p, r, m, config) {
    const radio = num(p.diametroCm, 12.5) / 2;
    const dobladillo = num(p.dobladilloCm, 1);
    const pestana = num(p.pestanaCm, 3);
    // Perfil: dobladillo del frente, media caña (medio círculo de abajo) y pestaña trasera.
    const puntos = [{ x: -radio - 0.3, y: dobladillo }, { x: -radio - 0.3, y: 0 }, { x: -radio, y: 0 }];
    const pasos = 24;
    for (let i = 1; i <= pasos; i++) {
      const angulo = Math.PI + (i / pasos) * Math.PI;
      puntos.push({ x: radio * Math.cos(angulo), y: radio * Math.sin(angulo) });
    }
    puntos.push({ x: radio + pestana * Math.SQRT1_2, y: pestana * Math.SQRT1_2 });
    const segmentos = puntos.slice(1).map((fin, i) => ({ indice: i, inicio: puntos[i], fin }));
    // Gira a la izquierda (antihorario) → el exterior queda a la derecha del recorrido.
    const pintadoAfuera = r.ladoPintura !== 'adentro';
    const lados = m.esPrepintada
      ? (pintadoAfuera ? { izquierda: m.sinPintar, derecha: m.pintado } : { izquierda: m.pintado, derecha: m.sinPintar })
      : { izquierda: m.pintado, derecha: m.pintado };
    return construirDesdeSegmentos(segmentos, num(r.largoCm, 100), lados, config);
  },

  tapa(p, r, m, config) {
    return construirTapa(r, m, config, 0, 1);
  },
};

/**
 * Tapa de canaleta: chapa con la forma del perfil + pestaña de apoyo alrededor.
 * @param {number} z        dónde va la tapa (0 = punta izquierda de la canaleta)
 * @param {number} sentidoZ +1 = la pestaña entra hacia +Z; −1 = hacia −Z
 */
export function construirTapa(renglonTapa, materiales, config, z, sentidoZ) {
  const grupo = new THREE.Group();
  const perfil = renglonTapa.perfil;
  if (!perfil?.tramos?.length) return grupo;
  const geometria = calcularGeometria(perfil, config);
  const pestana = num(renglonTapa.parametros?.pestanaApoyoCm, 1.5);

  // 1) Chapa plana con la forma del perfil.
  const forma = new THREE.Shape(geometria.puntos.map((q) => new THREE.Vector2(q.x, q.y)));
  const plano = superficie(new THREE.ShapeGeometry(forma), materiales, renglonTapa.ladoPintura);
  plano.position.z = z;
  grupo.add(plano);

  // 2) Pestaña de apoyo: el mismo perfil, estirado solo `pestana` cm hacia adentro de la canaleta.
  const ladoPintado = materiales.esPrepintada ? ladoPintadoDelPerfil(perfil, renglonTapa.ladoPintura || 'afuera', config) : 'izquierda';
  const lados = ladoPintado === 'izquierda'
    ? { izquierda: materiales.pintado, derecha: materiales.sinPintar }
    : { izquierda: materiales.sinPintar, derecha: materiales.pintado };
  const borde = construirDesdeSegmentos(geometria.segmentos.map((s) => ({ indice: s.indice, inicio: s.inicio, fin: s.fin })), pestana, lados, config);
  borde.position.z = sentidoZ > 0 ? z : z - pestana;
  grupo.add(borde);
  return grupo;
}
