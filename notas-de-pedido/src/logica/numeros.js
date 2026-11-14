// =============================================================
// numeros.js
// Leer y escribir números "a la argentina": coma decimal ("2,5").
// Puro: no usa el navegador. Se prueba con node --test.
// =============================================================

/**
 * Convierte lo que escribió el vendedor en un número.
 * Acepta coma o punto decimal: "2,5" → 2.5, "2.5" → 2.5, " 60 " → 60.
 * Si no es un número válido devuelve NaN (Not a Number = "no es un número").
 */
export function leerNumero(texto) {
  if (typeof texto === 'number') {
    return Number.isFinite(texto) ? texto : NaN;
  }
  if (texto === null || texto === undefined) {
    return NaN;
  }
  let limpio = String(texto).trim().replace(/\s+/g, '');
  if (limpio === '') {
    return NaN;
  }
  // Una sola coma o un solo punto como separador decimal.
  limpio = limpio.replace(',', '.');
  const pareceNumero = /^-?(\d+\.?\d*|\.\d+)$/.test(limpio);
  if (!pareceNumero) {
    return NaN;
  }
  return Number(limpio);
}

/**
 * Redondea a una cantidad fija de decimales.
 * Sirve para evitar errores típicos de las computadoras: 0,1 + 0,2 = 0,30000000000000004.
 */
export function redondear(numero, decimales = 2) {
  const factor = 10 ** decimales;
  const resultado = Math.round(numero * factor) / factor;
  // Evitamos el "-0" que a veces aparece al redondear.
  return Object.is(resultado, -0) ? 0 : resultado;
}

/**
 * Escribe un número con coma decimal y una cantidad fija de decimales.
 * formatearNumero(2.44, 2) → "2,44"   formatearNumero(3, 2) → "3,00"
 */
export function formatearNumero(numero, decimales = 2) {
  return redondear(numero, decimales).toFixed(decimales).replace('.', ',');
}

/**
 * Escribe un número con coma decimal, sin ceros de más.
 * 60 → "60"   60.5 → "60,5"   32.42 → "32,42"
 */
export function formatearCorto(numero, decimalesMaximos = 2) {
  return String(redondear(numero, decimalesMaximos)).replace('.', ',');
}

/**
 * Lo que escribió el vendedor en un campo numérico: el número si lo es; si no, el texto tal cual
 * (así se ve lo que escribió y la validación lo marca), nunca NaN.
 */
export function numeroOTexto(texto) {
  const numero = leerNumero(texto);
  return Number.isFinite(numero) ? numero : String(texto ?? '').trim();
}

/** Valor para mostrar en un campo de cantidad: "2,5", el texto tal cual o vacío (nunca "NaN" ni "null"). */
export function textoDeCantidad(valor) {
  if (valor === null || valor === undefined) return '';
  if (typeof valor === 'number') return Number.isFinite(valor) ? String(valor).replace('.', ',') : '';
  return String(valor);
}

/** Fecha en formato dd/mm/aaaa. */
export function formatearFecha(fecha) {
  const dia = String(fecha.getDate()).padStart(2, '0');
  const mes = String(fecha.getMonth() + 1).padStart(2, '0');
  return `${dia}/${mes}/${fecha.getFullYear()}`;
}

/** Hora en formato hh:mm. */
export function formatearHora(fecha) {
  const horas = String(fecha.getHours()).padStart(2, '0');
  const minutos = String(fecha.getMinutes()).padStart(2, '0');
  return `${horas}:${minutos}`;
}
