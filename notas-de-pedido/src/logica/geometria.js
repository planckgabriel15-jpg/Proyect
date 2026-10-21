// =============================================================
// geometria.js
// Convierte la lista de tramos en puntos 2D (el "dibujo" del perfil).
// Puro: no usa el navegador ni Three.js. Lo usan el SVG y el 3D.
//
// Reglas (sección 6):
// - Se parte de (0,0) con la dirección inicial (arriba, abajo, izquierda,
//   derecha o un ángulo en grados). 0° = derecha, 90° = arriba (como en
//   matemática: el eje Y crece hacia arriba).
// - En cada tramo la dirección gira (180 − anguloPliegue) grados hacia el
//   sentido indicado (izquierda = antihorario, derecha = horario) y se
//   avanza medidaCm.
// - Dobladillos: el giro es siempre de 180° (vuelve sobre sí mismo).
//   Si el dobladillo es el PRIMER tramo, el giro de 180° está en la unión
//   con el SEGUNDO tramo (SUPUESTO aprobado, ver PENDIENTES.md).
//   Para que se vea, se separa con una "luz" chica que NO suma al desarrollo.
// =============================================================

import { leerNumero, redondear } from './numeros.js';

export const DIRECCIONES = { derecha: 0, arriba: 90, izquierda: 180, abajo: 270 };

export const TIPOS_DE_TRAMO = ['normal', 'dobladillo', 'dobladillo_aplastado', 'pestana_engrafe'];

/** ¿Este tramo es un dobladillo (abierto o aplastado)? */
export function esDobladillo(tramo) {
  return tramo && (tramo.tipo === 'dobladillo' || tramo.tipo === 'dobladillo_aplastado');
}

/** Convierte "arriba" / "derecha" / 45 / "45" en grados. */
export function direccionEnGrados(direccionInicial) {
  if (direccionInicial in DIRECCIONES) {
    return DIRECCIONES[direccionInicial];
  }
  const grados = leerNumero(direccionInicial);
  return Number.isFinite(grados) ? normalizarGrados(grados) : DIRECCIONES.arriba;
}

/** Lleva cualquier ángulo al rango 0 a 360 (sin incluir 360). */
export function normalizarGrados(grados) {
  const resultado = ((grados % 360) + 360) % 360;
  return redondear(resultado, 6) === 360 ? 0 : redondear(resultado, 6);
}

/** Si la dirección coincide con arriba/abajo/izquierda/derecha devuelve el nombre; si no, los grados. */
export function nombreDeDireccion(grados) {
  const normalizado = normalizarGrados(grados);
  for (const [nombre, valor] of Object.entries(DIRECCIONES)) {
    if (valor === normalizado) {
      return nombre;
    }
  }
  return normalizado;
}

/**
 * Dice cómo gira el perfil al llegar al tramo número `indice`.
 * @returns {{giroGrados: number, sentido: string, esVuelta: boolean, luzCm: number, anguloInterior: number|null}}
 *   giroGrados: cuánto gira la dirección (0 en el primer tramo)
 *   esVuelta: true si es un pliegue de 180° (dobladillo)
 *   anguloInterior: el ángulo que se acota en el dibujo (null en el primer tramo)
 */
export function giroEnTramo(tramos, indice, config) {
  const tramo = tramos[indice];
  if (indice === 0) {
    return { giroGrados: 0, sentido: tramo.sentido || 'izquierda', esVuelta: false, luzCm: 0, anguloInterior: null };
  }

  // ¿Este pliegue es de 180° por un dobladillo?
  // a) el tramo actual es un dobladillo, o
  // b) el tramo anterior es el primero y es un dobladillo.
  let tramoDobladillo = null;
  if (esDobladillo(tramo)) {
    tramoDobladillo = tramo;
  } else if (indice === 1 && esDobladillo(tramos[0])) {
    tramoDobladillo = tramos[0];
  }

  if (tramoDobladillo) {
    const luzCm = tramoDobladillo.tipo === 'dobladillo_aplastado'
      ? config.dibujo.luzDobladilloAplastadoCm
      : config.dibujo.luzDobladilloAbiertoCm;
    return { giroGrados: 180, sentido: tramo.sentido || 'izquierda', esVuelta: true, luzCm, anguloInterior: 0 };
  }

  const anguloInterior = leerNumero(tramo.anguloPliegue);
  const angulo = Number.isFinite(anguloInterior) ? anguloInterior : config.anguloPorDefecto;
  return { giroGrados: 180 - angulo, sentido: tramo.sentido || 'izquierda', esVuelta: false, luzCm: 0, anguloInterior: angulo };
}

/** Punto que está a `distancia` de `punto` en la dirección `grados`. */
function avanzar(punto, grados, distancia) {
  const radianes = (grados * Math.PI) / 180;
  return {
    x: redondear(punto.x + distancia * Math.cos(radianes), 6),
    y: redondear(punto.y + distancia * Math.sin(radianes), 6),
  };
}

