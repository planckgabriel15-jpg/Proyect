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
    } else if (medidaCm < (config.medidaMinimaTramoCm ?? 0)) {
      // Un tramo de 0,0001 cm no se puede plegar: casi seguro es un error de tipeo.
      problemas.push({ nivel: 'error', indice, mensaje: `Tramo ${numeroTramo}: la medida mínima es ${formatearCorto(config.medidaMinimaTramoCm)} cm` });
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
    return [{ nivel: 'error', campo: 'largoCm', mensaje: 'Falta el largo de la pieza' }];
  }
  // Fuera de lo razonable: casi seguro un error de tipeo (0,001 m, 99999 m).
  if (largo < (config.largoMinimoPiezaCm ?? 0)) {
    return [{ nivel: 'error', campo: 'largoCm', mensaje: `El largo es muy chico (mínimo ${formatearCorto(config.largoMinimoPiezaCm)} cm): revisalo` }];
  }
  if (config.largoMaximoPiezaCm && largo > config.largoMaximoPiezaCm) {
    return [{ nivel: 'error', campo: 'largoCm', mensaje: `El largo es muy grande (máximo ${formatearNumero(config.largoMaximoPiezaCm / 100, 2)} m por pieza): revisalo` }];
  }
  if (largo > config.largoMaximoChapaCm) {
    const texto = AVISO_EMPALME.replace('2,44', formatearNumero(config.largoMaximoChapaCm / 100, 2));
    return [{ nivel: 'aviso', campo: 'largoCm', mensaje: texto }];
  }
  return [];
}

/** Revisa material, calibre, terminación, color, lado de la pintura y cantidad. */
export function validarMaterialYCantidad(renglon, materiales, config) {
  const problemas = validarCantidadRazonable(renglon, config);
  const cantidadLeida = leerNumero(renglon.cantidad);
  if (renglon.sinMaterial) {
    // Artículo de catálogo, servicio o pieza con plano: solo importa la cantidad.
    if (renglon.cantidadDecimal) {
      // Servicios: se pueden vender 2,5 horas.
      if (!(cantidadLeida > 0)) problemas.push({ nivel: 'error', campo: 'cantidad', mensaje: 'La cantidad tiene que ser mayor a 0' });
    } else if (!Number.isInteger(cantidadLeida) || cantidadLeida < 1) {
      problemas.push({ nivel: 'error', campo: 'cantidad', mensaje: 'La cantidad tiene que ser un número entero mayor a 0' });
    }
    return problemas;
  }
  const material = materiales.materiales.find((m) => m.id === renglon.materialId);
  if (!material) {
    problemas.push({ nivel: 'error', campo: 'materialId', mensaje: 'Elegí el material' });
  } else if (!material.terminaciones.includes(renglon.terminacion)) {
    problemas.push({ nivel: 'error', campo: 'terminacion', mensaje: `La terminación elegida no existe para ${material.nombre}` });
  }

  if (!materiales.calibres.find((c) => c.id === renglon.calibreId)) {
    problemas.push({ nivel: 'error', campo: 'calibreId', mensaje: 'Elegí el calibre' });
  }

  if (renglon.terminacion === 'P') {
    if (!materiales.colores.find((c) => c.id === renglon.colorId)) {
      problemas.push({ nivel: 'error', campo: 'colorId', mensaje: 'Elegí el color de la chapa prepintada' });
    }
    if (config.ladoPinturaObligatorio && !['afuera', 'adentro', 'ambos'].includes(renglon.ladoPintura)) {
      problemas.push({ nivel: 'error', campo: 'ladoPintura', mensaje: 'Indicá de qué lado va la pintura (afuera, adentro o los dos lados)' });
    }
  }

  const cantidad = leerNumero(renglon.cantidad);
  if (!Number.isInteger(cantidad) || cantidad < 1) {
    problemas.push({ nivel: 'error', campo: 'cantidad', mensaje: 'La cantidad tiene que ser un número entero mayor a 0' });
  }
  return problemas;
}

