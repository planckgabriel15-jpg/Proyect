// =============================================================
// especialSvg.js
// Esquema 2D ACOTADO de las piezas especiales (boquetas, caños, codos,
// sombreros, embudos, reducciones, media caña). No es a escala exacta:
// es un dibujo claro con las medidas escritas, para que producción entienda.
// Las tapas usan el perfil de la canaleta (perfilSvg.js).
// =============================================================

import { leerNumero, formatearCorto } from '../logica/numeros.js';
import { escaparTexto } from './perfilSvg.js';

const f = (valor) => {
  const n = leerNumero(valor);
  return Number.isFinite(n) ? formatearCorto(n) : '?';
};

/** "caño Ø15" o "caño 20 × 10" según la forma (sombreros y boquetas). */
const medidaCano = (p) => (p.forma === 'rectangular'
  ? `${f(p.ladoACm)} × ${f(p.ladoBCm)}`
  : (p.forma === 'cuadrada' ? `${f(p.ladoACm)} × ${f(p.ladoACm)}` : `Ø ${f(p.diametroCm)}`));

/** Texto de cota simple. */
const texto = (x, y, contenido, ancla = 'middle', clase = 'cota-texto') =>
  `<text class="${clase}" x="${x}" y="${y}" text-anchor="${ancla}">${escaparTexto(contenido)}</text>`;

/** Cota horizontal con flechitas y texto arriba. */
function cotaH(x1, x2, y, contenido) {
  return `<line class="cota" x1="${x1}" y1="${y}" x2="${x2}" y2="${y}"/>
  <line class="cota" x1="${x1}" y1="${y - 5}" x2="${x1}" y2="${y + 5}"/>
  <line class="cota" x1="${x2}" y1="${y - 5}" x2="${x2}" y2="${y + 5}"/>
  ${texto((x1 + x2) / 2, y - 6, contenido)}`;
}

/** Cota vertical con texto a la izquierda. */
function cotaV(x, y1, y2, contenido) {
  return `<line class="cota" x1="${x}" y1="${y1}" x2="${x}" y2="${y2}"/>
  <line class="cota" x1="${x - 5}" y1="${y1}" x2="${x + 5}" y2="${y1}"/>
  <line class="cota" x1="${x - 5}" y1="${y2}" x2="${x + 5}" y2="${y2}"/>
  ${texto(x - 8, (y1 + y2) / 2 + 4, contenido, 'end')}`;
}

