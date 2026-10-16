// =============================================================
// perfilSvg.js
// Dibujo 2D ACOTADO del perfil (SVG = dibujo hecho con líneas que se
// imprime nítido a cualquier tamaño). Es la referencia oficial para fabricar.
//
// Devuelve el SVG como TEXTO, así se usa igual en pantalla, en la impresión
// y en las pruebas (no necesita el navegador).
//
// Muestra: la medida sobre cada tramo, el ángulo en cada pliegue si no es 90°,
// los dobladillos ("dobl." / "dobl. aplast."), el corte láser y una flecha en
// el lado pintado. Todo en negro: se entiende impreso en blanco y negro.
// =============================================================

import { calcularGeometria, calcularLimites, ladoPintadoDelPerfil } from '../logica/geometria.js';
import { leerNumero, formatearCorto } from '../logica/numeros.js';

/** Escapa texto para meterlo dentro del SVG sin romperlo. */
export function escaparTexto(texto) {
  return String(texto)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

const r1 = (n) => Math.round(n * 10) / 10; // redondeo para que el SVG no tenga 15 decimales

/**
 * @param {{direccionInicial, tramos}} perfil
 * @param {object} opciones
 *   config         datos/config.json (obligatorio)
 *   ancho, alto    tamaño del dibujo en píxeles (por defecto 640 × 420)
 *   resaltado      índice del tramo a resaltar (o null)
 *   ladoPintura    'afuera' | 'adentro' | null (null = no es prepintada)
 *   miniatura      true = sin cotas ni textos (para la galería)
 *   interactivo    true = cada tramo tiene data-tramo para hacer clic
 * @returns {string} el SVG
 */
export function svgDelPerfil(perfil, opciones) {
  const config = opciones.config;
  const ancho = opciones.ancho || 640;
  const alto = opciones.alto || 420;
  const miniatura = opciones.miniatura === true;
  const tramos = perfil?.tramos || [];

  if (tramos.length === 0) {
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${ancho} ${alto}" class="perfil-svg" role="img" aria-label="Perfil vacío">
      <text x="${ancho / 2}" y="${alto / 2}" text-anchor="middle" class="perfil-vacio">${miniatura ? '?' : 'Agregá tramos para ver el dibujo'}</text></svg>`;
  }

  const geometria = calcularGeometria(perfil, config);
  const limites = calcularLimites(geometria.puntos);

  // ---- Escala: el perfil entra en el dibujo dejando margen para las cotas ----
  const margen = miniatura ? 10 : 56;
  const anchoUtil = ancho - 2 * margen;
  const altoUtil = alto - 2 * margen - (miniatura ? 0 : 18); // 18 px abajo para la leyenda
  const escala = Math.min(
    anchoUtil / Math.max(limites.ancho, 0.001),
    altoUtil / Math.max(limites.alto, 0.001),
    miniatura ? 40 : 30, // tope: una pieza chica no se dibuja gigante
  );
  // Centramos el dibujo.
  const desplazamientoX = margen + (anchoUtil - limites.ancho * escala) / 2;
  const desplazamientoY = margen + (altoUtil - limites.alto * escala) / 2;
  // En SVG la Y crece hacia ABAJO; en nuestra geometría crece hacia ARRIBA: por eso se invierte.
  const aPantalla = (p) => ({
    x: r1(desplazamientoX + (p.x - limites.minX) * escala),
    y: r1(desplazamientoY + (limites.maxY - p.y) * escala),
  });

  const partes = [];
  partes.push(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${ancho} ${alto}" class="perfil-svg${miniatura ? ' perfil-mini' : ''}" role="img" aria-label="Dibujo del perfil">`);

  // ---- Línea completa (incluye la luz de los dobladillos) ----
  const puntosPantalla = geometria.puntos.map(aPantalla);
  partes.push(`<polyline class="perfil-linea" fill="none" points="${puntosPantalla.map((p) => `${p.x},${p.y}`).join(' ')}"/>`);

  // ---- Cada tramo por separado (para resaltarlo y hacer clic) ----
  geometria.segmentos.forEach((segmento) => {
    const a = aPantalla(segmento.inicio);
    const b = aPantalla(segmento.fin);
    const clases = ['perfil-tramo'];
    if (opciones.resaltado === segmento.indice) clases.push('resaltado');
    if (segmento.tramo.tipo === 'dobladillo' || segmento.tramo.tipo === 'dobladillo_aplastado') clases.push('dobladillo');
    if (segmento.tramo.corteLaser) clases.push('con-laser');
    partes.push(`<line class="${clases.join(' ')}" data-tramo="${segmento.indice}" x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}"/>`);
    // Línea ancha transparente encima: hace más fácil tocar el tramo con el dedo.
    if (opciones.interactivo) {
      partes.push(`<line class="perfil-toque" data-tramo="${segmento.indice}" x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}"/>`);
    }
  });

  // Punto de arranque (para saber dónde empieza el tramo 1).
  const inicio = puntosPantalla[0];
  partes.push(`<circle class="perfil-inicio" cx="${inicio.x}" cy="${inicio.y}" r="${miniatura ? 2.5 : 4}"/>`);

  if (!miniatura) {
    partes.push(...cotasDeTramos(geometria, aPantalla, opciones));
    partes.push(...cotasDeAngulos(geometria, aPantalla));
    const ladoPintado = opciones.ladoPintura ? ladoPintadoDelPerfil(perfil, opciones.ladoPintura, config) : null;
    if (ladoPintado) {
      partes.push(...flechaDePintura(geometria, aPantalla, ladoPintado));
    }
    // Leyenda abajo (texto: se lee en blanco y negro).
    const leyenda = [`Medidas EXTERIORES en cm`, `punto = inicio del tramo 1`];
    if (opciones.ladoPintura) leyenda.push(`Pintura ${opciones.ladoPintura.toUpperCase()}`);
    partes.push(`<text class="perfil-leyenda" x="8" y="${alto - 8}">${escaparTexto(leyenda.join('  ·  '))}</text>`);
  }

  partes.push('</svg>');
  return partes.join('\n');
}

/** Vector unitario de una dirección en grados (en pantalla, con la Y invertida). */
function vectorPantalla(grados) {
  const radianes = (grados * Math.PI) / 180;
  return { x: Math.cos(radianes), y: -Math.sin(radianes) };
}

/** Texto con la medida de cada tramo, al costado del tramo. */
function cotasDeTramos(geometria, aPantalla, opciones) {
  const partes = [];
  geometria.segmentos.forEach((segmento) => {
    const a = aPantalla(segmento.inicio);
    const b = aPantalla(segmento.fin);
    const medio = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
    const direccion = vectorPantalla(segmento.direccion);
    // Normal a la izquierda del recorrido (en pantalla).
    const normal = { x: direccion.y, y: -direccion.x };
    const separacion = 16;
    const x = r1(medio.x + normal.x * separacion);
    const y = r1(medio.y + normal.y * separacion + 5);

    const medida = leerNumero(segmento.tramo.medidaCm);
    let texto = Number.isFinite(medida) ? formatearCorto(medida) : '?';
    if (segmento.tramo.tipo === 'dobladillo') texto += ' dobl.';
    if (segmento.tramo.tipo === 'dobladillo_aplastado') texto += ' dobl. aplast.';
    if (segmento.tramo.tipo === 'pestana_engrafe') texto += ' engrafe';
    if (segmento.tramo.corteLaser) texto += ` · láser ${segmento.tramo.corteLaser.tipo === 'sinusoidal' ? 'sinus.' : 'trap.'}`;

    const clase = opciones.resaltado === segmento.indice ? 'perfil-cota resaltado' : 'perfil-cota';
    partes.push(`<text class="${clase}" data-tramo="${segmento.indice}" x="${x}" y="${y}" text-anchor="middle">${escaparTexto(texto)}</text>`);

    // Marca del corte láser: una línea ondulada paralela al tramo, del lado de afuera de la cota.
    if (segmento.tramo.corteLaser) {
      partes.push(lineaOndulada(a, b, normal, -7));
    }
  });
  return partes;
}

/** Línea ondulada chiquita paralela a un tramo (marca de corte láser). */
function lineaOndulada(a, b, normal, separacion) {
  const largo = Math.hypot(b.x - a.x, b.y - a.y);
  const ondas = Math.max(2, Math.round(largo / 10));
  const puntos = [];
  for (let i = 0; i <= ondas * 4; i++) {
    const t = i / (ondas * 4);
    const ola = Math.sin((t * ondas * 2 * Math.PI)) * 3;
    puntos.push(`${r1(a.x + (b.x - a.x) * t + normal.x * (separacion + ola))},${r1(a.y + (b.y - a.y) * t + normal.y * (separacion + ola))}`);
  }
  return `<polyline class="perfil-laser" fill="none" points="${puntos.join(' ')}"/>`;
}

/** Ángulo escrito en cada pliegue que NO es de 90° (y "180°" no se escribe: es dobladillo). */
function cotasDeAngulos(geometria, aPantalla) {
  const partes = [];
  for (const pliegue of geometria.pliegues) {
    if (pliegue.esVuelta || pliegue.anguloInterior === null || Math.abs(pliegue.anguloInterior - 90) < 0.01) {
      continue;
    }
    const vertice = aPantalla(pliegue.punto);
    // Bisectriz del ángulo interior: suma de "hacia atrás" y "hacia adelante".
    const atras = vectorPantalla(pliegue.direccionAntes + 180);
    const adelante = vectorPantalla(pliegue.direccionDespues);
    let bx = atras.x + adelante.x;
    let by = atras.y + adelante.y;
    const largo = Math.hypot(bx, by) || 1;
    bx /= largo;
    by /= largo;
    const x = r1(vertice.x + bx * 24);
    const y = r1(vertice.y + by * 24 + 4);
    partes.push(`<text class="perfil-angulo" x="${x}" y="${y}" text-anchor="middle">${formatearCorto(pliegue.anguloInterior, 1)}°</text>`);
  }
  return partes;
}

/** Flecha que apunta al lado pintado, sobre el tramo más largo. */
function flechaDePintura(geometria, aPantalla, ladoPintado) {
  const masLargo = [...geometria.segmentos].sort((s1, s2) => leerNumero(s2.tramo.medidaCm) - leerNumero(s1.tramo.medidaCm))[0];
  const a = aPantalla(masLargo.inicio);
  const b = aPantalla(masLargo.fin);
  const medio = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
  const direccion = vectorPantalla(masLargo.direccion);
  // Normal izquierda en pantalla (mismo cálculo que en las cotas).
  let normal = { x: direccion.y, y: -direccion.x };
  if (ladoPintado === 'derecha') normal = { x: -normal.x, y: -normal.y };
  // Corremos la flecha un poco a lo largo del tramo para que no tape la cota.
  const base = { x: medio.x + direccion.x * 22, y: medio.y + direccion.y * 22 };
  const punta = { x: r1(base.x + normal.x * 4), y: r1(base.y + normal.y * 4) };
  const cola = { x: r1(base.x + normal.x * 34), y: r1(base.y + normal.y * 34) };
  const texto = { x: r1(base.x + normal.x * 44), y: r1(base.y + normal.y * 44 + 4) };
  return [
    `<line class="perfil-pintura" x1="${cola.x}" y1="${cola.y}" x2="${punta.x}" y2="${punta.y}" marker-end="url(#punta-flecha)"/>`,
    `<defs><marker id="punta-flecha" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="perfil-punta"/></marker></defs>`,
    `<text class="perfil-pintura-texto" x="${texto.x}" y="${texto.y}" text-anchor="middle">pintura</text>`,
  ];
}
