// =============================================================
// codigoGenerico.js
// Código para los productos que NO están en la tabla de facturación
// (pedido de la empresa). Se arma así:
//   siglas del producto + medidas importantes + letra del color o material
//   Ej.: chapa lisa 10 x 10 negra → CL + 10 + 10 + N = CL1010N
//
// Primero SIEMPRE se busca en la tabla una fila para ese elemento exacto
// (cuando llegue la lista real, manda la tabla). Solo si no hay, se usa
// este código genérico, que queda marcado para que administración lo confirme.
// Las siglas y medidas de cada producto están en datos/catalogo.json
// ("codigoGenerico"); las letras de color y material en datos/materiales.json.
// =============================================================

import { leerNumero, redondear } from './numeros.js';
import { calcularDesarrollo } from './desarrollo.js';

/** 10 → "10"   7,5 → "75"   12,5 → "125"   (sin coma ni punto). */
export function medidaParaCodigo(numero) {
  return String(redondear(numero, 2)).replace('.', '');
}

/** Lee una medida del renglón según su "fuente". */
export function valorDeMedida(fuente, renglon) {
  if (fuente === 'tramo1') return leerNumero(renglon.perfil?.tramos?.[0]?.medidaCm);
  if (fuente === 'largoCm') return leerNumero(renglon.largoCm);
  if (fuente === 'desarrolloPerfil') return calcularDesarrollo(renglon.perfil?.tramos);
  return leerNumero(renglon.parametros?.[fuente]);
}

/**
 * @param {{siglas?, medidas?, siglasPorForma?, medidasPorForma?}} definicion
 * @param {object} renglon
 * @param {object} materiales  datos/materiales.json
 * @returns {string|null} el código, o null si falta alguna medida
 */
export function armarCodigoGenerico(definicion, renglon, materiales) {
  const forma = renglon.parametros?.forma;
  const siglas = definicion.siglasPorForma?.[forma] ?? definicion.siglas;
  const fuentes = definicion.medidasPorForma?.[forma] ?? definicion.medidas ?? [];
  if (!siglas) return null;

  const numeros = [];
  for (const fuente of fuentes) {
    const valor = valorDeMedida(fuente, renglon);
    const crudo = renglon.parametros?.[fuente];
    if (valor > 0) {
      numeros.push(medidaParaCodigo(valor));
    } else if (typeof crudo === 'string' && /\d/.test(crudo)) {
      numeros.push(crudo.replace(/\D/g, '')); // "15x30" → "1530"
    } else {
      return null;
    }
  }

  let letra = '';
  if (renglon.sinMaterial) {
    letra = ''; // artículos de catálogo: no llevan letra de color ni material
  } else if (renglon.terminacion === 'P') {
    letra = materiales.colores.find((c) => c.id === renglon.colorId)?.letraCodigoGenerico || '';
  } else {
    letra = materiales.materiales.find((m) => m.id === renglon.materialId)?.letraCodigoGenerico || '';
  }
  return `${siglas}${numeros.join('')}${letra}`;
}
