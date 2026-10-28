// =============================================================
// exportar.js
// Planillas para Excel sin librerías: CSV con punto y coma y coma decimal (lo que espera
// Excel configurado en español de Argentina) y con BOM UTF-8 para que respete las tildes.
// El PDF se saca con la impresión del navegador ("Guardar como PDF").
// =============================================================

/** Un valor de celda: números con coma decimal; texto entre comillas si hace falta. */
export function celdaCsv(valor) {
  if (valor === null || valor === undefined) return '';
  if (typeof valor === 'number') return Number.isFinite(valor) ? String(Math.round(valor * 100) / 100).replace('.', ',') : '';
  const texto = String(valor);
  return /[;"\n\r]/.test(texto) ? `"${texto.replace(/"/g, '""')}"` : texto;
}

/**
 * @param {string[]} columnas  encabezados
 * @param {Array<Array>} filas
 * @returns {string} CSV listo para bajar (con BOM)
 */
export function armarCsv(columnas, filas) {
  return `﻿${[columnas, ...filas].map((fila) => fila.map(celdaCsv).join(';')).join('\r\n')}\r\n`;
}

/**
 * Lee el CSV de la hoja PARAMETROS_API (Google Sheets → Descargar → CSV): columnas
 * Clave, Valor, Unidad, Origen. Acepta coma o punto y coma y coma o punto decimal.
 * @returns {{valores: object, errores: string[]}}
 */
export function leerCsvParametros(texto) {
  const lineas = String(texto).replace(/^﻿/, '').split(/\r?\n/).filter((l) => l.trim());
  const separador = (lineas.find((l) => /clave/i.test(l)) || lineas[0] || '').includes(';') ? ';' : ',';
  const valores = {};
  const errores = [];
  for (const linea of lineas) {
    const partes = dividir(linea, separador);
    const clave = (partes[0] || '').trim();
    if (!/^p_|^q_/.test(clave)) continue;
    const crudo = (partes[1] || '').trim();
    const numero = Number(crudo.replace(/\.(?=\d{3}(\D|$))/g, '').replace(',', '.'));
    if (crudo === '') errores.push(`${clave}: sin valor`);
    else valores[clave] = Number.isFinite(numero) ? numero : crudo;
  }
  if (!Object.keys(valores).length) errores.push('No se encontraron filas con claves p_… (¿es la hoja PARAMETROS_API?)');
  return { valores, errores };
}

function dividir(linea, separador) {
  const partes = [];
  let actual = '';
  let comillas = false;
  for (let i = 0; i < linea.length; i++) {
    const c = linea[i];
    if (c === '"') {
      if (comillas && linea[i + 1] === '"') { actual += '"'; i++; } else comillas = !comillas;
    } else if (c === separador && !comillas) { partes.push(actual); actual = ''; } else actual += c;
  }
  partes.push(actual);
  return partes;
}
