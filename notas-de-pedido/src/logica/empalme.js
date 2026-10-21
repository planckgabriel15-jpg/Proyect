// =============================================================
// empalme.js
// Piezas más largas que la chapa (2,44 m): se arman con varios TRAMOS DE
// CHAPA empalmados a lo largo.
//   - Automático: tramos de 2,44 y lo que falta (3 m → 2,44 + 0,56).
//   - Partes iguales: 3 m → 1,50 + 1,50 (se puede pedir un tramo más o menos).
//   - A mano: el vendedor escribe cada tramo; el último se ajusta solo
//     para que la suma dé el largo.
// En el renglón: renglon.empalme = { modo: 'automatico'|'iguales'|'manual', cantidad?, tramosCm? }
// Sin solape entre tramos (SUPUESTO, config.json → empalme.solapeCm).
// Puro: se prueba con node --test.
// =============================================================

import { leerNumero, formatearNumero, redondear } from './numeros.js';

const largoDe = (renglon) => leerNumero(renglon.largoCm);

/** ¿La pieza necesita empalme? (tiene largo y es más larga que la chapa) */
export function necesitaEmpalme(renglon, config) {
  return renglon.usaLargo !== false && largoDe(renglon) > config.largoMaximoChapaCm + 1e-9;
}

/** Cantidad mínima de tramos de chapa para cubrir el largo. */
export function cantidadMinimaDeTramos(largoCm, maximoCm, solapeCm = 0) {
  if (!(largoCm > 0)) return 1;
  // n tramos de "maximo" cubren n·maximo − (n−1)·solape.
  return Math.max(1, Math.ceil((largoCm - solapeCm) / (maximoCm - solapeCm) - 1e-9));
}

/** 300 cm con chapa de 244 → [244, 56]. */
export function tramosAutomaticos(largoCm, maximoCm, solapeCm = 0) {
  const n = cantidadMinimaDeTramos(largoCm, maximoCm, solapeCm);
  const tramos = Array(n - 1).fill(maximoCm);
  const resto = largoCm - (n - 1) * maximoCm + (n - 1) * solapeCm;
  tramos.push(redondear(resto, 2));
  return tramos;
}

/** 300 cm en 2 → [150, 150]. Si no se dice cuántos, el mínimo que hace falta. */
export function tramosIguales(largoCm, maximoCm, cantidad = null, solapeCm = 0) {
  const minimo = cantidadMinimaDeTramos(largoCm, maximoCm, solapeCm);
  const n = Math.max(minimo, Math.round(cantidad || minimo));
  const cada = (largoCm + (n - 1) * solapeCm) / n;
  // Se redondea a mm y la diferencia va al último, así la suma da justa.
  const tramos = Array(n).fill(redondear(cada, 1));
  tramos[n - 1] = redondear(largoCm + (n - 1) * solapeCm - tramos[0] * (n - 1), 2);
  return tramos;
}

/**
 * Cambia un tramo a mano y ajusta otro para que la suma siga dando el largo
 * (el último; si se cambió el último, el anterior).
 */
export function ajustarTramoDeChapa(tramos, indice, valorCm, largoCm, solapeCm = 0) {
  const nuevos = [...tramos];
  nuevos[indice] = valorCm;
  if (nuevos.length > 1) {
    const compensa = indice === nuevos.length - 1 ? indice - 1 : nuevos.length - 1;
    const otros = nuevos.reduce((suma, t, i) => (i === compensa ? suma : suma + t), 0);
    nuevos[compensa] = redondear(largoCm + (nuevos.length - 1) * solapeCm - otros, 2);
  }
  return nuevos;
}

/** Los tramos de chapa del renglón (en cm), según el modo elegido. */
export function tramosDeChapa(renglon, config) {
  const largo = largoDe(renglon);
  const maximo = config.largoMaximoChapaCm;
  const solape = config.empalme?.solapeCm ?? 0;
  if (!(largo > 0)) return [];
  if (!necesitaEmpalme(renglon, config) && renglon.empalme?.modo !== 'manual' && renglon.empalme?.modo !== 'iguales') return [largo];
  const empalme = renglon.empalme || { modo: 'automatico' };
  if (empalme.modo === 'manual' && empalme.tramosCm?.length) return empalme.tramosCm.map((t) => leerNumero(t));
  if (empalme.modo === 'iguales') return tramosIguales(largo, maximo, empalme.cantidad, solape);
  return tramosAutomaticos(largo, maximo, solape);
}

/** Revisa los tramos: ninguno más largo que la chapa y que sumen el largo. */
export function validarEmpalme(renglon, config) {
  const problemas = [];
  const tramos = tramosDeChapa(renglon, config);
  if (tramos.length <= 1) return problemas;
  const maximo = config.largoMaximoChapaCm;
  const solape = config.empalme?.solapeCm ?? 0;
  const tolerancia = config.empalme?.toleranciaCm ?? 0.5;
  tramos.forEach((t, i) => {
    if (!(t > 0)) problemas.push({ nivel: 'error', mensaje: `Empalme: el tramo de chapa ${i + 1} tiene que medir más de 0` });
    else if (t > maximo + 1e-9) problemas.push({ nivel: 'error', mensaje: `Empalme: el tramo de chapa ${i + 1} mide ${formatearNumero(t / 100, 2)} m y la chapa mide ${formatearNumero(maximo / 100, 2)} m` });
  });
  const cubre = tramos.reduce((s, t) => s + t, 0) - (tramos.length - 1) * solape;
  if (Math.abs(cubre - largoDe(renglon)) > tolerancia) {
    problemas.push({ nivel: 'error', mensaje: `Empalme: los tramos suman ${formatearNumero(cubre / 100, 2)} m y la pieza mide ${formatearNumero(largoDe(renglon) / 100, 2)} m` });
  }
  return problemas;
}

/** "2 tramos de chapa: 2,44 + 0,56 m" ('' si va en un solo tramo). */
export function textoEmpalme(tramos) {
  if (!tramos || tramos.length <= 1) return '';
  return `${tramos.length} tramos de chapa: ${tramos.map((t) => formatearNumero(t / 100, 2)).join(' + ')} m`;
}

/** Dónde empieza cada tramo a lo largo de la pieza (para dibujar las uniones). */
export function posicionesDeUniones(tramos, solapeCm = 0) {
  const uniones = [];
  let z = 0;
  for (let i = 0; i < tramos.length - 1; i++) {
    z += tramos[i] - (i > 0 ? solapeCm : 0);
    uniones.push(redondear(z, 2));
  }
  return uniones;
}
