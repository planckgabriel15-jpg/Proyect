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

/** Filtra plantillas por texto (nombre o palabras clave), sin importar mayúsculas ni tildes. */
export function filtrarPlantillas(catalogo, texto) {
  const buscado = sinTildes(texto);
  if (!buscado) {
    return catalogo.plantillas;
  }
  return catalogo.plantillas.filter((p) =>
    sinTildes(`${p.nombre} ${(p.palabrasClave || []).join(' ')}`).includes(buscado));
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
    tipoPieza: plantilla.tipoPieza,                 // 'plegada' | 'especial'
    elemento: plantilla.elemento,                   // se usa para buscar el código
    textoDescripcion: plantilla.textoDescripcion,   // ej. "canaleta"
    usaLargo: plantilla.usaLargo !== false,
    calculoDesarrollo: plantilla.calculoDesarrollo || 'sumaDeTramos',
    usaPerfil: plantilla.usaPerfil === true,        // tapa suelta: pieza especial que igual lleva perfil
    sinMaterial: plantilla.sinMaterial === true,    // artículos de catálogo: sin material, calibre ni color
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
    codigoPendiente: false,
    // Tapas y boquetas puestas en la canaleta (solo canaletas).
    accesorios: plantilla.admiteAccesorios ? accesoriosVacios() : null,
    // Plegado con pendiente: el perfil cambia de una punta a la otra (ver pendiente.js).
    conPendiente: false,
  };
}

/** Copia un renglón con un id nuevo (botón "Duplicar"). */
export function duplicarRenglon(renglon) {
  const copia = JSON.parse(JSON.stringify(renglon));
  copia.id = crearId('r');
  return copia;
}
