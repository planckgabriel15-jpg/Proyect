// =============================================================
// calculoRenglon.js
// Junta todos los cálculos de un renglón en una sola función:
// desarrollo → banda → código → descripción → errores y avisos.
// Es lo que usa el "panel de resultados" que se actualiza en vivo.
// =============================================================

import { leerNumero, formatearCorto } from './numeros.js';
import { calcularDesarrollo } from './desarrollo.js';
import { calcularBanda, AVISO_REQUIERE_SOLDAR } from './banda.js';
import { buscarCodigo } from './codigos.js';
import { calcularDesarrolloEspecial, validarParametros } from './piezasEspeciales.js';
import { validarTramos, validarLargo, validarMaterialYCantidad } from './validaciones.js';
import { armarDescripcion } from './descripcion.js';
import { buscarPlantilla } from './renglones.js';

/**
 * @param {object} renglon
 * @param {{config: object, materiales: object, codigos: Array, catalogo?: object}} datos
 * @returns {{
 *   desarrolloCm: number|null, desarrolloEsManual: boolean, formulaDesarrollo: string, porUnidad: boolean,
 *   banda: object, codigo: {encontrado: boolean, codigo: string|null, aviso: string|null},
 *   descripcion: string, errores: string[], avisos: string[], puedeEmitirse: boolean,
 *   problemasTramos: Array
 * }}
 */
export function calcularRenglon(renglon, datos) {
  const { config, materiales, codigos, catalogo } = datos;
  const errores = [];
  const avisos = [];
  const agregar = (problemas) => {
    for (const p of problemas) {
      (p.nivel === 'error' ? errores : avisos).push(p.mensaje);
    }
  };

  // ---- 1) Desarrollo ----
  let desarrolloCm = null;
  let porUnidad = false;
  let formulaDesarrollo = 'suma de las medidas de los tramos';
  let desarrolloEsManual = false;
  let problemasTramos = [];

  if (renglon.tipoPieza === 'plegada') {
    problemasTramos = validarTramos(renglon.perfil?.tramos, config);
    agregar(problemasTramos);
    desarrolloCm = calcularDesarrollo(renglon.perfil?.tramos);
  } else {
    const calculo = calcularDesarrolloEspecial(renglon.calculoDesarrollo, renglon.parametros, config);
    desarrolloCm = calculo.desarrolloCm;
    porUnidad = calculo.porUnidad;
    formulaDesarrollo = calculo.formula;

    const plantilla = catalogo ? buscarPlantilla(catalogo, renglon.plantillaId) : null;
    if (plantilla) {
      agregar(validarParametros(plantilla, renglon.parametros));
    }

    // Tapas: necesitan el perfil de la canaleta para poder fabricarse.
    if (renglon.usaPerfilVinculado) {
      if (!renglon.perfil?.tramos?.length) {
        errores.push('La tapa necesita el perfil de una canaleta: vinculala al renglón de la canaleta');
      } else {
        problemasTramos = validarTramos(renglon.perfil.tramos, config);
        agregar(problemasTramos);
      }
    }

    // El vendedor puede corregir el desarrollo a mano (queda registrado).
    const manual = leerNumero(renglon.desarrolloManualCm);
    if (!porUnidad && manual > 0) {
      desarrolloCm = manual;
      desarrolloEsManual = true;
      avisos.push(`Desarrollo corregido a mano: ${formatearCorto(manual)} cm (fórmula: ${formulaDesarrollo})`);
    }
  }

  // ---- 2) Largo ----
  if (renglon.usaLargo !== false) {
    agregar(validarLargo(renglon.largoCm, config));
  }

  // ---- 3) Material, calibre, color, cantidad ----
  agregar(validarMaterialYCantidad(renglon, materiales, config));

  // ---- 4) Banda ----
  const banda = porUnidad
    ? { numero: config.bandaPorUnidad, nombre: 'por unidad', requiereSoldar: false, aviso: null }
    : calcularBanda(desarrolloCm, config);
  if (banda.requiereSoldar) {
    avisos.push(AVISO_REQUIERE_SOLDAR);
  }

  // ---- 5) Código (se BUSCA en la tabla, no se arma) ----
  const material = materiales.materiales.find((m) => m.id === renglon.materialId);
  const calibre = materiales.calibres.find((c) => c.id === renglon.calibreId);
  let codigo = { encontrado: false, codigo: null, aviso: null };
  if (material && calibre) {
    codigo = buscarCodigo(codigos, {
      elemento: renglon.elemento,
      material: material.codigo,
      espesor: calibre.codigoEspesor,
      terminacion: renglon.terminacion,
      banda: banda.numero,
    });
    if (!codigo.encontrado) {
      if (renglon.codigoPendiente) {
        avisos.push('Código pendiente: lo completa administración');
      } else {
        errores.push(codigo.aviso);
      }
    }
  }

  // ---- 6) Descripción ----
  const descripcion = armarDescripcion(renglon, materiales, { desarrolloCm, porUnidad });

  return {
    desarrolloCm,
    desarrolloEsManual,
    formulaDesarrollo,
    porUnidad,
    banda,
    codigo,
    descripcion,
    errores,
    avisos,
    puedeEmitirse: errores.length === 0,
    problemasTramos,
  };
}
