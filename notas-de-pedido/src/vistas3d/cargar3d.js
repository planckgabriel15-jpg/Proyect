// =============================================================
// cargar3d.js
// Carga el 3D "a demanda". Three.js viene de internet (CDN): si no se puede
// cargar, el programa sigue funcionando sin el 3D (el 2D es la referencia
// oficial para fabricar).
// =============================================================

let promesa = null;

/** @returns {Promise<{crearVisor3d, capturarRenglon}|null>} */
export function cargar3d() {
  if (!promesa) {
    promesa = Promise.all([import('./escena.js'), import('./capturas.js')])
      .then(([escena, capturas]) => ({ crearVisor3d: escena.crearVisor3d, capturarRenglon: capturas.capturarRenglon }))
      .catch((error) => {
        console.warn('No se pudo cargar el 3D:', error);
        return null;
      });
  }
  return promesa;
}
