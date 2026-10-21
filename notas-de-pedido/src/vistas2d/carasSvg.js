// =============================================================
// carasSvg.js
// Vista de cada CARA que lleva agujeros (cortes o bocas de boquetas):
// la cara estirada, vista de frente, con cada agujero acotado desde la
// punta izquierda y desde el comienzo de la cara. A escala.
// También: la TAPA de la canaleta (a medida o con boqueta) dentro del perfil.
// Devuelve el SVG como texto (sirve en pantalla, impresión y pruebas).
// =============================================================

import { leerNumero, formatearCorto, formatearNumero } from '../logica/numeros.js';
import { calcularLimites } from '../logica/geometria.js';
import { huecosEnCaras, medidaDeCorte } from '../logica/cortes.js';
import { medidaDeBoqueta, normalizarBoqueta, ubicarTapa, centroDeBoquetaEnTapa, huellaDeBoqueta, tipoDeTapa, medidasDeTapa } from '../logica/accesoriosCanaleta.js';
import { escaparTexto } from './perfilSvg.js';

const r1 = (n) => Math.round(n * 10) / 10;

/** Una vista por cada cara con agujeros. '' si no hay agujeros. */
export function svgCaras(renglon, config, ancho = 640) {
  const huecos = huecosEnCaras(renglon, config);
  if (!huecos.length) return '';
  const caras = [...new Set(huecos.map((h) => h.tramo))].sort((a, b) => a - b);
  return caras.map((tramo) => svgDeUnaCara(renglon, tramo, huecos.filter((h) => h.tramo === tramo), ancho)).join('');
}

function svgDeUnaCara(renglon, tramo, huecos, ancho) {
  const largo = leerNumero(renglon.largoCm) > 0 ? leerNumero(renglon.largoCm) : 100;
  const medida = huecos[0].medidaCara;
  const margenX = 80;
  const arriba = 40;
  const filasCota = huecos.length;
  const escala = Math.min((ancho - 2 * margenX) / largo, 150 / Math.max(medida, 0.1));
  const altoCara = medida * escala;
  const alto = arriba + altoCara + 34 + filasCota * 20 + 16;
  const x = (z) => r1(margenX + z * escala);
  const y = (u) => r1(arriba + u * escala); // u = 0 arriba (comienzo de la cara)
  const partes = [`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${ancho} ${r1(alto)}" class="caras-svg" role="img" aria-label="Cara ${tramo + 1} con cortes">`];
  partes.push(`<text class="laser-titulo" x="8" y="18">Cara ${tramo + 1} (${formatearCorto(medida)} cm) vista de frente, con sus cortes — medidas en cm</text>`);
  partes.push(`<rect class="pieza" x="${x(0)}" y="${y(0)}" width="${r1(largo * escala)}" height="${r1(altoCara)}"/>`);
  partes.push(`<text class="nota" x="${x(0) - 6}" y="${y(0) + 10}" text-anchor="end">comienzo</text>`);
  partes.push(`<text class="nota" x="${x(largo)}" y="${arriba - 6}" text-anchor="end">largo ${formatearNumero(largo / 100, 2)} m</text>`);

  huecos.forEach((h, i) => {
    const cx = x(h.centroZ);
    const cy = y(h.centroU);
    let medioAncho;
    let medioAlto;
    if (h.huella.forma === 'circulo') {
      const r = Math.max((h.huella.diametro / 2) * escala, 2);
      medioAncho = r;
      medioAlto = r;
      partes.push(`<circle class="pieza-boqueta" cx="${cx}" cy="${cy}" r="${r1(r)}"/>`);
    } else {
      medioAncho = Math.max(h.huella.alto * escala, 3) / 2;
      medioAlto = Math.max(h.huella.ancho * escala, 3) / 2;
      partes.push(`<rect class="pieza-boqueta" x="${r1(cx - medioAncho)}" y="${r1(cy - medioAlto)}" width="${r1(medioAncho * 2)}" height="${r1(medioAlto * 2)}"/>`);
    }
    const nombre = h.origen.tipo === 'corte'
      ? `C${h.origen.indice + 1} ${medidaDeCorte(renglon.cortes[h.origen.indice])}`
      : `B${h.origen.indice + 1} ${medidaDeBoqueta(normalizarBoqueta(renglon.accesorios.boquetas[h.origen.indice]))}`;
    // Nombre arriba de la cara, sobre el agujero.
    partes.push(`<text class="cota-texto" x="${cx}" y="${arriba - 6}" text-anchor="middle">${escaparTexto(nombre)}</text>`);
    // Desde el comienzo de la cara hasta el centro: a la derecha del agujero.
    const xLado = r1(cx + medioAncho + 6);
    partes.push(`<line class="cota-guia" x1="${cx}" y1="${cy}" x2="${xLado + 4}" y2="${cy}"/>`);
    partes.push(`<line class="cota" x1="${xLado}" y1="${y(0)}" x2="${xLado}" y2="${cy}"/>`);
    partes.push(`<text class="cota-texto" x="${xLado + 4}" y="${r1((y(0) + cy) / 2 + 5)}">${formatearCorto(h.centroU)}</text>`);
    // Desde la punta izquierda hasta el centro: abajo.
    const yCota = r1(y(medida) + 26 + i * 20);
    partes.push(`<line class="cota" x1="${x(0)}" y1="${yCota}" x2="${cx}" y2="${yCota}"/>`);
    partes.push(`<line class="cota-guia" x1="${cx}" y1="${r1(cy + medioAlto)}" x2="${cx}" y2="${yCota + 4}"/>`);
    partes.push(`<text class="cota-texto" x="${r1((x(0) + cx) / 2)}" y="${yCota - 4}" text-anchor="middle">${formatearCorto(h.centroZ)}</text>`);
  });
  partes.push('</svg>');
  return partes.join('\n');
}

