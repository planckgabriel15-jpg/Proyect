// =============================================================
// fotoCalculo.js
// UNA sola fuente para lo que se muestra de cada renglón (pantalla, impresión, PDF,
// producción):
//
// - Mientras la nota es borrador se usa el cálculo en vivo (calcularRenglon).
// - Al EMITIR se guarda una "foto" (renglon.calculado) con lo que se factura:
//   descripción, código, códigos extra, desarrollo, banda y CANTIDAD DE CHAPAS.
//   Así la nota impresa no cambia si mañana cambia la tabla de códigos o la configuración.
// - Antes, la impresión mezclaba la foto con datos en vivo (empalme, pendiente) y la
//   foto se armaba en dos lugares distintos. Ahora la arma SOLO fotoDelCalculo().
//
// Y la regla del 3D opcional (por nota y por renglón): mostrar3d().
// =============================================================

import { calcularRenglon } from './calculoRenglon.js';
import { cantidadDeLaNota } from './chapas.js';
import { buscarPlantilla } from './renglones.js';

/** Versión de la foto. 2 = agrega cantidad (chapas), empalme y pendiente. */
export const VERSION_FOTO = 2;

/** Arma la foto de lo calculado (se guarda al emitir). */
export function fotoDelCalculo(renglon, resultado, config) {
  return {
    version: VERSION_FOTO,
    descripcion: resultado.descripcion,
    codigo: resultado.codigo.encontrado ? resultado.codigo.codigo : null,
    codigoGenerico: Boolean(resultado.codigo.generico),
    codigosAdicionales: resultado.codigosAdicionales,
    desarrolloCm: resultado.desarrolloCm,
    desarrolloEsManual: resultado.desarrolloEsManual,
    banda: resultado.banda,
    porUnidad: resultado.porUnidad,
    avisos: resultado.avisos,
    cantidad: cantidadDeLaNota(renglon, resultado, config),
    empalmeTexto: resultado.empalme?.texto || null,
    pendienteTexto: resultado.pendiente?.texto || null,
  };
}

/**
 * Completa una foto vieja (notas emitidas antes de la versión 2): le agrega la cantidad de
 * chapas calculada con los datos de la PROPIA foto (desarrollo, banda, por unidad).
 * No toca lo facturado (código, descripción).
 */
export function completarFotoVieja(renglon, foto, config, vivo = null) {
  if (foto.version >= VERSION_FOTO) return foto;
  const base = { porUnidad: foto.porUnidad, desarrolloCm: foto.desarrolloCm, banda: foto.banda };
  return {
    ...foto,
    version: VERSION_FOTO,
    codigoGenerico: Boolean(foto.codigoGenerico),
    cantidad: cantidadDeLaNota(renglon, base, config),
    empalmeTexto: foto.empalmeTexto ?? vivo?.empalme?.texto ?? null,
    pendienteTexto: foto.pendienteTexto ?? vivo?.pendiente?.texto ?? null,
    completadaDesdeVersion: foto.version || 1,
  };
}

/**
 * Lo que se muestra del renglón.
 * @returns {{vivo: object, foto: object}} vivo = calcularRenglon (para dibujos y errores);
 *   foto = lo que se factura (la guardada si la nota está emitida, si no la del cálculo en vivo).
 */
export function datosDelRenglon(renglon, datos) {
  const vivo = calcularRenglon(renglon, datos);
  const foto = renglon.calculado
    ? completarFotoVieja(renglon, renglon.calculado, datos.config, vivo)
    : fotoDelCalculo(renglon, vivo, datos.config);
  return { vivo, foto };
}

// ---------- 3D opcional ----------

export const OPCIONES_3D_NOTA = [
  { valor: 'auto', texto: '3D automático (no en productos estándar)' },
  { valor: 'si', texto: '3D en todos los renglones' },
  { valor: 'no', texto: 'Sin 3D (solo dibujo 2D)' },
];

/** Lo que haría la regla automática para este renglón (sin elección del renglón ni de la nota). */
export function mostrar3dPorDefecto(renglon, datos) {
  const apagados = datos.config.vista3d?.gruposApagadosPorDefecto || [];
  const plantilla = datos.catalogo ? buscarPlantilla(datos.catalogo, renglon.plantillaId) : null;
  return !(plantilla && apagados.includes(plantilla.grupo));
}

/**
 * ¿Este renglón lleva imagen 3D? Manda, en orden: lo elegido en el renglón (true/false),
 * lo elegido en la nota ('si'/'no') y la regla automática.
 */
export function mostrar3d(renglon, nota, datos) {
  if (renglon.mostrar3d === true || renglon.mostrar3d === false) return renglon.mostrar3d;
  if (nota?.mostrar3d === 'si') return true;
  if (nota?.mostrar3d === 'no') return false;
  return mostrar3dPorDefecto(renglon, datos);
}
