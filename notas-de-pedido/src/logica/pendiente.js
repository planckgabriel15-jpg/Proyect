// =============================================================
// pendiente.js
// Plegados "con pendiente": la pieza cambia de perfil a lo largo.
// Ejemplo: una canaleta que arranca con 20 cm de alto en la punta izquierda
// y termina con 25 cm en la derecha (más honda hacia la bajada).
//
// Cómo se carga (igual que en los programas de CAD con "chapa entre dos
// perfiles", ver PENDIENTES.md): los dos perfiles tienen los MISMOS tramos,
// en el mismo orden, con el mismo tipo y sentido. Lo único que cambia es la
// medida y el ángulo de cada tramo en la punta final. En cada tramo:
//   medidaCm / anguloPliegue            → punta izquierda (inicio, Z = 0)
//   medidaFinalCm / anguloPliegueFinal  → punta derecha (final, Z = largo)
// Si un tramo no tiene valor final, es igual en las dos puntas.
//
// Las dos puntas se dibujan desde el mismo punto de arranque (el comienzo del
// tramo 1): así, en una canaleta, el borde de arriba queda a nivel y el fondo
// baja hacia la punta más honda.
// Puro: no usa el navegador. Se prueba con node --test.
// =============================================================

import { leerNumero, formatearCorto, redondear } from './numeros.js';
import { calcularDesarrollo } from './desarrollo.js';
import { calcularGeometria, calcularLimites } from './geometria.js';
import { copiarPerfil } from './perfil.js';

/** ¿El renglón es un plegado con pendiente? */
export function tienePendiente(renglon) {
  return Boolean(renglon?.conPendiente && renglon.tipoPieza === 'plegada' && renglon.perfil?.tramos?.length);
}

/** Medida final de un tramo (si no tiene, la misma del inicio). */
export function medidaFinal(tramo) {
  const final = tramo.medidaFinalCm;
  return final === undefined || final === null || final === '' ? tramo.medidaCm : final;
}

/** Ángulo final de un tramo (si no tiene, el mismo del inicio). */
export function anguloFinal(tramo) {
  const final = tramo.anguloPliegueFinal;
  return final === undefined || final === null || final === '' ? tramo.anguloPliegue : final;
}

/** Perfil de la punta final (derecha), armado con las medidas y ángulos finales. */
export function perfilFinal(perfil) {
  const final = copiarPerfil(perfil);
  final.tramos = final.tramos.map((tramo) => {
    const { medidaFinalCm, anguloPliegueFinal, ...resto } = tramo;
    return { ...resto, medidaCm: medidaFinal(tramo), anguloPliegue: anguloFinal(tramo) };
  });
  return final;
}

/**
 * Prende la pendiente: copia las medidas y ángulos del inicio como valores finales
 * (así en la tabla se ven los dos y el vendedor cambia solo los que difieren).
 */
export function activarPendiente(perfil) {
  const nuevo = copiarPerfil(perfil);
  for (const tramo of nuevo.tramos) {
    if (tramo.medidaFinalCm === undefined) tramo.medidaFinalCm = tramo.medidaCm;
    if (tramo.anguloPliegueFinal === undefined) tramo.anguloPliegueFinal = tramo.anguloPliegue;
  }
  return nuevo;
}

/**
 * Números de la pendiente.
 * @returns {{
 *   desarrolloInicialCm, desarrolloFinalCm,
 *   desarrolloCm,          // el MAYOR de los dos: es el ancho de chapa que hace falta (SUPUESTO)
 *   bajadaCm,              // cuánto más abajo queda el punto más bajo en la punta final (negativo = sube)
 *   milimetrosPorMetro,    // pendiente: mm de bajada por cada metro de largo
 *   porcentaje,            // la misma pendiente en %
 *   relacion,              // "1:49" (1 cm de bajada cada 49 cm); null si no hay bajada
 *   texto                  // "baja 5 cm en 2,44 m (20,5 mm/m · 1:49)"
 * }}
 */