/**
 * Calcula todo lo necesario para dibujar el perfil.
 * @param {{direccionInicial: string|number, tramos: Array}} perfil
 * @param {object} config  datos/config.json
 * @returns {{
 *   puntos: Array<{x:number,y:number}>,      // la línea completa, en orden (incluye la luz de los dobladillos)
 *   segmentos: Array<{indice:number, inicio:{x,y}, fin:{x,y}, direccion:number, tramo:object}>, // un segmento por tramo
 *   pliegues: Array<{indice:number, punto:{x,y}, anguloInterior:number|null, sentido:string, esVuelta:boolean, direccionAntes:number, direccionDespues:number}>
 * }}
 */
export function calcularGeometria(perfil, config) {
  const tramos = perfil.tramos || [];
  let direccion = direccionEnGrados(perfil.direccionInicial);
  let posicion = { x: 0, y: 0 };
  const puntos = [{ ...posicion }];
  const segmentos = [];
  const pliegues = [];

  tramos.forEach((tramo, indice) => {
    const medidaLeida = leerNumero(tramo.medidaCm);
    const medidaCm = Number.isFinite(medidaLeida) && medidaLeida > 0 ? medidaLeida : 0;
    const giro = giroEnTramo(tramos, indice, config);
    const direccionAntes = direccion;

    if (indice > 0) {
      const signo = giro.sentido === 'derecha' ? -1 : 1;
      if (giro.esVuelta && giro.luzCm > 0) {
        // Corremos el punto de arranque hacia el lado del giro, solo para que se vea.
        posicion = avanzar(posicion, direccion + signo * 90, giro.luzCm);
        puntos.push({ ...posicion });
      }
      direccion = normalizarGrados(direccion + signo * giro.giroGrados);
      pliegues.push({
        indice,
        punto: { ...posicion },
        anguloInterior: giro.anguloInterior,
        sentido: giro.sentido,
        esVuelta: giro.esVuelta,
        direccionAntes,
        direccionDespues: direccion,
      });
    }

    const inicio = { ...posicion };
    posicion = avanzar(posicion, direccion, medidaCm);
    puntos.push({ ...posicion });
    segmentos.push({ indice, inicio, fin: { ...posicion }, direccion, tramo });
  });

  return { puntos, segmentos, pliegues };
}

/** Atajo: solo la lista de puntos (es lo que pide el caso de prueba 15). */
export function calcularPuntos(perfil, config) {
  return calcularGeometria(perfil, config).puntos;
}