/** Cantidades fuera de lo razonable (error de tipeo): muy grande frena, grande avisa. */
export function validarCantidadRazonable(renglon, config) {
  const cantidad = leerNumero(renglon.cantidad);
  if (!Number.isFinite(cantidad)) return [];
  if (config?.cantidadMaxima && cantidad > config.cantidadMaxima) {
    return [{ nivel: 'error', campo: 'cantidad', mensaje: `La cantidad es demasiado grande (máximo ${formatearCorto(config.cantidadMaxima)}): revisala` }];
  }
  if (config?.cantidadAvisoDesde && cantidad >= config.cantidadAvisoDesde) {
    return [{ nivel: 'aviso', campo: 'cantidad', mensaje: `Cantidad muy alta (${formatearCorto(cantidad)}): confirmá que no sobra un cero` }];
  }
  return [];
}

/**
 * Avisos de la nota entera que no frenan la emisión pero conviene mirar:
 * fecha de entrega ya pasada y número de factura usado en otra nota emitida.
 * @param {object} nota
 * @param {Array} otrasNotas  notas guardadas (para buscar la misma factura)
 * @param {string} hoy  'aaaa-mm-dd'
 * @returns {string[]}
 */
export function avisosDeNota(nota, otrasNotas = [], hoy = null) {
  const avisos = [];
  if (nota.fechaEntrega && hoy && nota.fechaEntrega < hoy) {
    const [a, m, d] = nota.fechaEntrega.split('-');
    avisos.push(`La fecha de entrega (${d}/${m}/${a}) ya pasó: ¿está bien?`);
  }
  const factura = String(nota.factura || '').replace(/\s+/g, '').toLowerCase();
  if (factura) {
    const misma = otrasNotas.find((n) => n.id !== nota.id && n.estado === 'emitida' && !n.demo
      && String(n.factura || '').replace(/\s+/g, '').toLowerCase() === factura);
    if (misma) avisos.push(`La factura ${nota.factura} ya está en la nota Nº ${misma.numero} (${misma.cliente || 'sin cliente'}): ¿es otra entrega de la misma venta?`);
  }
  return avisos;
}

/** Revisa el encabezado de la nota: sucursal, cliente y factura son obligatorios. */
export function validarEncabezado(nota) {
  const problemas = [];
  if (!nota.sucursalId) {
    problemas.push({ nivel: 'error', campo: 'sucursalId', mensaje: 'Falta la sucursal de origen' });
  }
  if (!String(nota.cliente || '').trim()) {
    problemas.push({ nivel: 'error', campo: 'cliente', mensaje: 'Falta el cliente' });
  }
  if (!String(nota.factura || '').trim()) {
    problemas.push({ nivel: 'error', campo: 'factura', mensaje: 'Falta el número de factura' });
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

/**
 * Lo que falta para poder emitir, con el LUGAR donde se corrige (para llevar al vendedor ahí,
 * en vez de mostrarle una lista suelta).
 * @returns {Array<{donde: 'encabezado'|'nota'|'renglon', campo: string|null, renglonId?: string, numero?: number, mensaje: string}>}
 */
export function faltantesDeNota(nota, resultadosRenglones) {
  const faltantes = validarEncabezado(nota).map((p) => ({ donde: 'encabezado', campo: p.campo, mensaje: p.mensaje }));
  if (!nota.renglones || nota.renglones.length === 0) {
    faltantes.push({ donde: 'nota', campo: null, mensaje: 'La nota no tiene renglones: agregá al menos una pieza' });
  }
  (resultadosRenglones || []).forEach((resultado, i) => {
    const errores = (resultado.problemas || resultado.errores.map((mensaje) => ({ nivel: 'error', mensaje, campo: null }))).filter((p) => p.nivel === 'error');
    for (const p of errores) {
      faltantes.push({ donde: 'renglon', campo: p.campo ?? null, renglonId: nota.renglones[i]?.id, numero: i + 1, mensaje: p.mensaje });
    }
  });
  return faltantes;
}

/** Mensaje corto para mostrar la medida de un tramo (lo usan las pantallas). */
export function textoMedida(medidaCm) {
  const medida = leerNumero(medidaCm);
  return Number.isFinite(medida) ? `${formatearCorto(medida)} cm` : '—';
}
