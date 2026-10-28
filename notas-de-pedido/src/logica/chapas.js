// =============================================================
// chapas.js
// La columna "Cantidad" de la nota es la CANTIDAD DE CHAPAS (pedido de la empresa):
//
//   chapas = piezas × largo ÷ largo de la chapa estándar (2,44 m, config.largoMaximoChapaCm)
//
//   canaleta de 2,44 m × 1 → 1      canaleta de 1,22 m × 1 → 0,5
//   canaleta de 1,50 m × 2 → 1,23   canaleta de 3,00 m × 1 → 1,23 (2,44 + 0,56)
//
// La "chapa" de esta cuenta es la unidad del código: una tira de 2,44 m del ancho de
// la banda (30, 60 o 120 cm). Por eso NO depende del desarrollo: el desarrollo ya está
// en el código (CG05P60 = banda de media chapa).
//
// Además se calcula una ESTIMACIÓN FÍSICA (cuánta chapa sale del depósito si los
// recortes no se reutilizan). Se MUESTRA para comparar, pero NO cambia la cantidad de
// la nota. Ver explicarDiferencia().
// =============================================================

import { leerNumero, redondear, formatearCorto, formatearNumero } from './numeros.js';
import { tramosDeChapa } from './empalme.js';

/** ¿Este renglón se cuenta en chapas? (tiene largo y se cotiza por banda). Si no, en unidades. */
export function seCuentaEnChapas(renglon, resultado) {
  return renglon.usaLargo !== false
    && !renglon.sinMaterial
    && !resultado?.porUnidad
    && leerNumero(renglon.largoCm) > 0;
}

/** Cantidad de piezas del renglón (entero ≥ 0). Es el campo renglon.cantidad. */
export function piezasDe(renglon) {
  const piezas = leerNumero(renglon.cantidad);
  return Number.isFinite(piezas) && piezas > 0 ? piezas : 0;
}

/**
 * Lo que va en la columna "Cantidad" de la nota.
 * @returns {{unidad: 'chapas'|'unidades', valor: number, piezas: number, texto: string, regla: string}}
 */
export function cantidadDeLaNota(renglon, resultado, config) {
  const piezas = piezasDe(renglon);
  if (!seCuentaEnChapas(renglon, resultado)) {
    return { unidad: 'unidades', valor: piezas, piezas, texto: formatearCorto(piezas, 2), regla: 'por unidad (no tiene largo)' };
  }
  const decimales = config.cantidadDeChapas?.decimales ?? 2;
  const largoChapa = config.largoMaximoChapaCm;
  const valor = redondear((piezas * leerNumero(renglon.largoCm)) / largoChapa, decimales);
  return {
    unidad: 'chapas',
    valor,
    piezas,
    texto: formatearCorto(valor, decimales),
    regla: `${formatearCorto(piezas)} pieza(s) × ${formatearNumero(leerNumero(renglon.largoCm) / 100, 2)} m ÷ ${formatearNumero(largoChapa / 100, 2)} m`,
  };
}

/**
 * Reparte tiras de un largo fijo con el método "primero que entre, de mayor a menor"
 * (First Fit Decreasing, el clásico para cortar barras o tiras a medida).
 * @param {number[]} largos  largos a cortar (cm)
 * @param {number} largoTira  largo de la tira (cm)
 * @returns {number[]} lo que queda libre en cada tira usada
 */
export function repartirEnTiras(largos, largoTira) {
  const libres = [];
  for (const largo of [...largos].sort((a, b) => b - a)) {
    const lugar = libres.findIndex((libre) => libre >= largo - 1e-6);
    if (lugar >= 0) libres[lugar] = redondear(libres[lugar] - largo, 6);
    else libres.push(redondear(largoTira - largo, 6));
  }
  return libres;
}

