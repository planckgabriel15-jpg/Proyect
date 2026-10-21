// =============================================================
// cortes.js
// Cortes (agujeros) en una cara de un plegado: redondos, cuadrados o
// rectangulares. Por ejemplo, el corte para una boqueta que el cliente ya
// tiene, o una chapa lisa con un agujero. Alrededor del corte puede ir una
// PARED (cuello o aletas) de cierta altura, hacia afuera o hacia adentro.
//
// Cada corte:
//   tramo        en qué cara va (número de tramo, empieza en 0)
//   forma        'redonda' | 'cuadrada' | 'rectangular'
//   diametroCm   (redonda)  · ladoACm = a lo ancho de la cara · ladoBCm = a lo largo de la pieza
//   posicionCm   centro, medido desde la punta izquierda de la pieza
//   centroCm     centro, medido desde donde empieza la cara (vacío = al medio)
//   paredAlturaCm / paredLado   pared alrededor del corte (0 = sin pared)
//
// Las boquetas puestas en el fondo de una canaleta también cortan la chapa:
// huecosEnCaras() junta los dos (lo usan el 3D y el 2D).
// El corte NO cambia el desarrollo ni el código (SUPUESTO, ver PENDIENTES.md).
// =============================================================

import { leerNumero, formatearCorto, redondear } from './numeros.js';
import { calcularGeometria, buscarFondo } from './geometria.js';
import { normalizarBoqueta, huellaDeBoqueta } from './accesoriosCanaleta.js';

export const FORMAS_CORTE = ['redonda', 'cuadrada', 'rectangular'];
export const LADOS_PARED = [
  { valor: 'afuera', texto: 'hacia afuera' },
  { valor: 'adentro', texto: 'hacia adentro' },
];

const f = (v) => formatearCorto(leerNumero(v));
const largoDe = (renglon) => (leerNumero(renglon.largoCm) > 0 ? leerNumero(renglon.largoCm) : 100);

/** Medida de cada cara (tramo) tal como se dibuja. */
function medidasDeCaras(renglon, config) {
  return calcularGeometria(renglon.perfil, config).segmentos.map((s) => redondear(Math.hypot(s.fin.x - s.inicio.x, s.fin.y - s.inicio.y), 6));
}

/** Corte nuevo: en el fondo de la pieza (o en su única cara), al medio del largo. */
export function crearCorte(renglon, config) {
  const fondo = buscarFondo(calcularGeometria(renglon.perfil, config).segmentos);
  return { ...config.cortes.porDefecto, tramo: fondo.indice, posicionCm: redondear(largoDe(renglon) / 2, 1), centroCm: null };
}

/** Lo que ocupa el corte: ancho = a lo ancho de la cara, alto = a lo largo de la pieza. */
export function huellaDeCorte(corte) {
  if (corte.forma === 'redonda') return { forma: 'circulo', diametro: leerNumero(corte.diametroCm) };
  const a = leerNumero(corte.ladoACm);
  return { forma: 'rect', ancho: a, alto: corte.forma === 'cuadrada' ? a : leerNumero(corte.ladoBCm) };
}

/** "Ø10", "10x10", "10x5". */
export function medidaDeCorte(corte) {
  if (corte.forma === 'redonda') return `Ø${f(corte.diametroCm)}`;
  if (corte.forma === 'cuadrada') return `${f(corte.ladoACm)}x${f(corte.ladoACm)}`;
  return `${f(corte.ladoACm)}x${f(corte.ladoBCm)}`;
}

/** Centro del corte a lo ancho de la cara (si está vacío, al medio). */
export function centroDelCorte(corte, medidaCara) {
  const centro = leerNumero(corte.centroCm);
  return corte.centroCm === null || corte.centroCm === undefined || corte.centroCm === '' || !Number.isFinite(centro) ? medidaCara / 2 : centro;
}

/**
 * Todos los agujeros de la chapa: los cortes y las boquetas puestas en el fondo.
 * @returns {Array<{tramo, centroU, centroZ, huella, medidaCara, origen: {tipo: 'corte'|'boqueta', indice}}>}
 *   centroU = a lo ancho de la cara (desde donde empieza) · centroZ = desde la punta izquierda
 */
export function huecosEnCaras(renglon, config) {
  if (renglon.tipoPieza !== 'plegada' || !renglon.perfil?.tramos?.length) return [];
  const medidas = medidasDeCaras(renglon, config);
  const largo = largoDe(renglon);
  const huecos = [];
  (renglon.cortes || []).forEach((corte, indice) => {
    const medidaCara = medidas[corte.tramo];
    if (medidaCara === undefined) return;
    huecos.push({
      tramo: corte.tramo, centroU: centroDelCorte(corte, medidaCara), centroZ: leerNumero(corte.posicionCm) || 0,
      huella: huellaDeCorte(corte), medidaCara, origen: { tipo: 'corte', indice },
    });
  });
  if (renglon.accesorios) {
    const fondo = buscarFondo(calcularGeometria(renglon.perfil, config).segmentos);
    (renglon.accesorios.boquetas || []).forEach((original, indice) => {
      const boqueta = normalizarBoqueta(original, config);
      if (boqueta.ubicacion !== 'fondo') return;
      huecos.push({
        tramo: fondo.indice, centroU: medidas[fondo.indice] / 2,
        centroZ: Math.min(Math.max(leerNumero(boqueta.posicionCm) || 0, 0), largo),
        huella: huellaDeBoqueta(boqueta), medidaCara: medidas[fondo.indice], origen: { tipo: 'boqueta', indice },
      });
    });
  }
  return huecos;
}

