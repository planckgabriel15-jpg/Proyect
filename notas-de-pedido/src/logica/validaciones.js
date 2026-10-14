// =============================================================
// validaciones.js
// Revisa lo cargado y devuelve una lista de "problemas".
// Cada problema tiene un nivel:
//   'error' → BLOQUEA (no se puede emitir la nota)
//   'aviso' → NO bloquea, solo informa (ej. "requiere empalme")
// =============================================================

import { leerNumero, formatearNumero, formatearCorto } from './numeros.js';
import { giroEnTramo, TIPOS_DE_TRAMO } from './geometria.js';
import { validarCorteLaser } from './corteLaser.js';

export const AVISO_EMPALME = 'Supera el largo de la chapa (2,44 m): requiere empalme';

/** Revisa la lista de tramos de un perfil. */
export function validarTramos(tramos, config) {
  const problemas = [];
  if (!tramos || tramos.length === 0) {
    problemas.push({ nivel: 'error', indice: null, mensaje: 'Agregá al menos un tramo' });
    return problemas;
  }

  tramos.forEach((tramo, indice) => {
    const numeroTramo = indice + 1;

    const medidaCm = leerNumero(tramo.medidaCm);
    if (!Number.isFinite(medidaCm)) {
      problemas.push({ nivel: 'error', indice, mensaje: `Tramo ${numeroTramo}: falta la medida` });
    } else if (medidaCm <= 0) {
      problemas.push({ nivel: 'error', indice, mensaje: `Tramo ${numeroTramo}: la medida tiene que ser mayor a 0` });
    }

    if (!TIPOS_DE_TRAMO.includes(tramo.tipo)) {
      problemas.push({ nivel: 'error', indice, mensaje: `Tramo ${numeroTramo}: tipo de tramo desconocido` });
    }

    if (indice > 0) {
      if (tramo.sentido !== 'izquierda' && tramo.sentido !== 'derecha') {
        problemas.push({ nivel: 'error', indice, mensaje: `Tramo ${numeroTramo}: elegí el sentido (izquierda o derecha)` });
      }
      // El ángulo solo se revisa si el pliegue no es un dobladillo (que siempre es 180°).
      const giro = giroEnTramo(tramos, indice, config);
      if (!giro.esVuelta) {
        const angulo = leerNumero(tramo.anguloPliegue);
        if (!Number.isFinite(angulo) || angulo < config.anguloMinimo || angulo > config.anguloMaximo) {
          problemas.push({
            nivel: 'error',
            indice,
            mensaje: `Tramo ${numeroTramo}: el ángulo tiene que estar entre ${config.anguloMinimo}° y ${config.anguloMaximo}°`,
          });
        }
      }
    }

    problemas.push(...validarCorteLaser(tramo, indice, config));
  });

  return problemas;
}

/**
 * Revisa el largo de la pieza (en cm).
 * Más largo que la chapa → aviso de empalme (no bloquea). Configurable: largoMaximoChapaCm.
 */
export function validarLargo(largoCm, config) {
  const largo = leerNumero(largoCm);
  if (!Number.isFinite(largo) || largo <= 0) {
    return [{ nivel: 'error', mensaje: 'Falta el largo de la pieza' }];
  }
  if (largo > config.largoMaximoChapaCm) {
    const texto = AVISO_EMPALME.replace('2,44', formatearNumero(config.largoMaximoChapaCm / 100, 2));
    return [{ nivel: 'aviso', mensaje: texto }];
  }
  return [];
}

/** Revisa material, calibre, terminación, color, lado de la pintura y cantidad. */
export function validarMaterialYCantidad(renglon, materiales, config) {
  const problemas = [];
  const material = materiales.materiales.find((m) => m.id === renglon.materialId);
  if (!material) {
    problemas.push({ nivel: 'error', mensaje: 'Elegí el material' });
  } else if (!material.terminaciones.includes(renglon.terminacion)) {
    problemas.push({ nivel: 'error', mensaje: `La terminación elegida no existe para ${material.nombre}` });
  }

  if (!materiales.calibres.find((c) => c.id === renglon.calibreId)) {
    problemas.push({ nivel: 'error', mensaje: 'Elegí el calibre' });
  }

  if (renglon.terminacion === 'P') {
    if (!materiales.colores.find((c) => c.id === renglon.colorId)) {
      problemas.push({ nivel: 'error', mensaje: 'Elegí el color de la chapa prepintada' });
    }
    if (config.ladoPinturaObligatorio && !['afuera', 'adentro'].includes(renglon.ladoPintura)) {
      problemas.push({ nivel: 'error', mensaje: 'Indicá de qué lado va la pintura (afuera o adentro)' });
    }
  }

  const cantidad = leerNumero(renglon.cantidad);
  if (!Number.isInteger(cantidad) || cantidad < 1) {
    problemas.push({ nivel: 'error', mensaje: 'La cantidad tiene que ser un número entero mayor a 0' });
  }
  return problemas;
}

/** Revisa el encabezado de la nota: sucursal, cliente y factura son obligatorios. */
export function validarEncabezado(nota) {
  const problemas = [];
  if (!nota.sucursalId) {
    problemas.push({ nivel: 'error', mensaje: 'Falta la sucursal de origen' });
  }
  if (!String(nota.cliente || '').trim()) {
    problemas.push({ nivel: 'error', mensaje: 'Falta el cliente' });
  }
  if (!String(nota.factura || '').trim()) {
    problemas.push({ nivel: 'error', mensaje: 'Falta el número de factura' });
  }
  return problemas;
}

/**
 * Revisa la nota entera antes de emitir.
 * @param {object} nota
 * @param {Array<object>} resultadosRenglones  lo que devuelve calcularRenglon() para cada renglón
 * @returns {{puedeEmitir: boolean, errores: string[], avisos: string[]}}
 */
export function validarNota(nota, resultadosRenglones) {
  const errores = [];
  const avisos = [];

  for (const problema of validarEncabezado(nota)) {
    errores.push(problema.mensaje);
  }
  if (!nota.renglones || nota.renglones.length === 0) {
    errores.push('La nota no tiene renglones: agregá al menos una pieza');
  }

  (resultadosRenglones || []).forEach((resultado, i) => {
    const prefijo = `Renglón ${i + 1}: `;
    resultado.errores.forEach((mensaje) => errores.push(prefijo + mensaje));
    resultado.avisos.forEach((mensaje) => avisos.push(prefijo + mensaje));
  });

  return { puedeEmitir: errores.length === 0, errores, avisos };
}

/** Mensaje corto para mostrar la medida de un tramo (lo usan las pantallas). */
export function textoMedida(medidaCm) {
  const medida = leerNumero(medidaCm);
  return Number.isFinite(medida) ? `${formatearCorto(medida)} cm` : '—';
}
