import { test } from 'node:test';
import assert from 'node:assert/strict';

import { crearCorteLaser, validarCorteLaser, generarBordeOndulado, describirCorteLaser } from '../src/logica/corteLaser.js';
import { validarTramos } from '../src/logica/validaciones.js';
import { calcularRenglon } from '../src/logica/calculoRenglon.js';
import { leerDatos, datosCompletos } from './ayudante.js';

const config = leerDatos('config.json');

test('valores por defecto del corte láser', () => {
  const corte = crearCorteLaser('sinusoidal', config);
  assert.equal(corte.tipo, 'sinusoidal');
  assert.equal(corte.alturaOndaCm, 3.6);
  assert.ok(corte.separacionVallesCm > 0);
  assert.throws(() => crearCorteLaser('triangular', config));
});

test('cara de menos de 3,6 cm con corte láser → AVISO (no bloquea)', () => {
  const tramo = { medidaCm: 3, tipo: 'normal', corteLaser: { tipo: 'sinusoidal', alturaOndaCm: 3.6, separacionVallesCm: 7.6 } };
  const problemas = validarCorteLaser(tramo, 2, config);
  const avisoAncho = problemas.find((p) => p.mensaje.includes('el mínimo es 3,6 cm') && p.mensaje.includes('cara'));
  assert.ok(avisoAncho, 'debería avisar el ancho mínimo de la cara');
  assert.equal(avisoAncho.nivel, 'aviso');
  assert.match(avisoAncho.mensaje, /^Tramo 3:/);
  assert.equal(problemas.filter((p) => p.nivel === 'error').length, 0);
});

test('cara de 3,6 cm justos → sin aviso de ancho', () => {
  const tramo = { medidaCm: '3,6', tipo: 'normal', corteLaser: { tipo: 'trapezoidal', alturaOndaCm: 1, separacionVallesCm: 20 } };
  const problemas = validarCorteLaser(tramo, 0, config);
  assert.equal(problemas.some((p) => p.mensaje.includes('la cara con corte láser')), false);
});

test('altura de onda menor a 3,6 cm → AVISO', () => {
  const tramo = { medidaCm: 12, tipo: 'normal', corteLaser: { tipo: 'sinusoidal', alturaOndaCm: '2,5', separacionVallesCm: 7.6 } };
  const problemas = validarCorteLaser(tramo, 0, config);
  assert.equal(problemas.length, 1);
  assert.equal(problemas[0].nivel, 'aviso');
  assert.match(problemas[0].mensaje, /altura de onda es 2,5 cm; el mínimo es 3,6 cm/);
});

test('onda más alta que la cara → aviso; sin separación → error', () => {
  const tramo = { medidaCm: 4, tipo: 'normal', corteLaser: { tipo: 'sinusoidal', alturaOndaCm: 5, separacionVallesCm: 0 } };
  const problemas = validarCorteLaser(tramo, 0, config);
  assert.ok(problemas.some((p) => p.nivel === 'aviso' && p.mensaje.includes('se come toda la cara')));
  assert.ok(problemas.some((p) => p.nivel === 'error' && p.mensaje.includes('separación')));
});

test('validarTramos incluye los avisos del corte láser', () => {
  const tramos = [
    { medidaCm: 15, tipo: 'normal' },
    { medidaCm: 2, anguloPliegue: 90, sentido: 'derecha', tipo: 'normal', corteLaser: { tipo: 'sinusoidal', alturaOndaCm: 3.6, separacionVallesCm: 7.6 } },
  ];
  const problemas = validarTramos(tramos, config);
  assert.ok(problemas.some((p) => p.nivel === 'aviso' && p.indice === 1));
});

test('borde sinusoidal: arranca en cresta, valle a mitad de paso, termina en el largo', () => {
  const corte = { tipo: 'sinusoidal', alturaOndaCm: 3.6, separacionVallesCm: 8 };
  const borde = generarBordeOndulado(16, corte, config, 8);
  assert.deepEqual(borde[0], { a: 0, h: 0 });
  assert.equal(borde[borde.length - 1].a, 16);
  const valle = borde.find((p) => p.a === 4);
  assert.equal(valle.h, 3.6);
  assert.ok(borde.every((p) => p.h >= 0 && p.h <= 3.6));
});

test('borde trapezoidal: crestas y valles planos, termina en el largo', () => {
  const corte = { tipo: 'trapezoidal', alturaOndaCm: 4, separacionVallesCm: 20 };
  const borde = generarBordeOndulado(50, corte, config);
  assert.deepEqual(borde[0], { a: 0, h: 0 });
  assert.equal(borde[borde.length - 1].a, 50);
  assert.ok(borde.some((p) => p.h === 4));
  assert.ok(borde.every((p) => p.h >= 0 && p.h <= 4));
  // Las posiciones van siempre hacia adelante.
  for (let i = 1; i < borde.length; i++) {
    assert.ok(borde[i].a >= borde[i - 1].a);
  }
});

test('descripción del renglón y texto del corte', () => {
  const plantilla = datosCompletos().catalogo.plantillas.find((p) => p.id === 'cumbrera_sinusoidal_20');
  const renglon = {
    ...plantilla, plantillaId: plantilla.id, parametros: {}, largoCm: 244, materialId: 'galvanizado', calibreId: 'C25',
    terminacion: 'P', colorId: 'rojo_teja', ladoPintura: 'afuera', cantidad: 2,
  };
  const r = calcularRenglon(renglon, datosCompletos());
  assert.equal(r.descripcion, '2,44 mts cumbrera 20x20 c/ corte láser sinusoidal pp rojo teja D40 CH 25');
  assert.equal(r.codigo.codigo, 'CG05P60');
  assert.equal(describirCorteLaser({ tipo: 'sinusoidal', alturaOndaCm: 3.6, separacionVallesCm: 7.6 }),
    'corte láser sinusoidal: onda 3,6 cm, valles cada 7,6 cm (tercerizado)');
});
