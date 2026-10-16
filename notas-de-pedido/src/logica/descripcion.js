// =============================================================
// descripcion.js
// Arma la descripción del renglón como la escriben hoy en papel:
//   "2,44 mts canaleta pp negro D60 CH 25"
//    │        │        │        │   └ calibre
//    │        │        │        └ desarrollo en cm
//    │        │        └ terminación: "pp <color>" si es prepintada;
//    │        │          si no, la abreviatura del material ("galv") → SUPUESTO
//    │        └ texto de la plantilla (puede llevar medidas: "boqueta redonda Ø{diametroCm}")
//    └ largo en metros, con 2 decimales (solo piezas que tienen largo)
// =============================================================

import { leerNumero, formatearNumero, formatearCorto } from './numeros.js';
import { describirAccesorios } from './accesoriosCanaleta.js';

/**
 * Reemplaza {nombreParametro} en el texto por el valor cargado.
 * completarTexto("codo {anguloGrados}° Ø{diametroCm}", {anguloGrados: 90, diametroCm: 10}) → "codo 90° Ø10"
 */
export function completarTexto(texto, parametros = {}) {
  return String(texto || '').replace(/\{(\w+)\}/g, (coincidencia, nombre) => {
    if (nombre === 'medidas') return textoMedidasSegunForma(parametros);
    const valor = parametros[nombre];
    if (valor === undefined || valor === null || valor === '') {
      return '?';
    }
    const numero = leerNumero(valor);
    return Number.isFinite(numero) ? formatearCorto(numero) : String(valor);
  });
}

/** Medidas según la forma: "Ø10" (redonda o circular), "10x10" (cuadrada) o "20x10" (rectangular). */
export function textoMedidasSegunForma(parametros = {}) {
  const f = (v) => {
    const n = leerNumero(v);
    return Number.isFinite(n) ? formatearCorto(n) : '?';
  };
  if (parametros.forma === 'redonda' || parametros.forma === 'circular') return `Ø${f(parametros.diametroCm)}`;
  if (parametros.forma === 'cuadrada') return `${f(parametros.ladoACm)}x${f(parametros.ladoACm)}`;
  return `${f(parametros.ladoACm)}x${f(parametros.ladoBCm)}`;
}

/**
 * @param {object} renglon      el renglón de la nota
 * @param {object} materiales   datos/materiales.json
 * @param {{desarrolloCm: number|null, porUnidad: boolean}} resultado
 * @returns {string}
 */
export function armarDescripcion(renglon, materiales, resultado) {
  const partes = [];

  // 1) Largo en metros
  const largoCm = leerNumero(renglon.largoCm);
  if (renglon.usaLargo !== false && largoCm > 0) {
    partes.push(`${formatearNumero(largoCm / 100, 2)} mts`);
  }

  // 2) Nombre de la pieza (con sus medidas, si la plantilla las pide)
  partes.push(completarTexto(renglon.textoDescripcion, renglon.parametros));

  // 3) Corte láser (SUPUESTO: se agrega para que se vea que hay un trabajo tercerizado)
  const tiposDeCorte = [...new Set((renglon.perfil?.tramos || [])
    .filter((t) => t.corteLaser)
    .map((t) => t.corteLaser.tipo))];
  if (tiposDeCorte.length > 0) {
    partes.push(`c/ corte láser ${tiposDeCorte.join(' y ')}`);
  }

  // 4) Terminación (los artículos de catálogo no llevan material ni calibre)
  const material = materiales.materiales.find((m) => m.id === renglon.materialId);
  if (renglon.sinMaterial) {
    // nada
  } else if (renglon.terminacion === 'P') {
    const color = materiales.colores.find((c) => c.id === renglon.colorId);
    partes.push(`pp ${color ? color.nombre : '(sin color)'}${renglon.ladoPintura === 'ambos' ? ' 2 caras' : ''}`);
  } else if (material) {
    partes.push(material.abreviatura);
  }

  // 5) Desarrollo
  if (!resultado.porUnidad && resultado.desarrolloCm > 0) {
    partes.push(`D${formatearCorto(resultado.desarrolloCm, 1)}`);
  }

  // 6) Calibre
  const calibre = materiales.calibres.find((c) => c.id === renglon.calibreId);
  if (calibre && !renglon.sinMaterial) {
    partes.push(`CH ${calibre.numero}`);
  }

  // 7) Tapas y boquetas puestas en la canaleta (al final, para no cambiar el formato del papel)
  partes.push(describirAccesorios(renglon.accesorios));

  return partes.filter((parte) => parte !== '').join(' ');
}

/**
 * Texto de los tramos para la nota impresa, como se anota en papel:
 *   "1 (dobl. aplast.) + 20 + 32 + 7 = 60"
 */
export function textoDeTramos(tramos) {
  const nombres = { dobladillo: 'dobl.', dobladillo_aplastado: 'dobl. aplast.', pestana_engrafe: 'engrafe' };
  let suma = 0;
  const partes = (tramos || []).map((tramo) => {
    const medida = leerNumero(tramo.medidaCm);
    if (Number.isFinite(medida)) suma += medida;
    const marcas = [];
    if (nombres[tramo.tipo]) marcas.push(nombres[tramo.tipo]);
    if (tramo.corteLaser) marcas.push(`láser ${tramo.corteLaser.tipo}`);
    const texto = Number.isFinite(medida) ? formatearCorto(medida) : '?';
    return marcas.length ? `${texto} (${marcas.join(', ')})` : texto;
  });
  return partes.length ? `${partes.join(' + ')} = ${formatearCorto(Math.round(suma * 100) / 100)}` : '';
}