/**
 * ESTIMACIÓN física de chapa (no se usa para facturar):
 * - a lo largo: los tramos de cada pieza se acomodan en tiras de 2,44 m (los recortes NO se reutilizan);
 * - a lo ancho: cuántas tiras del desarrollo salen de una chapa de 1,22 m (menos el despunte).
 * @returns {null | {tirasBanda: number, unidadesBanda: number, tirasPorChapaFisica: number,
 *   chapasEnteras: number, fraccionChapa: number, recorteCm: number, aprovechamiento: number}}
 */
export function consumoFisico(renglon, resultado, config) {
  if (!seCuentaEnChapas(renglon, resultado)) return null;
  const piezas = piezasDe(renglon);
  const desarrollo = leerNumero(resultado?.desarrolloCm);
  if (!(piezas > 0) || !(desarrollo > 0)) return null;
  const largoChapa = config.largoMaximoChapaCm;
  const anchoUtil = config.anchoChapaCm - (config.cantidadDeChapas?.margenEscuadreCm ?? 0);
  const tramos = renglon.tipoPieza === 'plegada' ? tramosDeChapa(renglon, config) : [leerNumero(renglon.largoCm)];
  const largos = [];
  for (let i = 0; i < piezas; i++) largos.push(...tramos.filter((t) => t > 0));
  const libres = repartirEnTiras(largos, largoChapa);
  const tirasBanda = libres.length;
  const tirasPorChapaFisica = Math.max(1, Math.floor(anchoUtil / desarrollo));
  const banda = resultado?.banda?.numero || null;
  const anchoTotal = config.bandas?.numeroChapaCompleta || 120;
  const usado = largos.reduce((suma, l) => suma + l, 0) * desarrollo;
  const chapasEnteras = Math.ceil(tirasBanda / tirasPorChapaFisica);
  return {
    tirasBanda,
    // Cada tira de 2,44 m de la banda es "1" en la unidad del código.
    unidadesBanda: tirasBanda,
    tirasPorChapaFisica,
    chapasEnteras,
    fraccionChapa: redondear(tirasBanda / tirasPorChapaFisica, 2),
    fraccionSegunBanda: banda ? redondear((tirasBanda * banda) / anchoTotal, 2) : null,
    recorteCm: redondear(libres.reduce((suma, l) => suma + l, 0), 1),
    aprovechamiento: redondear(usado / (chapasEnteras * largoChapa * config.anchoChapaCm), 3),
  };
}

/**
 * Compara la cantidad de la nota con la estimación física y lo explica en palabras.
 * @returns {null | {diferencia: number, texto: string}}
 */
export function explicarDiferencia(renglon, resultado, config) {
  const nota = cantidadDeLaNota(renglon, resultado, config);
  const fisico = consumoFisico(renglon, resultado, config);
  if (nota.unidad !== 'chapas' || !fisico) return null;
  const diferencia = redondear(fisico.unidadesBanda - nota.valor, 2);
  const partes = [`Regla de la nota: ${nota.regla} = ${nota.texto} chapa(s).`];
  if (Math.abs(diferencia) < 0.005) {
    partes.push('Coincide con lo que se corta: no sobran recortes.');
  } else {
    partes.push(`Si los recortes no se reutilizan se cortan ${fisico.tirasBanda} tira(s) enteras de 2,44 m (${formatearCorto(diferencia, 2)} más; sobran ${formatearCorto(fisico.recorteCm / 100, 2)} m de recorte).`);
  }
  partes.push(`A lo ancho entran ${fisico.tirasPorChapaFisica} tira(s) de ${formatearCorto(resultado.desarrolloCm, 1)} cm por chapa de ${formatearCorto(config.anchoChapaCm)} cm`
    + ` → ${formatearCorto(fisico.fraccionChapa, 2)} chapa(s) entera(s) de 1,22 × 2,44 (la banda supone ${formatearCorto(fisico.fraccionSegunBanda ?? 0, 2)}).`);
  return { diferencia, texto: partes.join(' ') };
}