export function calcularPendiente(renglon, config) {
  const perfil = renglon.perfil;
  const final = perfilFinal(perfil);
  const desarrolloInicialCm = calcularDesarrollo(perfil.tramos);
  const desarrolloFinalCm = calcularDesarrollo(final.tramos);
  const limitesInicio = calcularLimites(calcularGeometria(perfil, config).puntos);
  const limitesFinal = calcularLimites(calcularGeometria(final, config).puntos);
  const bajadaCm = redondear(limitesInicio.minY - limitesFinal.minY, 2);
  const largoCm = leerNumero(renglon.largoCm);

  let milimetrosPorMetro = null;
  let porcentaje = null;
  let relacion = null;
  if (largoCm > 0) {
    milimetrosPorMetro = redondear((bajadaCm * 10) / (largoCm / 100), 1);
    porcentaje = redondear((bajadaCm / largoCm) * 100, 2);
    if (Math.abs(bajadaCm) > 0.001) relacion = `1:${Math.round(largoCm / Math.abs(bajadaCm))}`;
  }

  let texto;
  if (Math.abs(bajadaCm) < 0.001) {
    texto = 'el fondo queda a nivel';
  } else {
    const verbo = bajadaCm > 0 ? 'baja' : 'sube';
    texto = `${verbo} ${formatearCorto(Math.abs(bajadaCm))} cm`;
    if (largoCm > 0) texto += ` en ${formatearCorto(redondear(largoCm / 100, 2))} m (${formatearCorto(Math.abs(milimetrosPorMetro), 1)} mm/m · ${relacion})`;
  }

  return {
    desarrolloInicialCm,
    desarrolloFinalCm,
    desarrolloCm: Math.max(desarrolloInicialCm, desarrolloFinalCm),
    bajadaCm,
    milimetrosPorMetro,
    porcentaje,
    relacion,
    texto,
  };
}

/** Texto para la descripción: "con pendiente D60 a D65". */
export function textoPendienteDescripcion(calculo) {
  return `con pendiente D${formatearCorto(calculo.desarrolloInicialCm, 1)} a D${formatearCorto(calculo.desarrolloFinalCm, 1)}`;
}

/**
 * Revisa las medidas y ángulos finales.
 * @returns {Array<{nivel, indice, mensaje}>}
 */
export function validarPendiente(renglon, config) {
  const problemas = [];
  renglon.perfil.tramos.forEach((tramo, indice) => {
    const numero = indice + 1;
    const medida = leerNumero(medidaFinal(tramo));
    if (!(medida > 0)) {
      problemas.push({ nivel: 'error', indice, mensaje: `Tramo ${numero}: falta la medida en la punta final` });
    }
    const esDobladillo = tramo.tipo === 'dobladillo' || tramo.tipo === 'dobladillo_aplastado'
      || (indice === 1 && ['dobladillo', 'dobladillo_aplastado'].includes(renglon.perfil.tramos[0].tipo));
    if (indice > 0 && !esDobladillo) {
      const angulo = leerNumero(anguloFinal(tramo));
      if (!Number.isFinite(angulo) || angulo < config.anguloMinimo || angulo > config.anguloMaximo) {
        problemas.push({ nivel: 'error', indice, mensaje: `Tramo ${numero}: el ángulo de la punta final tiene que estar entre ${config.anguloMinimo}° y ${config.anguloMaximo}°` });
      }
    }
  });
  const iguales = renglon.perfil.tramos.every((t) => leerNumero(medidaFinal(t)) === leerNumero(t.medidaCm)
    && leerNumero(anguloFinal(t)) === leerNumero(t.anguloPliegue));
  if (iguales) {
    problemas.push({ nivel: 'aviso', indice: null, mensaje: 'Pendiente: las dos puntas son iguales (cambiá la medida final de algún tramo)' });
  }
  return problemas;
}
