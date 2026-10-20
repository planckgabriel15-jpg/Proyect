// =============================================================
// cotas.js
// Dónde van las cotas (medidas escritas) de un perfil plegado.
// Puro: no usa el navegador ni Three.js. Lo usan el 2D y el editor 3D.
//
// Para cada tramo devuelve los dos puntos medidos y la "normal" (hacia
// dónde se corre la línea de cota). Las cotas van del lado EXTERIOR de la
// pieza, como en un plano: así no quedan metidas adentro de la canaleta.
// Para cada pliegue devuelve el vértice, la bisectriz (hacia dónde se
// escribe el ángulo) y el arco que hay que dibujar.
// También dice dónde están las dos puntas libres del perfil (ahí el editor
// 3D pone el botón "+" para agregar un tramo).
// =============================================================

import { calcularGeometria, calcularLimites, ladoExteriorDelPerfil, diferenciaDeAngulos } from './geometria.js';
import { leerNumero, formatearCorto, redondear } from './numeros.js';

/** Texto de la cota de un tramo: "20", "1 dobl. aplast.", "7 · láser sinus.". */
export function textoCotaTramo(tramo) {
  const medida = leerNumero(tramo.medidaCm);
  let texto = Number.isFinite(medida) ? formatearCorto(medida) : '?';
  if (tramo.tipo === 'dobladillo') texto += ' dobl.';
  if (tramo.tipo === 'dobladillo_aplastado') texto += ' dobl. aplast.';
  if (tramo.tipo === 'pestana_engrafe') texto += ' engrafe';
  if (tramo.corteLaser) texto += ` · láser ${tramo.corteLaser.tipo === 'sinusoidal' ? 'sinus.' : 'trap.'}`;
  return texto;
}

/** Vector unitario de una dirección en grados (Y hacia arriba). */
function vector(grados) {
  const radianes = (grados * Math.PI) / 180;
  return { x: redondear(Math.cos(radianes), 9), y: redondear(Math.sin(radianes), 9) };
}

/**
 * @param {{direccionInicial, tramos}} perfil
 * @param {object} config  datos/config.json
 * @returns {{
 *   tamanoCm: number,        // lado mayor del perfil (sirve para escalar flechas y textos)
 *   separacionCm: number,    // cuánto se corre la línea de cota de la pieza
 *   ladoExterior: 'izquierda'|'derecha',
 *   medidas: Array<{indice, desde:{x,y}, hasta:{x,y}, direccion:{x,y}, normal:{x,y}, valor:number, texto:string}>,
 *   angulos: Array<{indice, vertice:{x,y}, bisectriz:{x,y}, desdeGrados:number, barridoGrados:number, valor:number, texto:string}>,
 *   extremos: Array<{extremo:'inicio'|'fin', punto:{x,y}, direccion:{x,y}}>
 * }}
 */
export function cotasDelPerfil(perfil, config) {
  const geometria = calcularGeometria(perfil, config);
  const limites = calcularLimites(geometria.puntos);
  const tamanoCm = Math.max(limites.ancho, limites.alto, 1);
  const separacionCm = redondear(Math.max(tamanoCm * 0.12, 1), 3);
  const ladoExterior = ladoExteriorDelPerfil(perfil, config);
  // Normal izquierda del recorrido = (−dy, dx). Si el exterior es la derecha, se da vuelta.
  const signo = ladoExterior === 'izquierda' ? 1 : -1;

  const medidas = geometria.segmentos.map((segmento) => {
    const direccion = vector(segmento.direccion);
    return {
      indice: segmento.indice,
      desde: { ...segmento.inicio },
      hasta: { ...segmento.fin },
      direccion,
      normal: { x: redondear(-direccion.y * signo, 9), y: redondear(direccion.x * signo, 9) },
      valor: leerNumero(segmento.tramo.medidaCm),
      texto: textoCotaTramo(segmento.tramo),
    };
  });

  // Los pliegues de 180° (dobladillos) no llevan ángulo: ya lo dice la cota del tramo.
  const angulos = geometria.pliegues
    .filter((pliegue) => !pliegue.esVuelta && pliegue.anguloInterior !== null)
    .map((pliegue) => {
      const desdeGrados = pliegue.direccionAntes + 180; // "hacia atrás", por el tramo anterior
      const barridoGrados = diferenciaDeAngulos(desdeGrados, pliegue.direccionDespues);
      const bisectriz = vector(desdeGrados + barridoGrados / 2);
      return {
        indice: pliegue.indice,
        vertice: { ...pliegue.punto },
        bisectriz,
        desdeGrados: redondear(desdeGrados, 6),
        barridoGrados,
        valor: pliegue.anguloInterior,
        texto: `${formatearCorto(pliegue.anguloInterior, 1)}°`,
      };
    });

  const extremos = [];
  if (medidas.length) {
    const primero = medidas[0];
    const ultimo = medidas[medidas.length - 1];
    extremos.push({ extremo: 'inicio', punto: { ...primero.desde }, direccion: { x: redondear(-primero.direccion.x, 9), y: redondear(-primero.direccion.y, 9) } });
    extremos.push({ extremo: 'fin', punto: { ...ultimo.hasta }, direccion: { ...ultimo.direccion } });
  }

  return { tamanoCm, separacionCm, ladoExterior, medidas, angulos, extremos };
}

/**
 * Lee lo que escribió el vendedor en una cota y dice si sirve.
 * @param {'medida'|'angulo'|'largo'|'numero'} tipo
 * @returns {{ok: true, valor: number} | {ok: false, mensaje: string}}
 */
export function leerValorDeCota(texto, tipo, config) {
  const valor = leerNumero(texto);
  if (!Number.isFinite(valor)) return { ok: false, mensaje: 'Escribí un número (con coma o punto)' };
  if (tipo === 'angulo') {
    if (valor < config.anguloMinimo || valor > config.anguloMaximo) {
      return { ok: false, mensaje: `El ángulo tiene que estar entre ${config.anguloMinimo}° y ${config.anguloMaximo}°` };
    }
    return { ok: true, valor };
  }
  if (tipo === 'posicion') {
    return valor >= 0 ? { ok: true, valor } : { ok: false, mensaje: 'La posición no puede ser negativa' };
  }
  if (valor <= 0) return { ok: false, mensaje: 'La medida tiene que ser mayor a 0' };
  return { ok: true, valor };
}
