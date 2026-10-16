// =============================================================
// piezasEspeciales.js
// Desarrollo de las piezas que NO se arman por tramos (boquetas, caños,
// codos, sombreros, embudos, reducciones, tapas, canaleta media caña).
// Todas las fórmulas son SUPUESTO (sección 7.2): el vendedor puede corregir
// el desarrollo a mano y queda registrado que fue manual.
// =============================================================

import { leerNumero, redondear } from './numeros.js';

/**
 * Tipos de cálculo que puede tener una plantilla especial (campo "calculoDesarrollo"):
 *   perimetroRedondo      → π·Ø + solape de engrafe
 *   perimetroRectangular  → 2·(a + b) + solape de engrafe
 *   perimetroSegunForma   → según el parámetro "forma": redonda (π·Ø), cuadrada (4·a) o rectangular (2·(a+b)), + solape
 *   mediaCana             → π·Ø/2 + dobladillo + pestaña trasera
 *   unidad                → se cotiza por unidad (sin desarrollo)
 */
export const TIPOS_DE_CALCULO = ['perimetroRedondo', 'perimetroRectangular', 'perimetroSegunForma', 'mediaCana', 'unidad'];

/**
 * @param {string} tipoCalculo
 * @param {object} parametros  valores cargados por el vendedor (ej. {diametroCm: 10})
 * @param {object} config      datos/config.json
 * @returns {{desarrolloCm: number|null, porUnidad: boolean, formula: string}}
 */
export function calcularDesarrolloEspecial(tipoCalculo, parametros, config) {
  const solapeCm = config.solapeEngrafeCm;
  const p = (nombre) => leerNumero(parametros?.[nombre]);

  switch (tipoCalculo) {
    case 'perimetroRedondo': {
      const diametroCm = p('diametroCm');
      if (!(diametroCm > 0)) return sinDato('π·Ø + solape');
      return { desarrolloCm: redondear(Math.PI * diametroCm + solapeCm, 1), porUnidad: false, formula: `π × ${diametroCm} + ${solapeCm} (solape)` };
    }
    case 'perimetroRectangular': {
      const a = p('ladoACm');
      const b = p('ladoBCm');
      if (!(a > 0) || !(b > 0)) return sinDato('2·(a+b) + solape');
      return { desarrolloCm: redondear(2 * (a + b) + solapeCm, 1), porUnidad: false, formula: `2 × (${a} + ${b}) + ${solapeCm} (solape)` };
    }
    case 'perimetroSegunForma': {
      const forma = parametros?.forma;
      if (forma === 'redonda' || forma === 'circular') return calcularDesarrolloEspecial('perimetroRedondo', parametros, config);
      if (forma === 'cuadrada') {
        const a = p('ladoACm');
        if (!(a > 0)) return sinDato('4·a + solape');
        return { desarrolloCm: redondear(4 * a + solapeCm, 1), porUnidad: false, formula: `4 × ${a} + ${solapeCm} (solape)` };
      }
      return calcularDesarrolloEspecial('perimetroRectangular', parametros, config);
    }
    case 'mediaCana': {
      const diametroCm = p('diametroCm');
      const dobladilloCm = p('dobladilloCm') || 0;
      const pestanaCm = p('pestanaCm') || 0;
      if (!(diametroCm > 0)) return sinDato('π·Ø/2 + dobladillo + pestaña');
      return {
        desarrolloCm: redondear((Math.PI * diametroCm) / 2 + dobladilloCm + pestanaCm, 1),
        porUnidad: false,
        formula: `π × ${diametroCm} / 2 + ${dobladilloCm} + ${pestanaCm}`,
      };
    }
    case 'unidad':
      return { desarrolloCm: null, porUnidad: true, formula: 'se cotiza por unidad' };
    default:
      throw new Error(`Tipo de cálculo desconocido: ${tipoCalculo}`);
  }
}

function sinDato(formula) {
  return { desarrolloCm: null, porUnidad: false, formula };
}

/**
 * Revisa los parámetros de una pieza especial contra su plantilla.
 * Cada parámetro numérico tiene que ser un número mayor o igual al mínimo.
 * @returns {Array<{nivel:'error', mensaje:string}>}
 */
export function validarParametros(plantilla, parametros) {
  const problemas = [];
  for (const definicion of parametrosVisibles(plantilla, parametros)) {
    const valor = parametros?.[definicion.id];
    if (definicion.tipo === 'numero' || definicion.tipo === 'diametro') {
      const numero = leerNumero(valor);
      const minimo = definicion.minimo ?? 0;
      if (!Number.isFinite(numero)) {
        problemas.push({ nivel: 'error', mensaje: `Falta "${definicion.etiqueta}"` });
      } else if (numero < minimo || (minimo === 0 && numero <= 0)) {
        problemas.push({ nivel: 'error', mensaje: `"${definicion.etiqueta}" tiene que ser mayor a ${minimo}` });
      }
    } else if (definicion.tipo === 'opciones') {
      const valores = (definicion.opciones || []).map((o) => String(o.valor));
      if (!valores.includes(String(valor))) {
        problemas.push({ nivel: 'error', mensaje: `Elegí "${definicion.etiqueta}"` });
      }
    }
  }
  return problemas;
}

/**
 * Parámetros que corresponden a la forma elegida (por ejemplo, una boqueta
 * redonda pide diámetro y una rectangular pide lado a y lado b).
 */
export function parametrosVisibles(plantilla, parametros) {
  return (plantilla.parametros || []).filter((d) => !d.soloSiForma || d.soloSiForma.includes(parametros?.forma));
}
