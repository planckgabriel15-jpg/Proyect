// =============================================================
// accesoriosCanaleta.js
// Tapas y boquetas que van PUESTAS en la canaleta (en el mismo renglón):
// - tapa izquierda y tapa derecha: ninguna, soldada o engrampada;
// - boquetas: forma (redonda, cuadrada o rectangular), medida, largo de la
//   boca y posición (desde la punta izquierda de la canaleta hasta el centro).
// Las tapas y boquetas sueltas son productos aparte (ver catalogo.json).
// =============================================================

import { leerNumero, formatearCorto } from './numeros.js';

export const FORMAS_BOQUETA = ['redonda', 'cuadrada', 'rectangular'];

/** Accesorios de una canaleta nueva: sin tapas ni boquetas. */
export function accesoriosVacios() {
  return { tapaIzquierda: 'ninguna', tapaDerecha: 'ninguna', boquetas: [] };
}

/** Boqueta nueva con los valores por defecto de config.json. */
export function crearBoqueta(config) {
  return { ...config.accesoriosCanaleta.boquetaPorDefecto };
}

/** "Ø10", "10x10" o "10x5" según la forma. */
export function medidaDeBoqueta(boqueta) {
  const f = (v) => formatearCorto(leerNumero(v));
  if (boqueta.forma === 'redonda') return `Ø${f(boqueta.diametroCm)}`;
  if (boqueta.forma === 'cuadrada') return `${f(boqueta.ladoACm)}x${f(boqueta.ladoACm)}`;
  return `${f(boqueta.ladoACm)}x${f(boqueta.ladoBCm)}`;
}

/** Ancho que ocupa la boqueta a lo largo de la canaleta (para ver si entra). */
function anchoDeBoqueta(boqueta) {
  return boqueta.forma === 'redonda' ? leerNumero(boqueta.diametroCm) : leerNumero(boqueta.ladoACm);
}

/**
 * Revisa tapas y boquetas.
 * @returns {Array<{nivel:'error'|'aviso', mensaje}>}
 */
export function validarAccesorios(accesorios, largoCm, config) {
  const problemas = [];
  if (!accesorios) return problemas;
  const tipos = config.accesoriosCanaleta.tiposDeTapa;
  for (const [lado, valor] of [['izquierda', accesorios.tapaIzquierda], ['derecha', accesorios.tapaDerecha]]) {
    if (!tipos.includes(valor)) problemas.push({ nivel: 'error', mensaje: `Tapa ${lado}: elegí ninguna, soldada o engrampada` });
  }
  const largo = leerNumero(largoCm);
  (accesorios.boquetas || []).forEach((b, i) => {
    const n = i + 1;
    if (!FORMAS_BOQUETA.includes(b.forma)) {
      problemas.push({ nivel: 'error', mensaje: `Boqueta ${n}: elegí la forma` });
      return;
    }
    const medidas = b.forma === 'redonda' ? ['diametroCm'] : (b.forma === 'cuadrada' ? ['ladoACm'] : ['ladoACm', 'ladoBCm']);
    for (const campo of [...medidas, 'largoBocaCm']) {
      if (!(leerNumero(b[campo]) > 0)) problemas.push({ nivel: 'error', mensaje: `Boqueta ${n}: falta una medida` });
    }
    const posicion = leerNumero(b.posicionCm);
    if (!Number.isFinite(posicion) || posicion < 0 || (largo > 0 && posicion > largo)) {
      problemas.push({ nivel: 'error', mensaje: `Boqueta ${n}: la posición tiene que estar entre 0 y ${formatearCorto(largo || 0)} cm` });
    } else if (largo > 0 && (posicion - anchoDeBoqueta(b) / 2 < 0 || posicion + anchoDeBoqueta(b) / 2 > largo)) {
      problemas.push({ nivel: 'aviso', mensaje: `Boqueta ${n}: queda pegada a la punta de la canaleta (se sale del largo)` });
    }
  });
  return problemas;
}

/** Texto corto para la descripción: "c/ 2 tapas soldadas y 1 boqueta". */
export function describirAccesorios(accesorios) {
  if (!accesorios) return '';
  const partes = [];
  const izq = accesorios.tapaIzquierda;
  const der = accesorios.tapaDerecha;
  const hayIzq = izq && izq !== 'ninguna';
  const hayDer = der && der !== 'ninguna';
  if (hayIzq && hayDer && izq === der) partes.push(`2 tapas ${izq}s`);
  else {
    if (hayIzq) partes.push(`tapa izq. ${izq}`);
    if (hayDer) partes.push(`tapa der. ${der}`);
  }
  const cantidad = (accesorios.boquetas || []).length;
  if (cantidad) partes.push(`${cantidad} boqueta${cantidad > 1 ? 's' : ''}`);
  if (!partes.length) return '';
  // "a", "a y b", "a, b y c"
  const texto = partes.length > 1 ? `${partes.slice(0, -1).join(', ')} y ${partes[partes.length - 1]}` : partes[0];
  return `c/ ${texto}`;
}

/** Líneas de detalle para la nota impresa (lo que producción necesita saber). */
export function detalleDeAccesorios(accesorios) {
  if (!accesorios) return [];
  const lineas = [];
  if (accesorios.tapaIzquierda !== 'ninguna') lineas.push(`Tapa izquierda: ${accesorios.tapaIzquierda}`);
  if (accesorios.tapaDerecha !== 'ninguna') lineas.push(`Tapa derecha: ${accesorios.tapaDerecha}`);
  (accesorios.boquetas || []).forEach((b, i) => {
    lineas.push(`Boqueta ${i + 1}: ${b.forma} ${medidaDeBoqueta(b)}, boca ${formatearCorto(leerNumero(b.largoBocaCm))} cm, centro a ${formatearCorto(leerNumero(b.posicionCm))} cm de la punta izquierda`);
  });
  return lineas;
}
