// =============================================================
// pendienteSvg.js
// Vista de costado de un plegado con pendiente: muestra cómo cambia el alto
// de la pieza de la punta izquierda (inicio) a la derecha (final).
// Las alturas se dibujan EXAGERADAS (si no, 5 cm en 2,44 m no se verían);
// lo dice la leyenda. Las medidas escritas son las reales.
// Devuelve el SVG como texto (sirve en pantalla, impresión y pruebas).
// =============================================================

import { calcularGeometria, calcularLimites } from '../logica/geometria.js';
import { perfilFinal } from '../logica/pendiente.js';
import { leerNumero, formatearCorto, formatearNumero } from '../logica/numeros.js';
import { escaparTexto } from './perfilSvg.js';

const r1 = (n) => Math.round(n * 10) / 10;

/**
 * @param {object} renglon   plegado con pendiente
 * @param {object} pendiente lo que devuelve calcularPendiente()
 * @param {{config, ancho?, alto?}} opciones
 */
export function svgPendienteLateral(renglon, pendiente, opciones) {
  const { config } = opciones;
  const ancho = opciones.ancho || 640;
  const alto = opciones.alto || 230;
  const inicio = calcularLimites(calcularGeometria(renglon.perfil, config).puntos);
  const final = calcularLimites(calcularGeometria(perfilFinal(renglon.perfil), config).puntos);
  const largoCm = leerNumero(renglon.largoCm) > 0 ? leerNumero(renglon.largoCm) : 100;

  // Escala: el largo ocupa el ancho; las alturas se estiran para ocupar el alto disponible.
  const margenX = 70;
  const margenArriba = 34;
  const margenAbajo = 58;
  const yMax = Math.max(inicio.maxY, final.maxY);
  const yMin = Math.min(inicio.minY, final.minY);
  const escalaX = (ancho - 2 * margenX) / largoCm;
  const escalaY = (alto - margenArriba - margenAbajo) / Math.max(yMax - yMin, 0.001);
  const x = (cm) => r1(margenX + cm * escalaX);
  const y = (cm) => r1(margenArriba + (yMax - cm) * escalaY);

  const izquierdaArriba = { x: x(0), y: y(inicio.maxY) };
  const izquierdaAbajo = { x: x(0), y: y(inicio.minY) };
  const derechaArriba = { x: x(largoCm), y: y(final.maxY) };
  const derechaAbajo = { x: x(largoCm), y: y(final.minY) };
  const altoInicio = inicio.maxY - inicio.minY;
  const altoFinal = final.maxY - final.minY;

  const partes = [`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${ancho} ${alto}" class="pendiente-svg" role="img" aria-label="Vista de costado: pendiente de la pieza">`];
  partes.push(`<text class="laser-titulo" x="8" y="18">Vista de costado (pendiente)</text>`);
  partes.push(`<polygon class="pieza" points="${[izquierdaArriba, derechaArriba, derechaAbajo, izquierdaAbajo].map((p) => `${p.x},${p.y}`).join(' ')}"/>`);
  // Línea de nivel: el fondo del inicio, para ver cuánto baja.
  partes.push(`<line class="cota-guia" x1="${izquierdaAbajo.x}" y1="${izquierdaAbajo.y}" x2="${derechaAbajo.x + 20}" y2="${izquierdaAbajo.y}"/>`);
  // Altos en las dos puntas.
  partes.push(`<line class="cota" x1="${izquierdaArriba.x - 18}" y1="${izquierdaArriba.y}" x2="${izquierdaAbajo.x - 18}" y2="${izquierdaAbajo.y}"/>`);
  partes.push(`<text class="cota-texto" x="${izquierdaArriba.x - 24}" y="${r1((izquierdaArriba.y + izquierdaAbajo.y) / 2 + 5)}" text-anchor="end">${formatearCorto(altoInicio, 1)}</text>`);
  partes.push(`<line class="cota" x1="${derechaArriba.x + 18}" y1="${derechaArriba.y}" x2="${derechaAbajo.x + 18}" y2="${derechaAbajo.y}"/>`);
  partes.push(`<text class="cota-texto" x="${derechaArriba.x + 24}" y="${r1((derechaArriba.y + derechaAbajo.y) / 2 + 5)}">${formatearCorto(altoFinal, 1)}</text>`);
  // Largo.
  const yLargo = alto - margenAbajo + 22;
  partes.push(`<line class="cota" x1="${x(0)}" y1="${yLargo}" x2="${x(largoCm)}" y2="${yLargo}"/>`);
  partes.push(`<text class="cota-texto" x="${r1((x(0) + x(largoCm)) / 2)}" y="${yLargo - 6}" text-anchor="middle">${formatearNumero(largoCm / 100, 2)} m</text>`);
  // Puntas.
  partes.push(`<text class="nota" x="${x(0)}" y="${alto - 6}" text-anchor="start">inicio (punta izq.) D${formatearCorto(pendiente.desarrolloInicialCm, 1)}</text>`);
  partes.push(`<text class="nota" x="${x(largoCm)}" y="${alto - 6}" text-anchor="end">final (punta der.) D${formatearCorto(pendiente.desarrolloFinalCm, 1)}</text>`);
  partes.push(`<text class="cota-texto" x="${ancho - 8}" y="18" text-anchor="end">${escaparTexto(`Pendiente: ${pendiente.texto}`)}</text>`);
  partes.push(`<text class="perfil-leyenda" x="8" y="${alto - 22}">alturas exageradas para que se vea la pendiente</text>`);
  partes.push('</svg>');
  return partes.join('\n');
}