/**
 * Revisa los cortes: que la cara exista, que tengan medida y que entren en la cara
 * (dejando el margen mínimo de config.json → cortes.margenMinimoCm).
 */
export function validarCortes(renglon, config) {
  const problemas = [];
  if (renglon.tipoPieza !== 'plegada') return problemas;
  const medidas = medidasDeCaras(renglon, config);
  const largo = largoDe(renglon);
  const margen = config.cortes?.margenMinimoCm ?? 0.5;
  (renglon.cortes || []).forEach((corte, i) => {
    const n = i + 1;
    const medidaCara = medidas[corte.tramo];
    if (medidaCara === undefined) {
      problemas.push({ nivel: 'error', mensaje: `Corte ${n}: la cara elegida ya no existe (elegí otra)` });
      return;
    }
    if (!FORMAS_CORTE.includes(corte.forma)) {
      problemas.push({ nivel: 'error', mensaje: `Corte ${n}: elegí la forma` });
      return;
    }
    const huella = huellaDeCorte(corte);
    const ancho = huella.forma === 'circulo' ? huella.diametro : huella.ancho;
    const alto = huella.forma === 'circulo' ? huella.diametro : huella.alto;
    if (!(ancho > 0) || !(alto > 0)) {
      problemas.push({ nivel: 'error', mensaje: `Corte ${n}: falta la medida` });
      return;
    }
    const centro = centroDelCorte(corte, medidaCara);
    if (centro - ancho / 2 < margen - 1e-9 || centro + ancho / 2 > medidaCara - margen + 1e-9) {
      problemas.push({ nivel: 'error', mensaje: `Corte ${n}: no entra a lo ancho de la cara ${corte.tramo + 1} (mide ${formatearCorto(medidaCara)} cm; tiene que quedar ${formatearCorto(margen)} cm de chapa a cada lado)` });
    }
    const posicion = leerNumero(corte.posicionCm);
    if (!Number.isFinite(posicion) || posicion - alto / 2 < margen - 1e-9 || posicion + alto / 2 > largo - margen + 1e-9) {
      problemas.push({ nivel: 'error', mensaje: `Corte ${n}: no entra a lo largo (el centro tiene que estar entre ${formatearCorto(alto / 2 + margen)} y ${formatearCorto(largo - alto / 2 - margen)} cm)` });
    }
    const pared = leerNumero(corte.paredAlturaCm);
    if (corte.paredAlturaCm !== undefined && corte.paredAlturaCm !== '' && (!Number.isFinite(pared) || pared < 0)) {
      problemas.push({ nivel: 'error', mensaje: `Corte ${n}: la altura de la pared no puede ser negativa` });
    }
  });
  return problemas;
}

/** Para la descripción: "c/ corte Ø10" · "c/ 2 cortes (Ø10, 10x5 c/ pared 3 cm)". */
export function describirCortes(cortes) {
  if (!cortes?.length) return '';
  const textos = cortes.map((c) => `${medidaDeCorte(c)}${leerNumero(c.paredAlturaCm) > 0 ? ` c/ pared ${f(c.paredAlturaCm)} cm` : ''}`);
  return cortes.length === 1 ? `c/ corte ${textos[0]}` : `c/ ${cortes.length} cortes (${textos.join(', ')})`;
}

/** Detalle para producción: dónde va cada corte, acotado. */
export function detalleDeCortes(renglon, config) {
  if (!renglon.cortes?.length) return [];
  const medidas = medidasDeCaras(renglon, config);
  const nombres = { redonda: 'redondo', cuadrada: 'cuadrado', rectangular: 'rectangular' };
  return renglon.cortes.map((c, i) => {
    const medidaCara = medidas[c.tramo] ?? 0;
    let linea = `Corte ${i + 1}: ${nombres[c.forma] || c.forma} ${medidaDeCorte(c)} en la cara ${c.tramo + 1} (${formatearCorto(medidaCara)} cm), `
      + `centro a ${f(c.posicionCm)} cm de la punta izquierda y a ${formatearCorto(centroDelCorte(c, medidaCara))} cm del comienzo de la cara`;
    if (leerNumero(c.paredAlturaCm) > 0) linea += `; pared de ${f(c.paredAlturaCm)} cm ${c.paredLado === 'adentro' ? 'hacia adentro' : 'hacia afuera'}`;
    return linea;
  });
}