/** Rectángulo que encierra todos los puntos (sirve para escalar el dibujo). */
export function calcularLimites(puntos) {
  if (!puntos || puntos.length === 0) {
    return { minX: 0, minY: 0, maxX: 0, maxY: 0, ancho: 0, alto: 0 };
  }
  const xs = puntos.map((p) => p.x);
  const ys = puntos.map((p) => p.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  return { minX, minY, maxX, maxY, ancho: maxX - minX, alto: maxY - minY };
}

// -------------------------------------------------------------
// Dibujo a mano: puntos → tramos
// -------------------------------------------------------------

/**
 * "Imán": acomoda el punto que tocó el vendedor.
 * - Si no hay punto anterior: lo lleva a la cuadrícula de 1 cm.
 * - Si hay punto anterior: redondea el ángulo a múltiplos de 15° y la distancia a 1 cm.
 */
export function imantarPunto(punto, puntoAnterior, config) {
  const pasoCm = config.dibujo.imanCuadriculaCm;
  const pasoAngulo = config.dibujo.imanAnguloGrados;
  if (!puntoAnterior) {
    return {
      x: redondear(Math.round(punto.x / pasoCm) * pasoCm, 6),
      y: redondear(Math.round(punto.y / pasoCm) * pasoCm, 6),
    };
  }
  const dx = punto.x - puntoAnterior.x;
  const dy = punto.y - puntoAnterior.y;
  const distancia = Math.round(Math.hypot(dx, dy) / pasoCm) * pasoCm;
  const angulo = Math.round((Math.atan2(dy, dx) * 180) / Math.PI / pasoAngulo) * pasoAngulo;
  return avanzar(puntoAnterior, angulo, distancia);
}

/**
 * Convierte una lista de puntos dibujados a mano en un perfil por tramos.
 * Une los segmentos que siguen derecho (sin pliegue) y descarta los de largo 0.
 * Un giro de 180° se carga como dobladillo.
 * @returns {{direccionInicial: string|number, tramos: Array}}
 */
export function puntosATramos(puntos) {
  // 1) Segmentos con largo y dirección.
  const segmentos = [];
  for (let i = 1; i < puntos.length; i++) {
    const dx = puntos[i].x - puntos[i - 1].x;
    const dy = puntos[i].y - puntos[i - 1].y;
    const largo = Math.hypot(dx, dy);
    if (largo < 0.0001) {
      continue;
    }
    const direccion = normalizarGrados((Math.atan2(dy, dx) * 180) / Math.PI);
    const anterior = segmentos[segmentos.length - 1];
    if (anterior && Math.abs(diferenciaDeAngulos(anterior.direccion, direccion)) < 0.0001) {
      anterior.largo += largo; // sigue derecho: es el mismo tramo
    } else {
      segmentos.push({ largo, direccion });
    }
  }

  if (segmentos.length === 0) {
    return { direccionInicial: 'arriba', tramos: [] };
  }

  // 2) Pasamos de direcciones absolutas a giros relativos.
  const tramos = segmentos.map((segmento, i) => {
    const tramo = {
      medidaCm: redondear(segmento.largo, 1),
      anguloPliegue: 90,
      sentido: 'izquierda',
      tipo: 'normal',
      observacion: '',
    };
    if (i > 0) {
      const giro = diferenciaDeAngulos(segmentos[i - 1].direccion, segmento.direccion);
      tramo.sentido = giro >= 0 ? 'izquierda' : 'derecha';
      const anguloInterior = redondear(180 - Math.abs(giro), 1);
      if (anguloInterior < 0.5) {
        tramo.tipo = 'dobladillo';
      } else {
        tramo.anguloPliegue = anguloInterior;
      }
    }
    return tramo;
  });

  return { direccionInicial: nombreDeDireccion(segmentos[0].direccion), tramos };
}

/** Diferencia entre dos direcciones, entre −180 y 180 (positivo = giro a la izquierda). */
export function diferenciaDeAngulos(desde, hasta) {
  let diferencia = normalizarGrados(hasta - desde);
  if (diferencia > 180) {
    diferencia -= 360;
  }
  return redondear(diferencia, 6);
}

// -------------------------------------------------------------
// Cara de afuera / cara de adentro (para la pintura)
// -------------------------------------------------------------

/**
 * Dice de qué lado del recorrido queda la cara EXTERIOR de la pieza
 * (el lado "convexo"), mirando en el sentido en que se cargan los tramos.
 * Se suman los giros: si en total el perfil dobla a la izquierda (como una U
 * dibujada en sentido antihorario), el interior queda a la izquierda y el
 * exterior a la derecha. Los dobladillos no cuentan.
 * @returns {'izquierda'|'derecha'}
 */
export function ladoExteriorDelPerfil(perfil, config) {
  const tramos = perfil.tramos || [];
  let sumaGiros = 0;
  for (let i = 1; i < tramos.length; i++) {
    const giro = giroEnTramo(tramos, i, config);
    if (!giro.esVuelta) {
      sumaGiros += (giro.sentido === 'derecha' ? -1 : 1) * giro.giroGrados;
    }
  }
  return sumaGiros > 0 ? 'derecha' : 'izquierda';
}

/**
 * Lado pintado según "pintura afuera", "pintura adentro" o "de los dos lados".
 * @param {'afuera'|'adentro'|'ambos'} ladoPintura
 * @returns {'izquierda'|'derecha'|'ambos'}
 */
export function ladoPintadoDelPerfil(perfil, ladoPintura, config) {
  if (ladoPintura === 'ambos') return 'ambos';
  const exterior = ladoExteriorDelPerfil(perfil, config);
  if (ladoPintura === 'adentro') {
    return exterior === 'izquierda' ? 'derecha' : 'izquierda';
  }
  return exterior;
}

/**
 * El "fondo" del perfil: el tramo más bajo de los que están más horizontales que verticales
 * (en una canaleta, la base). Ahí van las boquetas y, por defecto, los cortes.
 * @param {Array} segmentos  los de calcularGeometria()
 * @returns {{indice: number, punto: {x, y}}}  el tramo y su punto medio
 */
export function buscarFondo(segmentos) {
  let mejor = null;
  for (const s of segmentos || []) {
    const dx = Math.abs(s.fin.x - s.inicio.x);
    const dy = Math.abs(s.fin.y - s.inicio.y);
    if (dx < dy) continue; // no es horizontal
    const yMedio = (s.inicio.y + s.fin.y) / 2;
    if (!mejor || yMedio < mejor.punto.y - 1e-9) {
      mejor = { indice: s.indice, punto: { x: (s.inicio.x + s.fin.x) / 2, y: yMedio } };
    }
  }
  if (mejor) return mejor;
  const primero = segmentos?.[0];
  return primero
    ? { indice: 0, punto: { x: (primero.inicio.x + primero.fin.x) / 2, y: (primero.inicio.y + primero.fin.y) / 2 } }
    : { indice: 0, punto: { x: 0, y: 0 } };
}
