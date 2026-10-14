// =============================================================
// estado.js
// Lo que todas las pantallas comparten: los datos cargados y la sesión.
// Se completa una sola vez al arrancar (ver app.js).
// =============================================================

export const estado = {
  datos: null,     // { config, sucursales, vendedores, materiales, catalogo, codigos, glosario }
  sesion: null,    // { vendedorId, sucursalHoyId }
};

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
