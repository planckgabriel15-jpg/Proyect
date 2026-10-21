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
import { armarCodigoGenerico } from './codigoGenerico.js';
import { validarAccesorios, normalizarBoqueta, nombreDeBoqueta, perfilDeTapa, TIPOS_BOQUETA, tipoDeTapa } from './accesoriosCanaleta.js';
import { validarCortes } from './cortes.js';
import { tramosDeChapa, validarEmpalme, textoEmpalme } from './empalme.js';
import { tienePendiente, calcularPendiente, validarPendiente } from './pendiente.js';

export const AVISO_CODIGO_GENERICO = 'Código genérico: no está en la tabla de facturación, confirmarlo con administración';

/**
 * @param {object} renglon
 * @param {{config: object, materiales: object, codigos: Array, catalogo?: object}} datos
 * @returns {{
 *   desarrolloCm: number|null, desarrolloEsManual: boolean, formulaDesarrollo: string, porUnidad: boolean,
 *   banda: object, codigo: {encontrado: boolean, codigo: string|null, aviso: string|null},
 *   descripcion: string, errores: string[], avisos: string[], puedeEmitirse: boolean,
 *   problemasTramos: Array, pendiente: object|null  (ver pendiente.js → calcularPendiente)
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

  let pendiente = null;
  if (renglon.tipoPieza === 'plegada') {
    problemasTramos = validarTramos(renglon.perfil?.tramos, config);
    desarrolloCm = calcularDesarrollo(renglon.perfil?.tramos);
    if (tienePendiente(renglon)) {
      // Con pendiente: se cotiza por el MAYOR de los dos desarrollos (SUPUESTO, ver PENDIENTES.md).
      problemasTramos = problemasTramos.concat(validarPendiente(renglon, config));
      pendiente = calcularPendiente(renglon, config);
      desarrolloCm = pendiente.desarrolloCm;
      formulaDesarrollo = 'el mayor de los dos perfiles (inicio y final)';
    }
    agregar(problemasTramos);
  } else {
    const calculo = calcularDesarrolloEspecial(renglon.calculoDesarrollo, renglon.parametros, config);
    desarrolloCm = calculo.desarrolloCm;
    porUnidad = calculo.porUnidad;
    formulaDesarrollo = calculo.formula;

    const plantilla = catalogo ? buscarPlantilla(catalogo, renglon.plantillaId) : null;
    if (plantilla) {
      agregar(validarParametros(plantilla, renglon.parametros));
    }

    // Tapa suelta: necesita el perfil de la canaleta para poder fabricarse.
    if (renglon.usaPerfil) {
      if (!renglon.perfil?.tramos?.length) {
        errores.push('La tapa necesita el perfil de la canaleta: copialo de una canaleta o cargalo en la tabla');
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
  // Empalme: en qué tramos de chapa se arma la pieza (si es más larga que la chapa, o si se pidió).
  const tramosChapa = renglon.usaLargo !== false && renglon.tipoPieza === 'plegada' ? tramosDeChapa(renglon, config) : [];
  const empalme = tramosChapa.length > 1 ? { tramosCm: tramosChapa, texto: textoEmpalme(tramosChapa) } : null;
  if (empalme) agregar(validarEmpalme(renglon, config));

  // ---- 2b) Tapas y boquetas puestas en la canaleta ----
  if (renglon.accesorios) {
    agregar(validarAccesorios(renglon.accesorios, renglon.largoCm, config, renglon));
  }

  // ---- 2c) Cortes en las caras ----
  if (renglon.cortes?.length) {
    agregar(validarCortes(renglon, config));
  }

  // ---- 3) Material, calibre, color, cantidad ----
  agregar(validarMaterialYCantidad(renglon, materiales, config));

  // ---- 4) Banda ----
  const banda = porUnidad
    ? { numero: null, nombre: 'por unidad', requiereSoldar: false, aviso: null }
    : calcularBanda(desarrolloCm, config);
  if (banda.requiereSoldar) {
    avisos.push(AVISO_REQUIERE_SOLDAR);
  }

  // ---- 5) Código (se BUSCA en la tabla, no se arma) ----
  const material = materiales.materiales.find((m) => m.id === renglon.materialId);
  const calibre = materiales.calibres.find((c) => c.id === renglon.calibreId);
  let codigo = { encontrado: false, codigo: null, aviso: null, generico: false };
  if (material && calibre) {
    const criterio = {
      elemento: renglon.elemento,
      material: material.codigo,
      espesor: calibre.codigoEspesor,
      terminacion: renglon.terminacion,
      banda: banda.numero ?? 'UN',
    };
    if (renglon.codigoGenerico) {
      // Productos sin código en facturación: si la tabla tiene una fila para ESE elemento, manda la tabla;
      // si no, se arma el código genérico (siglas + medidas + letra de color/material).
      codigo = { ...buscarCodigo(codigos, { ...criterio, soloElementoExacto: true }), generico: false };
      if (!codigo.encontrado) {
        const generico = armarCodigoGenerico(renglon.codigoGenerico, renglon, materiales);
        if (generico) {
          codigo = { encontrado: true, codigo: generico, aviso: AVISO_CODIGO_GENERICO, generico: true };
          avisos.push(AVISO_CODIGO_GENERICO);
        }
      }
    } else {
      codigo = { ...buscarCodigo(codigos, criterio), generico: false };
    }
    if (!codigo.encontrado) {
      if (renglon.codigoPendiente) {
        avisos.push('Código pendiente: lo completa administración');
      } else {
        errores.push(codigo.aviso || 'Código no encontrado: avisar a administración');
      }
    }
  }

  // ---- 5b) Códigos extra: tapas y boquetas puestas en la canaleta ----
  // Pedido de la empresa: se factura la canaleta con su código y, además, cada tapa
  // (con el código de la tapa suelta) y cada boqueta (con el de la boqueta suelta),
  // aunque ya vayan soldadas o engrampadas.
  const codigosAdicionales = renglon.accesorios ? codigosDeAccesorios(renglon, datos) : [];

  // ---- 6) Descripción ----
  const descripcion = armarDescripcion(renglon, materiales, { desarrolloCm, porUnidad, pendiente, empalme });

  return {
    desarrolloCm,
    desarrolloEsManual,
    formulaDesarrollo,
    porUnidad,
    banda,
    codigo,
    codigosAdicionales,
    descripcion,
    errores,
    avisos,
    puedeEmitirse: errores.length === 0,
    problemasTramos,
    pendiente,
    empalme,
  };
}

/** Definición del código genérico de un producto suelto (tapa suelta, boqueta suelta). */
function definicionDe(catalogo, plantillaId, porDefecto) {
  const plantilla = catalogo ? buscarPlantilla(catalogo, plantillaId) : null;
  return plantilla?.codigoGenerico || porDefecto;
}

