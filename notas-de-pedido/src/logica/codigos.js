// =============================================================
// codigos.js
// Busca el código del producto en la tabla (datos/codigos.json).
// REGLA CONFIRMADA (5.4): el código NO se arma letra por letra.
// Siempre se BUSCA en la tabla, que viene del sistema de facturación.
// Columnas: elemento, material, espesor, terminacion, banda, codigo.
// elemento = "*" significa "sirve para cualquier pieza" (SUPUESTO).
// =============================================================

export const AVISO_CODIGO_NO_ENCONTRADO = 'Código no encontrado: avisar a administración';

/**
 * @param {Array<object>} tabla  filas de codigos.json
 * @param {{elemento: string, material: string, espesor: string, terminacion: string, banda: number|string|null}} criterio
 *        material = código de material (ej. "CG"), espesor = código de espesor (ej. "05")
 * @returns {{encontrado: boolean, codigo: string|null, aviso: string|null}}
 */
export function buscarCodigo(tabla, criterio) {
  if (criterio.banda === null || criterio.banda === undefined || criterio.banda === '') {
    return { encontrado: false, codigo: null, aviso: AVISO_CODIGO_NO_ENCONTRADO };
  }

  const coincideTodoMenosElemento = (fila) =>
    fila.material === criterio.material &&
    fila.espesor === criterio.espesor &&
    fila.terminacion === criterio.terminacion &&
    String(fila.banda) === String(criterio.banda);

  // 1) Primero buscamos una fila para ese elemento exacto (ej. "canaleta").
  let fila = (tabla || []).find((f) => f.elemento === criterio.elemento && coincideTodoMenosElemento(f));
  // 2) Si no hay, buscamos una fila genérica (elemento "*").
  if (!fila) {
    fila = (tabla || []).find((f) => f.elemento === '*' && coincideTodoMenosElemento(f));
  }

  if (!fila) {
    return { encontrado: false, codigo: null, aviso: AVISO_CODIGO_NO_ENCONTRADO };
  }
  return { encontrado: true, codigo: fila.codigo, aviso: null };
}

/**
 * Convierte un texto CSV (exportado del sistema de facturación) en filas de la tabla.
 * Primera línea = encabezados: elemento,material,espesor,terminacion,banda,codigo
 * Acepta coma o punto y coma como separador (Excel en español usa punto y coma).
 * @returns {{filas: Array<object>, errores: string[]}}
 */
export function convertirCsvEnTabla(textoCsv) {
  const columnas = ['elemento', 'material', 'espesor', 'terminacion', 'banda', 'codigo'];
  const lineas = String(textoCsv)
    .split(/\r?\n/)
    .map((linea) => linea.trim())
    .filter((linea) => linea !== '');

  if (lineas.length === 0) {
    return { filas: [], errores: ['El archivo está vacío'] };
  }

  const separador = lineas[0].includes(';') ? ';' : ',';
  const encabezados = lineas[0].split(separador).map((t) => t.trim().toLowerCase());
  const faltantes = columnas.filter((c) => !encabezados.includes(c));
  if (faltantes.length > 0) {
    return { filas: [], errores: [`Faltan columnas: ${faltantes.join(', ')}`] };
  }

  const filas = [];
  const errores = [];
  for (let numeroLinea = 1; numeroLinea < lineas.length; numeroLinea++) {
    const valores = lineas[numeroLinea].split(separador).map((t) => t.trim());
    const fila = {};
    for (const columna of columnas) {
      fila[columna] = valores[encabezados.indexOf(columna)] ?? '';
    }
    if (!fila.codigo) {
      errores.push(`Línea ${numeroLinea + 1}: falta el código`);
      continue;
    }
    if (!fila.elemento) {
      fila.elemento = '*';
    }
    filas.push(fila);
  }
  return { filas, errores };
}
