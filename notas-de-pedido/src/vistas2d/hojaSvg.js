// =============================================================
// hojaSvg.js
// Los DIBUJOS de un renglón para la hoja impresa, armados en un solo lugar
// (los usan la pantalla de impresión y la prueba "ningún dato aparece dos veces").
// Son los mismos dibujos de siempre, sin los textos que la hoja ya dice en otra parte:
//  - el 2D del perfil no repite "Pintura AFUERA" (está en la ficha de material; la flecha queda);
//  - el largo de la pieza se escribe en UNA sola vista extra;
//  - el tamaño de la boqueta o del corte se escribe en la vista desde arriba y, en la cara de
//    frente, queda solo su nombre (B1, C1) con la cota de posición.
// =============================================================

import { svgDelPerfil } from './perfilSvg.js';
import { svgDeEspecial } from './especialSvg.js';
import { svgCorteLaser } from './corteLaserSvg.js';
import { svgPendienteLateral } from './pendienteSvg.js';
import { svgPlantaCanaleta } from './plantaCanaletaSvg.js';
import { svgCaras, svgTapasConDetalle } from './carasSvg.js';
import { perfilFinal } from '../logica/pendiente.js';

/**
 * @param {object} renglon
 * @param {'perfil'|'pendiente'|'especial'|null} tipoDibujo  lo que dice armarRenglonDeHoja
 * @param {object} datos
 * @param {object|null} pendiente  resultado.pendiente (solo si tipoDibujo es 'pendiente')
 * @returns {{principal: string, extras: string}} SVG (texto) del dibujo principal y de las vistas extra
 */
export function dibujosDeRenglon(renglon, tipoDibujo, datos, pendiente = null) {
  if (!tipoDibujo) return { principal: '', extras: '' };
  const { config } = datos;
  const usaPerfil = tipoDibujo !== 'especial';
  const opciones = {
    config, ancho: 560, alto: tipoDibujo === 'pendiente' ? 250 : 340,
    ladoPintura: renglon.terminacion === 'P' ? renglon.ladoPintura : null,
    sinLeyendaPintura: true,
  };
  let principal;
  if (tipoDibujo === 'pendiente') {
    principal = `<p class="titulo-perfil">Punta izquierda (inicio)</p>${svgDelPerfil(renglon.perfil, opciones)}`
      + `<p class="titulo-perfil">Punta derecha (final)</p>${svgDelPerfil(perfilFinal(renglon.perfil), opciones)}`;
  } else {
    principal = usaPerfil ? svgDelPerfil(renglon.perfil, opciones) : svgDeEspecial(renglon, 560, 360);
  }
  const lateral = tipoDibujo === 'pendiente' && pendiente ? svgPendienteLateral(renglon, pendiente, { config, ancho: 640, alto: 210 }) : '';
  const laseres = usaPerfil ? renglon.perfil.tramos.map((t, n) => (t.corteLaser ? svgCorteLaser(t, n + 1, renglon.largoCm, config, 560, 190) : '')).join('') : '';
  const planta = svgPlantaCanaleta(renglon, 640, 170 + 22 * (renglon.accesorios?.boquetas?.length || 0));
  // Si ya está la vista desde arriba (con el largo y el tamaño de cada boqueta), las caras no lo repiten.
  const caras = svgCaras(renglon, config, 640, { sinLargo: Boolean(planta), soloNombreDeBoquetas: Boolean(planta) });
  return { principal, extras: lateral + laseres + planta + caras + svgTapasConDetalle(renglon, config) };
}

/** Textos que se leen en un SVG (para las pruebas). */
export function textosDeSvg(svg) {
  return [...String(svg).matchAll(/<(?:text|tspan|p)[^>]*>([^<]+)</g)].map((m) => m[1].trim()).filter(Boolean);
}
