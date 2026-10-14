// =============================================================
// corteLaserSvg.js
// Vista DE FRENTE de una cara con corte láser: se ve la onda a lo largo de
// la pieza, con la altura de onda, la separación entre valles y el ancho de
// la cara acotados. Así el taller que hace el corte (tercerizado) sabe qué cortar.
// =============================================================

import { generarBordeOndulado } from '../logica/corteLaser.js';
import { leerNumero, formatearCorto } from '../logica/numeros.js';
import { escaparTexto } from './perfilSvg.js';

const r1 = (n) => Math.round(n * 10) / 10;

/**
 * @param {object} tramo        tramo con tramo.corteLaser
 * @param {number} numeroTramo  1, 2, 3… (para el título)
 * @param {number} largoCm      largo de la pieza
 * @param {object} config
 * @returns {string} SVG
 */
export function svgCorteLaser(tramo, numeroTramo, largoCm, config, ancho = 640, alto = 220) {
  const corte = tramo.corteLaser;
  const anchoCara = leerNumero(tramo.medidaCm);
  const altura = leerNumero(corte.alturaOndaCm);
  const paso = leerNumero(corte.separacionVallesCm);
  const largo = leerNumero(largoCm);
  if (!(anchoCara > 0) || !(altura > 0) || !(paso > 0)) {
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${ancho} 60" class="laser-svg"><text x="10" y="35">Completá las medidas del corte láser del tramo ${numeroTramo}</text></svg>`;
  }

  // Mostramos un pedazo representativo: hasta 4 ondas (o todo el largo si es más corto).
  const largoMostrado = Math.min(largo > 0 ? largo : paso * 4, paso * 4);
  const margenIzq = 60;
  const margenDer = 30;
  const margenArriba = 34;
  const margenAbajo = 40;
  const escala = Math.min((ancho - margenIzq - margenDer) / largoMostrado, (alto - margenArriba - margenAbajo) / anchoCara);
  const x0 = margenIzq;
  const y0 = margenArriba;
  const X = (a) => r1(x0 + a * escala);
  const Y = (h) => r1(y0 + h * escala);

  // Borde ondulado arriba (h = cuánto entra el corte en la cara) y borde recto abajo (el pliegue).
  const borde = generarBordeOndulado(largoMostrado, corte, config, 32);
  const contorno = [
    ...borde.map((p) => `${X(p.a)},${Y(p.h)}`),
    `${X(largoMostrado)},${Y(anchoCara)}`,
    `${X(0)},${Y(anchoCara)}`,
  ];

  const partes = [];
  partes.push(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${ancho} ${alto}" class="laser-svg" role="img" aria-label="Vista de la cara con corte láser">`);
  partes.push(`<text class="laser-titulo" x="8" y="18">Tramo ${numeroTramo} – corte láser ${escaparTexto(corte.tipo)} (tercerizado) – vista de frente${largo > largoMostrado ? ', se repite en todo el largo' : ''}</text>`);
  partes.push(`<polygon class="laser-cara" points="${contorno.join(' ')}"/>`);
  // Línea de pliegue (abajo).
  partes.push(`<line class="laser-pliegue" x1="${X(0)}" y1="${Y(anchoCara)}" x2="${X(largoMostrado)}" y2="${Y(anchoCara)}"/>`);
  partes.push(`<text class="laser-nota" x="${X(largoMostrado)}" y="${r1(Y(anchoCara) + 14)}" text-anchor="end">pliegue</text>`);

  // Cota: ancho de la cara (a la izquierda).
  partes.push(cotaVertical(X(0) - 26, Y(0), Y(anchoCara), `${formatearCorto(anchoCara)}`));
  // Cota: altura de onda (busca el primer valle).
  const primerValle = borde.find((p) => Math.abs(p.h - altura) < 0.001) || borde[Math.floor(borde.length / 4)];
  const xValle = X(primerValle.a);
  partes.push(cotaVertical(xValle, Y(0), Y(altura), `onda ${formatearCorto(altura)}`, true));
  // Cota: separación entre valles.
  const valles = borde.filter((p) => Math.abs(p.h - altura) < 0.001);
  const aPrimerValle = valles.length ? valles[0].a : paso / 2;
  if (aPrimerValle + paso <= largoMostrado + 0.001) {
    const yCota = r1(Y(anchoCara) + 26);
    partes.push(`<line class="cota" x1="${X(aPrimerValle)}" y1="${yCota}" x2="${X(aPrimerValle + paso)}" y2="${yCota}"/>`);
    partes.push(`<line class="cota-guia" x1="${X(aPrimerValle)}" y1="${Y(altura)}" x2="${X(aPrimerValle)}" y2="${yCota + 4}"/>`);
    partes.push(`<line class="cota-guia" x1="${X(aPrimerValle + paso)}" y1="${Y(altura)}" x2="${X(aPrimerValle + paso)}" y2="${yCota + 4}"/>`);
    partes.push(`<text class="cota-texto" x="${r1((X(aPrimerValle) + X(aPrimerValle + paso)) / 2)}" y="${yCota - 4}" text-anchor="middle">valles cada ${formatearCorto(paso)}</text>`);
  }
  partes.push('</svg>');
  return partes.join('\n');
}

function cotaVertical(x, y1, y2, texto, textoAlCostado = false) {
  const xTexto = textoAlCostado ? x + 6 : x - 4;
  const ancla = textoAlCostado ? 'start' : 'end';
  return [
    `<line class="cota" x1="${x}" y1="${y1}" x2="${x}" y2="${y2}"/>`,
    `<line class="cota" x1="${x - 4}" y1="${y1}" x2="${x + 4}" y2="${y1}"/>`,
    `<line class="cota" x1="${x - 4}" y1="${y2}" x2="${x + 4}" y2="${y2}"/>`,
    `<text class="cota-texto" x="${xTexto}" y="${r1((y1 + y2) / 2 + 4)}" text-anchor="${ancla}">${escaparTexto(texto)}</text>`,
  ].join('\n');
}
