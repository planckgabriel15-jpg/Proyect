// =============================================================
// corteLaser.js
// Corte láser en el borde de una cara (tramo): onda sinusoidal o trapezoidal,
// por ejemplo para que una cumbrera o una babeta copie la onda de la chapa del techo.
// La empresa NO hace el corte láser: se terceriza (se manda a hacer afuera y vuelve).
//
// Reglas pedidas por la empresa:
// - La cara con corte láser tiene que medir al menos 3,6 cm → si no, AVISO.
// - La altura de la onda tiene que ser de al menos 3,6 cm → si no, AVISO.
// Los dos valores están en datos/config.json (corteLaser).
//
// Cómo se mide la onda (vista de frente de la cara, a lo largo de la pieza):
//   altura de onda        = distancia entre la cresta y el fondo del valle
//   separación de valles  = distancia entre dos valles seguidos (el "paso")
// =============================================================

import { leerNumero, redondear, formatearCorto } from './numeros.js';

export const TIPOS_CORTE_LASER = ['sinusoidal', 'trapezoidal'];

/** Crea un corte láser con los valores por defecto del tipo elegido. */
export function crearCorteLaser(tipo, config) {
  const porDefecto = config.corteLaser.valoresPorDefecto[tipo];
  if (!porDefecto) {
    throw new Error(`Tipo de corte láser desconocido: ${tipo}`);
  }
  return {
    tipo,
    alturaOndaCm: porDefecto.alturaOndaCm,
    separacionVallesCm: porDefecto.separacionVallesCm,
  };
}

/**
 * Revisa el corte láser de un tramo.
 * @returns {Array<{nivel: 'error'|'aviso', mensaje: string, indice: number}>}
 */
export function validarCorteLaser(tramo, indice, config) {
  const problemas = [];
  const corte = tramo.corteLaser;
  if (!corte) {
    return problemas;
  }
  const numeroTramo = indice + 1;
  const reglas = config.corteLaser;

  if (!TIPOS_CORTE_LASER.includes(corte.tipo)) {
    problemas.push({ nivel: 'error', indice, mensaje: `Tramo ${numeroTramo}: elegí el tipo de corte láser (sinusoidal o trapezoidal)` });
    return problemas;
  }

  const anchoCaraCm = leerNumero(tramo.medidaCm);
  const alturaOndaCm = leerNumero(corte.alturaOndaCm);
  const separacionCm = leerNumero(corte.separacionVallesCm);

  if (Number.isFinite(anchoCaraCm) && anchoCaraCm < reglas.anchoMinimoCaraCm) {
    problemas.push({
      nivel: 'aviso',
      indice,
      mensaje: `Tramo ${numeroTramo}: la cara con corte láser mide ${formatearCorto(anchoCaraCm)} cm; el mínimo es ${formatearCorto(reglas.anchoMinimoCaraCm)} cm`,
    });
  }

  if (!Number.isFinite(alturaOndaCm) || alturaOndaCm <= 0) {
    problemas.push({ nivel: 'error', indice, mensaje: `Tramo ${numeroTramo}: falta la altura de la onda del corte láser` });
  } else if (alturaOndaCm < reglas.alturaMinimaOndaCm) {
    problemas.push({
      nivel: 'aviso',
      indice,
      mensaje: `Tramo ${numeroTramo}: la altura de onda es ${formatearCorto(alturaOndaCm)} cm; el mínimo es ${formatearCorto(reglas.alturaMinimaOndaCm)} cm`,
    });
  }

  if (Number.isFinite(alturaOndaCm) && Number.isFinite(anchoCaraCm) && alturaOndaCm >= anchoCaraCm) {
    problemas.push({
      nivel: 'aviso',
      indice,
      mensaje: `Tramo ${numeroTramo}: la onda (${formatearCorto(alturaOndaCm)} cm) es igual o más alta que la cara (${formatearCorto(anchoCaraCm)} cm): el corte se come toda la cara`,
    });
  }

  if (!Number.isFinite(separacionCm) || separacionCm <= 0) {
    problemas.push({ nivel: 'error', indice, mensaje: `Tramo ${numeroTramo}: falta la separación entre valles del corte láser` });
  }

  return problemas;
}

/**
 * Calcula el borde cortado, visto de frente, a lo largo de la pieza.
 * Devuelve puntos {a, h}:
 *   a = posición a lo largo de la pieza (de 0 a largoCm)
 *   h = cuánto entra el corte en la cara (0 = cresta, alturaOndaCm = fondo del valle)
 * Arranca y termina en cresta (h = 0) en a = 0.
 */
export function generarBordeOndulado(largoCm, corte, config, puntosPorOnda = 24) {
  const largo = leerNumero(largoCm);
  const altura = leerNumero(corte.alturaOndaCm);
  const paso = leerNumero(corte.separacionVallesCm);
  if (!(largo > 0) || !(altura > 0) || !(paso > 0)) {
    return [];
  }

  if (corte.tipo === 'sinusoidal') {
    const puntos = [];
    const cantidadOndas = largo / paso;
    const totalPuntos = Math.max(2, Math.ceil(cantidadOndas * puntosPorOnda));
    for (let i = 0; i <= totalPuntos; i++) {
      const a = (largo * i) / totalPuntos;
      // Coseno: en a = 0 vale cresta (h = 0); en a = paso/2 el fondo del valle (h = altura).
      const h = (altura / 2) * (1 - Math.cos((2 * Math.PI * a) / paso));
      puntos.push({ a: redondear(a, 4), h: redondear(h, 4) });
    }
    return puntos;
  }

  // Trapezoidal: en cada paso hay cresta plana, flanco que baja, valle plano y flanco que sube.
  // Las proporciones son SUPUESTO (config.corteLaser.proporcionesTrapecio).
  const p = config.corteLaser.proporcionesTrapecio;
  const tramosDelPaso = [
    { largo: p.cresta / 2, hFinal: 0 },
    { largo: p.flanco, hFinal: altura },
    { largo: p.valle, hFinal: altura },
    { largo: p.flanco, hFinal: 0 },
    { largo: p.cresta / 2, hFinal: 0 },
  ];
  const sumaProporciones = tramosDelPaso.reduce((suma, t) => suma + t.largo, 0);

  const puntos = [{ a: 0, h: 0 }];
  let a = 0;
  let h = 0;
  while (a < largo - 1e-9) {
    for (const t of tramosDelPaso) {
      const avance = (t.largo / sumaProporciones) * paso;
      if (avance <= 0) {
        continue;
      }
      const aFinal = a + avance;
      if (aFinal >= largo) {
        // Cortamos el último pedazo justo en el largo de la pieza.
        const fraccion = (largo - a) / avance;
        puntos.push({ a: redondear(largo, 4), h: redondear(h + (t.hFinal - h) * fraccion, 4) });
        return puntos;
      }
      a = aFinal;
      h = t.hFinal;
      puntos.push({ a: redondear(a, 4), h: redondear(h, 4) });
    }
  }
  return puntos;
}

/** Texto corto para la nota: "corte láser sinusoidal: onda 3,6 cm, valles cada 7,6 cm (tercerizado)". */
export function describirCorteLaser(corte) {
  return `corte láser ${corte.tipo}: onda ${formatearCorto(leerNumero(corte.alturaOndaCm))} cm, valles cada ${formatearCorto(leerNumero(corte.separacionVallesCm))} cm (tercerizado)`;
}