/** Cada generador devuelve el contenido del SVG (viewBox 0 0 640 420). */
const DIBUJOS = {
  canoRedondo: (p, r) => `
    <rect class="pieza" x="200" y="60" width="160" height="300" rx="4"/>
    <ellipse class="pieza" cx="280" cy="60" rx="80" ry="16"/>
    ${cotaH(200, 360, 40, `Ø ${f(p.diametroCm)}`)}
    ${cotaV(170, 60, 360, `largo ${f(r.largoCm / 100)} m`)}
    ${texto(400, 210, 'caño redondo, engrafado', 'start', 'nota')}`,

  canoRectangular: (p, r) => `
    <rect class="pieza" x="220" y="60" width="160" height="300"/>
    <polygon class="pieza" points="220,60 260,36 420,36 380,60"/>
    <polygon class="pieza" points="380,60 420,36 420,336 380,360"/>
    ${cotaH(220, 380, 380, `a = ${f(p.ladoACm)}`)}
    ${texto(430, 30, `b = ${f(p.ladoBCm)}`, 'start')}
    ${cotaV(190, 60, 360, `largo ${f(r.largoCm / 100)} m`)}`,

  boquetaRedonda: (p) => `
    <polygon class="pieza" points="140,90 500,90 470,120 170,120"/>
    <rect class="pieza" x="250" y="120" width="140" height="200"/>
    ${cotaH(250, 390, 350, `Ø ${f(p.diametroCm)}`)}
    ${cotaV(220, 120, 320, `boca ${f(p.largoBocaCm)}`)}
    ${cotaH(140, 250, 70, `pestaña ${f(p.pestanaCm)}`)}
    ${texto(320, 400, `posición: centro a ${f(p.posicionCm)} cm del extremo de la canaleta`, 'middle', 'nota')}`,

  boquetaRectangular: (p) => `
    <polygon class="pieza" points="140,90 500,90 470,120 170,120"/>
    <rect class="pieza" x="250" y="120" width="140" height="200"/>
    <polygon class="pieza" points="390,120 420,100 420,300 390,320"/>
    ${cotaH(250, 390, 350, `a = ${f(p.ladoACm)}`)}
    ${texto(430, 210, `b = ${f(p.ladoBCm)}`, 'start')}
    ${cotaV(220, 120, 320, `boca ${f(p.largoBocaCm)}`)}
    ${cotaH(140, 250, 70, `pestaña ${f(p.pestanaCm)}`)}
    ${texto(320, 400, `posición: centro a ${f(p.posicionCm)} cm del extremo de la canaleta`, 'middle', 'nota')}`,

  codoRedondo: (p) => {
    const angulo = leerNumero(p.anguloGrados) || 90;
    const gajos = Math.max(2, Math.round(leerNumero(p.gajos) || 4));
    // Arco formado por gajos (segmentos rectos).
    const cx = 160;
    const cy = 340;
    const radioMedio = 200;
    const media = 45;
    const puntos = (radio) => Array.from({ length: gajos + 1 }, (_, i) => {
      const a = (angulo * i / gajos) * Math.PI / 180;
      return `${Math.round(cx + radio * Math.sin(a))},${Math.round(cy - radio * Math.cos(a))}`;
    });
    const exterior = puntos(radioMedio + media);
    const interior = puntos(radioMedio - media).reverse();
    const uniones = Array.from({ length: gajos - 1 }, (_, i) => {
      const a = (angulo * (i + 1) / gajos) * Math.PI / 180;
      return `<line class="pieza-linea" x1="${Math.round(cx + (radioMedio - media) * Math.sin(a))}" y1="${Math.round(cy - (radioMedio - media) * Math.cos(a))}" x2="${Math.round(cx + (radioMedio + media) * Math.sin(a))}" y2="${Math.round(cy - (radioMedio + media) * Math.cos(a))}"/>`;
    }).join('');
    return `<polygon class="pieza" points="${[...exterior, ...interior].join(' ')}"/>${uniones}
      ${texto(150, 80, `Ø ${f(p.diametroCm)}`, 'start')}
      ${texto(420, 380, `ángulo ${f(angulo)}° · ${gajos} gajos`, 'middle')}`;
  },

  codoRectangular: (p) => `
    <polygon class="pieza" points="120,340 120,180 280,80 420,80 420,180 300,220 240,260 240,340"/>
    ${texto(330, 60, `${f(p.ladoACm)} × ${f(p.ladoBCm)}`, 'middle')}
    ${texto(330, 380, `ángulo ${f(p.anguloGrados)}°`, 'middle')}`,

  ramal: (p) => {
    const angulo = leerNumero(p.anguloGrados) || 45;
    const rad = angulo * Math.PI / 180;
    const x2 = Math.round(320 + 180 * Math.sin(rad));
    const y2 = Math.round(250 - 180 * Math.cos(rad));
    return `<rect class="pieza" x="270" y="40" width="100" height="340"/>
      <line class="pieza-ancha" x1="320" y1="250" x2="${x2}" y2="${y2}"/>
      ${texto(260, 30, `Ø ${f(p.diametroCm)}`, 'end')}
      ${texto(x2 + 10, y2, `ramal Ø ${f(p.diametroRamalCm)}`, 'start')}
      ${texto(470, 380, `ángulo ${f(angulo)}°`, 'middle')}`;
  },

  reduccion: (p) => `
    <polygon class="pieza" points="200,80 440,80 380,320 260,320"/>
    ${cotaH(200, 440, 60, `Ø ${f(p.diametroMayorCm)}`)}
    ${cotaH(260, 380, 350, `Ø ${f(p.diametroMenorCm)}`)}
    ${cotaV(170, 80, 320, `alto ${f(p.altoCm)}`)}`,

  embudo: (p) => `
    <polygon class="pieza" points="140,70 500,70 380,250 260,250"/>
    <rect class="pieza" x="260" y="250" width="120" height="110"/>
    ${cotaH(140, 500, 50, `boca ${f(p.bocaACm)} × ${f(p.bocaBCm)}`)}
    ${cotaV(110, 70, 250, `alto ${f(p.altoCm)}`)}
    ${cotaH(260, 380, 385, `salida Ø ${f(p.diametroSalidaCm)}`)}`,

  sombreroChino: (p) => `
    <polygon class="pieza" points="140,170 320,70 500,170"/>
    <line class="pieza-linea" x1="250" y1="170" x2="250" y2="230"/><line class="pieza-linea" x1="390" y1="170" x2="390" y2="230"/>
    <rect class="pieza" x="250" y="230" width="140" height="140"/>
    ${cotaH(250, 390, 395, `caño ${medidaCano(p)}`)}
    ${texto(320, 40, `sombrero chino ${p.forma || ''}`, 'middle', 'nota')}`,

  sombreroVenturi: (p) => `
    <polygon class="pieza" points="170,120 320,60 470,120"/>
    <rect class="pieza" x="190" y="125" width="260" height="90"/>
    <polygon class="pieza" points="190,215 450,215 390,250 250,250"/>
    <rect class="pieza" x="250" y="250" width="140" height="120"/>
    ${cotaH(250, 390, 395, `caño Ø ${f(p.diametroCm)}`)}
    ${texto(320, 40, 'sombrero venturi', 'middle', 'nota')}`,

  sombreroCanadiense: (p) => `
    <polygon class="pieza" points="160,170 320,70 480,170"/>
    <polygon class="pieza" points="160,180 480,180 320,250"/>
    <rect class="pieza" x="260" y="250" width="120" height="120"/>
    ${cotaH(260, 380, 395, `caño ${medidaCano(p)}`)}
    ${texto(320, 40, `sombrero canadiense / salamandra ${p.forma || ''}`, 'middle', 'nota')}`,

  sombreroH: (p) => `
    <rect class="pieza" x="120" y="90" width="400" height="80"/>
    <rect class="pieza" x="270" y="170" width="100" height="200"/>
    <line class="pieza-linea" x1="270" y1="130" x2="370" y2="130"/>
    ${cotaH(270, 370, 395, `caño ${medidaCano(p)}`)}
    ${texto(320, 60, `sombrero H ${p.forma || ''}`, 'middle', 'nota')}`,

  sombreroSpiro: (p) => `
    <polygon class="pieza" points="170,150 320,70 470,150"/>
    <polygon class="pieza" points="180,165 460,165 420,195 220,195"/>
    <polygon class="pieza" points="190,205 450,205 410,235 230,235"/>
    <rect class="pieza" x="260" y="240" width="120" height="130"/>
    ${cotaH(260, 380, 395, `caño ${medidaCano(p)}`)}
    ${texto(320, 40, `sombrero tipo Spiro ${p.forma || ''}`, 'middle', 'nota')}`,

  boquetaSuelta: (p) => `
    <polygon class="pieza" points="140,90 500,90 470,120 170,120"/>
    <rect class="pieza" x="250" y="120" width="140" height="200"/>
    ${p.forma !== 'redonda' ? '<polygon class="pieza" points="390,120 420,100 420,300 390,320"/>' : '<ellipse class="pieza" cx="320" cy="320" rx="70" ry="10"/>'}
    ${cotaH(250, 390, 360, `${p.forma || ''} ${medidaCano(p)}`)}
    ${cotaV(220, 120, 320, `boca ${f(p.largoBocaCm)}`)}
    ${cotaH(140, 250, 70, `pestaña ${f(p.pestanaCm)}`)}`,

  mediaCana: (p) => `
    <path class="pieza-ancha" fill="none" d="M 160 120 A 160 160 0 0 0 480 120"/>
    <line class="pieza-ancha" x1="160" y1="120" x2="160" y2="104"/>
    <line class="pieza-ancha" x1="480" y1="120" x2="520" y2="90"/>
    ${cotaH(160, 480, 80, `Ø ${f(p.diametroCm)}`)}
    ${texto(150, 104, `dobl. ${f(p.dobladilloCm)}`, 'end')}
    ${texto(525, 86, `pestaña ${f(p.pestanaCm)}`, 'start')}`,
};

/**
 * @param {object} renglon  renglón de una pieza especial (usa generador3d y parametros)
 * @returns {string} SVG
 */
export function svgDeEspecial(renglon, ancho = 640, alto = 420) {
  const dibujar = DIBUJOS[renglon.generador3d];
  const contenido = dibujar
    ? dibujar(renglon.parametros || {}, renglon)
    : texto(ancho / 2, alto / 2, 'Sin esquema para esta pieza');
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${ancho} ${alto}" class="especial-svg" role="img" aria-label="Esquema de la pieza">${contenido}</svg>`;
}

/** Miniatura para la galería: el mismo esquema, sin textos. */
export function svgMiniaturaEspecial(generador3d) {
  const svg = svgDeEspecial({ generador3d, parametros: {}, largoCm: 0 });
  return svg.replace('class="especial-svg"', 'class="especial-svg especial-mini"');
}
