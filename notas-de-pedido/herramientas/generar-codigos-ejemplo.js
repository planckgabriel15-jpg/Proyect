// =============================================================
// generar-codigos-ejemplo.js
// Arma una tabla de códigos DE EJEMPLO (datos/codigos.json) combinando
// materiales × espesores × terminaciones × bandas con el patrón confirmado:
//   material + espesor + terminación + banda   →   CG + 05 + P + 60 = CG05P60
//
// OJO: esto es solo para probar. El programa NUNCA arma el código así:
// siempre lo BUSCA en la tabla. Cuando llegue la lista real del sistema de
// facturación, se reemplaza datos/codigos.json (o se importa desde Configuración).
//
// Uso:  node herramientas/generar-codigos-ejemplo.js
// =============================================================

import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, join } from 'node:path';

/**
 * @param {object} materiales  datos/materiales.json
 * @param {object} config      datos/config.json
 * @returns {Array<{elemento, material, espesor, terminacion, banda, codigo}>}
 */
export function generarCodigosEjemplo(materiales, config) {
  const bandas = [
    config.bandas.numeroCuartoChapa,
    config.bandas.numeroMediaChapa,
    config.bandas.numeroChapaCompleta,
  ];
  const filas = [];
  for (const material of materiales.materiales) {
    for (const calibre of materiales.calibres) {
      for (const terminacion of material.terminaciones) {
        for (const banda of bandas) {
          filas.push({
            elemento: '*', // SUPUESTO: todavía no sabemos cómo cambia el código según el elemento
            material: material.codigo,
            espesor: calibre.codigoEspesor,
            terminacion,
            banda: String(banda),
            codigo: `${material.codigo}${calibre.codigoEspesor}${terminacion}${banda}`,
          });
        }
      }
    }
  }
  return filas;
}

// Solo se ejecuta si se llama directo desde la terminal (no cuando lo importa una prueba).
const esEjecucionDirecta = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (esEjecucionDirecta) {
  const carpetaDatos = join(dirname(fileURLToPath(import.meta.url)), '..', 'datos');
  const materiales = JSON.parse(readFileSync(join(carpetaDatos, 'materiales.json'), 'utf8'));
  const config = JSON.parse(readFileSync(join(carpetaDatos, 'config.json'), 'utf8'));
  const filas = generarCodigosEjemplo(materiales, config);

  if (!filas.some((f) => f.codigo === 'CG05P60')) {
    throw new Error('La tabla de ejemplo tiene que incluir CG05P60');
  }

  writeFileSync(join(carpetaDatos, 'codigos.json'), JSON.stringify(filas, null, 2) + '\n', 'utf8');
  console.log(`Listo: ${filas.length} códigos de ejemplo en datos/codigos.json (incluye CG05P60).`);
}