/**
 * La tapa de una punta dibujada dentro del perfil de la canaleta (gris), con las bocas de las
 * boquetas que lleva. Sirve para ver que la tapa a medida entra. '' si esa punta no tiene tapa.
 */
export function svgTapa(renglon, lado, config, ancho = 320, alto = 240) {
  if (!renglon.accesorios || tipoDeTapa(renglon.accesorios, lado) === 'ninguna' || !renglon.perfil?.tramos?.length) return '';
  const { poligonoCanaleta, poligonoTapa } = ubicarTapa(renglon, lado, config);
  const limites = calcularLimites(poligonoCanaleta.concat(poligonoTapa));
  const margen = 28;
  const escala = Math.min((ancho - 2 * margen) / Math.max(limites.ancho, 0.1), (alto - 2 * margen - 16) / Math.max(limites.alto, 0.1));
  const px = (p) => `${r1(margen + (p.x - limites.minX) * escala)},${r1(margen + 14 + (limites.maxY - p.y) * escala)}`;
  const enEsta = lado === 'izquierda' ? 'tapaIzquierda' : 'tapaDerecha';
  const aMedida = medidasDeTapa(renglon.accesorios, lado, config).aMedida;
  const partes = [`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${ancho} ${alto}" class="tapa-svg" role="img" aria-label="Tapa ${lado}">`];
  partes.push(`<text class="laser-titulo" x="8" y="16">Tapa ${lado}${aMedida ? ' a medida' : ''} (gris: la canaleta)</text>`);
  partes.push(`<polygon class="tapa-canaleta" points="${poligonoCanaleta.map(px).join(' ')}"/>`);
  partes.push(`<polygon class="tapa-chapa" points="${poligonoTapa.map(px).join(' ')}"/>`);
  (renglon.accesorios.boquetas || []).forEach((original, i) => {
    const b = normalizarBoqueta(original, config);
    if (b.ubicacion !== enEsta) return;
    const centro = centroDeBoquetaEnTapa(renglon, b, config);
    const huella = huellaDeBoqueta(b);
    const [cx, cy] = px(centro).split(',').map(Number);
    if (huella.forma === 'circulo') partes.push(`<circle class="pieza-boqueta" cx="${cx}" cy="${cy}" r="${r1((huella.diametro / 2) * escala)}"/>`);
    else partes.push(`<rect class="pieza-boqueta" x="${r1(cx - (huella.ancho / 2) * escala)}" y="${r1(cy - (huella.alto / 2) * escala)}" width="${r1(huella.ancho * escala)}" height="${r1(huella.alto * escala)}"/>`);
    partes.push(`<text class="cota-texto" x="${cx}" y="${r1(cy + 5)}" text-anchor="middle">B${i + 1}</text>`);
  });
  partes.push('</svg>');
  return partes.join('\n');
}

/** Las tapas que conviene dibujar aparte: las a medida y las que llevan una boqueta. */
export function svgTapasConDetalle(renglon, config) {
  if (!renglon.accesorios) return '';
  return ['izquierda', 'derecha'].map((lado) => {
    const enEsta = lado === 'izquierda' ? 'tapaIzquierda' : 'tapaDerecha';
    const conBoqueta = (renglon.accesorios.boquetas || []).some((b) => normalizarBoqueta(b, config).ubicacion === enEsta);
    return medidasDeTapa(renglon.accesorios, lado, config).aMedida || conBoqueta ? svgTapa(renglon, lado, config) : '';
  }).join('');
}
