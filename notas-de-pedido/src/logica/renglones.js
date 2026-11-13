// =============================================================
// renglones.js
// Crear y duplicar renglones de la nota.
// Un renglón = una pieza (con su dibujo, largo, material, código y cantidad).
// =============================================================

import { copiarPerfil } from './perfil.js';
import { accesoriosVacios } from './accesoriosCanaleta.js';

/** Busca una plantilla del catálogo por su id. */
export function buscarPlantilla(catalogo, plantillaId) {
  return (catalogo.plantillas || []).find((p) => p.id === plantillaId) || null;
}

/** Todo el texto por el que se puede encontrar una plantilla: nombre, palabras del mostrador, marca y modelos. */
export function textoBuscable(plantilla) {
  const modelos = (plantilla.parametros || []).filter((d) => d.tipo === 'opciones' && d.id === 'variante')
    .flatMap((d) => d.opciones.map((o) => o.etiqueta));
  return sinTildes([plantilla.nombre, ...(plantilla.palabrasClave || []), plantilla.marca || '', ...modelos].join(' '));
}

/**
 * Filtra plantillas por texto, sin importar mayúsculas ni tildes. Se puede escribir más de una
 * palabra y en cualquier orden ("caño 100", "tapa americana"): tienen que estar todas.
 * @param {Array} [plantillas]  lista donde buscar (por defecto todo el catálogo)
 */
export function filtrarPlantillas(catalogo, texto, plantillas = catalogo.plantillas) {
  const palabras = sinTildes(texto).split(/\s+/).filter(Boolean);
  if (!palabras.length) {
    return plantillas;
  }
  return plantillas.filter((p) => {
    const donde = textoBuscable(p);
    return palabras.every((palabra) => donde.includes(palabra));
  });
}

/** Agrupa las plantillas por grupo, respetando el orden de catalogo.grupos. */
export function agruparPlantillas(catalogo, plantillas = catalogo.plantillas) {
  return catalogo.grupos
    .map((grupo) => ({ ...grupo, plantillas: plantillas.filter((p) => p.grupo === grupo.id) }))
    .filter((grupo) => grupo.plantillas.length > 0);
}

function sinTildes(texto) {
  return String(texto || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
}

/** Identificador único simple (no depende del navegador). */
export function crearId(prefijo = 'r') {
  return `${prefijo}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

/**
 * Crea un renglón nuevo a partir de una plantilla del catálogo.
 * Copia el perfil y los parámetros por defecto para que el vendedor los modifique.
 * @param {object} plantilla
 * @param {object} config  datos/config.json (usa config.renglonPorDefecto)
 */
export function crearRenglonDesdePlantilla(plantilla, config) {
  const porDefecto = config.renglonPorDefecto;
  const parametros = {};
  for (const definicion of plantilla.parametros || []) {
    parametros[definicion.id] = definicion.valorPorDefecto;
  }

  return {
    id: crearId('r'),
    plantillaId: plantilla.id,
    tipoPieza: plantilla.tipoPieza,                 // 'plegada' | 'especial' | 'metalmecanica' | 'servicio'
    elemento: plantilla.elemento,                   // se usa para buscar el código
    textoDescripcion: plantilla.textoDescripcion,   // ej. "canaleta"
    usaLargo: plantilla.usaLargo !== false,
    calculoDesarrollo: plantilla.calculoDesarrollo || 'sumaDeTramos',
    usaPerfil: plantilla.usaPerfil === true,        // tapa suelta: pieza especial que igual lleva perfil
    sinMaterial: plantilla.sinMaterial === true,    // artículos de catálogo: sin material, calibre ni color
    sinDibujo: plantilla.sinDibujo === true,        // artículos, servicios y piezas con plano: no llevan dibujo
    cantidadDecimal: plantilla.cantidadDecimal === true, // servicios: 2,5 horas
    // Dónde se hace (ver logica/empresas.js): planta, "tercero" o null; y si sale de stock o se fabrica.
    fabricaEn: plantilla.fabricaEn ?? null,
    abastecimiento: plantilla.abastecimiento || (plantilla.sinMaterial && plantilla.tipoPieza === 'especial' ? 'stock' : 'a_pedido'),
    codigoGenerico: plantilla.codigoGenerico || null, // cómo armar el código si no está en la tabla
    generador3d: plantilla.generador3d || 'extrusion',
    perfil: plantilla.perfil ? copiarPerfil(plantilla.perfil) : { direccionInicial: 'arriba', tramos: [] },
    parametros,
    largoCm: plantilla.usaLargo === false ? null : (plantilla.largoPorDefectoCm ?? porDefecto.largoCm),
    materialId: porDefecto.materialId,
    calibreId: porDefecto.calibreId,
    terminacion: porDefecto.terminacion,
    colorId: porDefecto.colorId,
    ladoPintura: porDefecto.ladoPintura,
    cantidad: 1,
    observaciones: '',
    desarrolloManualCm: null,
    codigoPendiente: plantilla.codigoPendiente === true, // productos sin código de facturación cargado
    // Tapas y boquetas puestas en la canaleta (solo canaletas).
    accesorios: plantilla.admiteAccesorios ? accesoriosVacios() : null,
    // Plegado con pendiente: el perfil cambia de una punta a la otra (ver pendiente.js).
    conPendiente: false,
    // Cortes (agujeros) en las caras, con pared opcional (ver cortes.js).
    cortes: [],
    // Empalme cuando la pieza es más larga que la chapa (ver empalme.js). null = automático.
    empalme: null,
  };
}

/** Copia un renglón con un id nuevo (botón "Duplicar"). */
export function duplicarRenglon(renglon) {
  const copia = JSON.parse(JSON.stringify(renglon));
  copia.id = crearId('r');
  return copia;
}
