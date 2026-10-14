// Ayudante para las pruebas: lee los archivos de /datos y crea un "localStorage" falso en memoria.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const carpetaDatos = join(dirname(fileURLToPath(import.meta.url)), '..', 'datos');

export function leerDatos(nombreArchivo) {
  return JSON.parse(readFileSync(join(carpetaDatos, nombreArchivo), 'utf8'));
}

/** Todos los datos que usa calcularRenglon(). */
export function datosCompletos() {
  return {
    config: leerDatos('config.json'),
    materiales: leerDatos('materiales.json'),
    codigos: leerDatos('codigos.json'),
    catalogo: leerDatos('catalogo.json'),
  };
}

/** Imita al localStorage del navegador, pero en memoria. */
export function crearMotorEnMemoria() {
  const cajon = new Map();
  return {
    getItem: (clave) => (cajon.has(clave) ? cajon.get(clave) : null),
    setItem: (clave, valor) => cajon.set(clave, String(valor)),
    removeItem: (clave) => cajon.delete(clave),
  };
}

/** Renglón de la canaleta de la nota real: 2,44 m, pp negro, C25, 1 aplastado + 20 + 32 + 7. */
export function renglonCanaletaNotaReal() {
  return {
    id: 'r1',
    plantillaId: 'canaleta_nota_real',
    tipoPieza: 'plegada',
    elemento: 'canaleta',
    textoDescripcion: 'canaleta',
    usaLargo: true,
    perfil: {
      direccionInicial: 'arriba',
      tramos: [
        { medidaCm: 1, anguloPliegue: 90, sentido: 'izquierda', tipo: 'dobladillo_aplastado' },
        { medidaCm: 20, anguloPliegue: 90, sentido: 'derecha', tipo: 'normal' },
        { medidaCm: 32, anguloPliegue: 90, sentido: 'izquierda', tipo: 'normal' },
        { medidaCm: 7, anguloPliegue: 90, sentido: 'izquierda', tipo: 'normal' },
      ],
    },
    parametros: {},
    largoCm: 244,
    materialId: 'galvanizado',
    calibreId: 'C25',
    terminacion: 'P',
    colorId: 'negro',
    ladoPintura: 'afuera',
    cantidad: 1,
    observaciones: '',
    codigoPendiente: false,
    vinculadoA: null,
  };
}
