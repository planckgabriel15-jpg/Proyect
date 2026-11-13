// =============================================================
// estado.js
// Lo que todas las pantallas comparten: los datos cargados y la sesión.
// Se completa una sola vez al arrancar (ver app.js).
// =============================================================

import { empresaDeSucursal, buscarEmpresa, buscarPlanta, listaEmpresas } from '../logica/empresas.js';

export const estado = {
  datos: null,     // { config, grupo, sucursales, vendedores, materiales, catalogo, codigos, glosario, tiemposMtm, produccion }
  sesion: null,    // { rol, vendedorId, sucursalHoyId, operarioId, plantaId, verTodoElGrupo }
};

/**
 * Planta que mira quien está usando el programa: el operario, la suya; el jefe, la que eligió
 * (null = todas las plantas); el comercial, ninguna en particular (ve sus notas en todas).
 */
export function plantaDeSesion() {
  const sesion = estado.sesion || {};
  if (sesion.rol === 'operario') return estado.datos.produccion.operarios.find((o) => o.id === sesion.operarioId)?.planta || null;
  if (sesion.rol === 'jefe') return sesion.plantaId || null;
  return null;
}

/** Empresa de quien está usando el programa (de ahí salen el logo, los colores y el catálogo). */
export function empresaActual() {
  const { datos, sesion } = estado;
  if (!datos) return null;
  if (sesion?.rol === 'comercial' && sesion.sucursalHoyId) return empresaDeSucursal(datos, sesion.sucursalHoyId);
  const planta = buscarPlanta(datos, plantaDeSesion());
  return buscarEmpresa(datos, planta?.empresaId) || listaEmpresas(datos)[0] || null;
}

/** Vendedor que está usando el programa. */
export function vendedorActual() {
  return estado.datos?.vendedores.find((v) => v.id === estado.sesion?.vendedorId) || null;
}

/** Sucursal donde trabaja hoy el vendedor. */
export function sucursalActual() {
  return estado.datos?.sucursales.find((s) => s.id === estado.sesion?.sucursalHoyId) || null;
}

export function nombreSucursal(id) {
  return estado.datos?.sucursales.find((s) => s.id === id)?.nombre || id;
}

export function nombreVendedor(id) {
  return estado.datos?.vendedores.find((v) => v.id === id)?.nombre || id;
}

/** Cambia de pantalla (las pantallas se eligen con lo que va después de # en la dirección). */
export function ir(ruta) {
  window.location.hash = ruta;
}