/**
 * Códigos extra de una canaleta con tapas y boquetas.
 * @returns {Array<{codigo: string, descripcion: string, cantidad: number}>}
 */
export function codigosDeAccesorios(renglon, datos) {
  const { materiales, catalogo } = datos;
  const acc = renglon.accesorios;
  const cantidadCanaletas = Math.max(1, Math.round(leerNumero(renglon.cantidad) || 1));
  const lista = [];
  const sumar = (codigo, descripcion, cantidad) => {
    if (!codigo) return;
    const existente = lista.find((x) => x.codigo === codigo);
    if (existente) existente.cantidad += cantidad;
    else lista.push({ codigo, descripcion, cantidad });
  };

  const defTapa = definicionDe(catalogo, 'tapa_suelta', { siglas: 'TS', medidas: ['desarrolloPerfil'] });
  // Cada tapa lleva su perfil: el de la canaleta en esa punta (con pendiente la derecha es otro)
  // o el suyo si es a medida. Si las dos dan el mismo código, van juntas en una línea.
  const tapas = ['izquierda', 'derecha']
    .map((lado) => ({ lado, abreviado: lado === 'izquierda' ? 'izq.' : 'der.', tipo: tipoDeTapa(acc, lado) }))
    .filter((t) => t.tipo !== 'ninguna')
    .map((t) => ({ ...t, codigo: armarCodigoGenerico(defTapa, { ...renglon, perfil: perfilDeTapa(renglon, t.lado, datos.config), parametros: {} }, materiales) }));
  for (const codigo of [...new Set(tapas.map((t) => t.codigo))]) {
    const iguales = tapas.filter((t) => t.codigo === codigo);
    const detalle = iguales.map((t) => `${t.abreviado} ${t.tipo}`).join(', ');
    sumar(codigo, iguales.length > 1 ? `2 tapas (${detalle})` : `tapa ${detalle}`, iguales.length * cantidadCanaletas);
  }

  // Cada boqueta factura con el código del mismo producto suelto (boqueta, tronera, colector…).
  const defBoqueta = definicionDe(catalogo, 'boqueta_suelta', {
    siglasPorForma: { redonda: 'BQ', cuadrada: 'BQC', rectangular: 'BQR' },
    medidasPorForma: { redonda: ['diametroCm'], cuadrada: ['ladoACm'], rectangular: ['ladoACm', 'ladoBCm'] },
  });
  for (const original of acc.boquetas || []) {
    const boqueta = normalizarBoqueta(original, datos.config);
    const tipo = TIPOS_BOQUETA.find((t) => t.valor === boqueta.tipo) || TIPOS_BOQUETA[0];
    const definicion = tipo.valor === 'boqueta' ? defBoqueta : definicionDe(catalogo, tipo.plantillaId, null);
    // Los artículos de reventa (colectores) no llevan letra de color ni material en el código.
    const sinMaterial = Boolean(catalogo && buscarPlantilla(catalogo, tipo.plantillaId)?.sinMaterial);
    const codigo = definicion ? armarCodigoGenerico(definicion, { ...renglon, sinMaterial, parametros: { ...boqueta } }, materiales) : null;
    sumar(codigo, nombreDeBoqueta(boqueta), cantidadCanaletas);
  }
  return lista;
}
