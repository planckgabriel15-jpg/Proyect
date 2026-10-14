// =============================================================
// perfil.js
// Herramientas para EDITAR un perfil (lista de tramos) sin romper el dibujo:
// agregar tramos, aletas y dobladillos al principio o al final, insertar,
// borrar y espejar.
//
// Todas las funciones devuelven un perfil NUEVO (no modifican el original).
// Así es fácil tener "deshacer": se guarda la versión anterior.
// =============================================================

import { calcularGeometria, esDobladillo, normalizarGrados, nombreDeDireccion, direccionEnGrados } from './geometria.js';

/** Crea un tramo con valores por defecto. */
export function crearTramo(datos = {}) {
  return {
    medidaCm: datos.medidaCm ?? 10,
    anguloPliegue: datos.anguloPliegue ?? 90,
    sentido: datos.sentido ?? 'izquierda',
    tipo: datos.tipo ?? 'normal',
    observacion: datos.observacion ?? '',
    corteLaser: datos.corteLaser ?? null,
  };
}

/** Copia profunda de un perfil (para no tocar el original). */
export function copiarPerfil(perfil) {
  return JSON.parse(JSON.stringify(perfil));
}

/** Agrega un tramo al final. */
export function agregarTramoAlFinal(perfil, datosTramo = {}) {
  const nuevo = copiarPerfil(perfil);
  nuevo.tramos.push(crearTramo(datosTramo));
  return nuevo;
}

/**
 * Agrega un tramo al principio SIN mover el resto del dibujo.
 * El ángulo y el sentido de datosTramo describen el pliegue entre el tramo nuevo
 * y el que antes era el primero.
 */
export function agregarTramoAlInicio(perfil, datosTramo = {}) {
  const nuevo = copiarPerfil(perfil);
  const tramoNuevo = crearTramo(datosTramo);

  if (nuevo.tramos.length === 0) {
    nuevo.tramos.push(tramoNuevo);
    return nuevo;
  }

  // Ojo: si el primer tramo actual es un dobladillo, el pliegue de 180° pasa a estar
  // entre el tramo nuevo y el dobladillo (regla de geometria.js). Es raro agregar algo
  // antes de un dobladillo, pero el dibujo lo muestra y el vendedor lo puede corregir.
  const direccionPrimeroViejo = direccionEnGrados(nuevo.direccionInicial);
  const primeroViejo = nuevo.tramos[0];
  // El que era primero ahora gira respecto del nuevo.
  primeroViejo.anguloPliegue = tramoNuevo.anguloPliegue;
  primeroViejo.sentido = tramoNuevo.sentido;

  // Calculamos hacia dónde tiene que apuntar el tramo nuevo para que, después del
  // giro, el que era primero siga apuntando igual que antes.
  const giro = esDobladillo(tramoNuevo) ? 180 : 180 - Number(tramoNuevo.anguloPliegue);
  const signo = tramoNuevo.sentido === 'derecha' ? -1 : 1;
  const direccionNuevo = normalizarGrados(direccionPrimeroViejo - signo * giro);

  nuevo.tramos.unshift(tramoNuevo);
  nuevo.direccionInicial = nombreDeDireccion(direccionNuevo);
  return nuevo;
}

/** Inserta un tramo ANTES del tramo número `indice`. */
export function insertarTramoAntes(perfil, indice, datosTramo = {}) {
  if (indice <= 0) {
    return agregarTramoAlInicio(perfil, datosTramo);
  }
  const nuevo = copiarPerfil(perfil);
  nuevo.tramos.splice(indice, 0, crearTramo(datosTramo));
  return nuevo;
}

/**
 * Borra el tramo número `indice`.
 * Si se borra el primero, el segundo pasa a ser el primero y conserva su dirección.
 */
export function borrarTramo(perfil, indice, config) {
  const nuevo = copiarPerfil(perfil);
  if (indice < 0 || indice >= nuevo.tramos.length) {
    return nuevo;
  }
  if (indice === 0 && nuevo.tramos.length > 1) {
    const geometria = calcularGeometria(perfil, config);
    nuevo.direccionInicial = nombreDeDireccion(geometria.segmentos[1].direccion);
  }
  nuevo.tramos.splice(indice, 1);
  return nuevo;
}

/**
 * Agrega un dobladillo en una punta del perfil.
 * @param {'inicio'|'fin'} extremo
 * @param {boolean} aplastado  true = dobladillo aplastado (cerrado)
 */
export function agregarDobladillo(perfil, extremo, aplastado, medidaCm = 1, sentido = 'izquierda') {
  const datos = { medidaCm, sentido, tipo: aplastado ? 'dobladillo_aplastado' : 'dobladillo', anguloPliegue: 90 };
  return extremo === 'inicio'
    ? agregarTramoAlInicio(perfil, datos)
    : agregarTramoAlFinal(perfil, datos);
}

/**
 * Agrega una aleta (tramo normal con su pliegue) en una punta del perfil.
 * @param {'inicio'|'fin'} extremo
 */
export function agregarAleta(perfil, extremo, medidaCm = 3, anguloPliegue = 90, sentido = 'izquierda') {
  const datos = { medidaCm, anguloPliegue, sentido, tipo: 'normal' };
  return extremo === 'inicio'
    ? agregarTramoAlInicio(perfil, datos)
    : agregarTramoAlFinal(perfil, datos);
}

/** Espeja el perfil (como verlo desde atrás): izquierda ↔ derecha. */
export function espejarPerfil(perfil) {
  const nuevo = copiarPerfil(perfil);
  nuevo.direccionInicial = nombreDeDireccion(180 - direccionEnGrados(nuevo.direccionInicial));
  for (const tramo of nuevo.tramos) {
    tramo.sentido = tramo.sentido === 'derecha' ? 'izquierda' : 'derecha';
  }
  return nuevo;
}
