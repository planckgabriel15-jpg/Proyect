// Pruebas de las cotas del editor 3D y de las herramientas de edición que usa.
import { test } from 'node:test';
import assert from 'node:assert/strict';

import { cotasDelPerfil, textoCotaTramo, leerValorDeCota } from '../src/logica/cotas.js';
import { insertarTramoDespues, cambiarTramo, agregarTramoEnExtremo } from '../src/logica/perfil.js';
import { calcularGeometria } from '../src/logica/geometria.js';
import { leerDatos } from './ayudante.js';

const config = leerDatos('config.json');
const catalogo = leerDatos('catalogo.json');

const canaletaNotaReal = () => JSON.parse(JSON.stringify(catalogo.plantillas.find((p) => p.id === 'canaleta_nota_real').perfil));
const babetaL = () => ({ direccionInicial: 'derecha', tramos: [
  { medidaCm: 15, tipo: 'normal' },
  { medidaCm: 15, anguloPliegue: 90, sentido: 'izquierda', tipo: 'normal' },
] });

test('cotas: una por tramo, con el mismo texto que el 2D', () => {
  const cotas = cotasDelPerfil(canaletaNotaReal(), config);
  assert.equal(cotas.medidas.length, 4);
  assert.deepEqual(cotas.medidas.map((m) => m.texto), ['1 dobl. aplast.', '20', '32', '7']);
  assert.deepEqual(cotas.medidas.map((m) => m.valor), [1, 20, 32, 7]);
});

test('cotas: la normal es perpendicular al tramo y mide 1', () => {
  for (const m of cotasDelPerfil(canaletaNotaReal(), config).medidas) {
    assert.ok(Math.abs(m.normal.x * m.direccion.x + m.normal.y * m.direccion.y) < 1e-9);
    assert.ok(Math.abs(Math.hypot(m.normal.x, m.normal.y) - 1) < 1e-9);
  }
});

test('cotas: van del lado de AFUERA de la pieza (en la babeta L, abajo y a la derecha)', () => {
  // L: 15 hacia la derecha y 15 hacia arriba (gira a la izquierda) → el exterior es la derecha del recorrido.
  const cotas = cotasDelPerfil(babetaL(), config);
  assert.equal(cotas.ladoExterior, 'derecha');
  assert.deepEqual(cotas.medidas[0].normal, { x: 0, y: -1 }); // el tramo horizontal se acota por abajo
  assert.deepEqual(cotas.medidas[1].normal, { x: 1, y: 0 });  // el vertical, por la derecha
});

test('cotas: ángulos en cada pliegue (menos los dobladillos), con la bisectriz hacia adentro', () => {
  const cotas = cotasDelPerfil(babetaL(), config);
  assert.equal(cotas.angulos.length, 1);
  const angulo = cotas.angulos[0];
  assert.equal(angulo.indice, 1);
  assert.equal(angulo.texto, '90°');
  assert.deepEqual(angulo.vertice, { x: 15, y: 0 });
  // La bisectriz apunta entre "hacia atrás" (izquierda) y "hacia adelante" (arriba).
  assert.ok(angulo.bisectriz.x < 0 && angulo.bisectriz.y > 0);
  assert.equal(Math.abs(angulo.barridoGrados), 90);

  const canaleta = cotasDelPerfil(canaletaNotaReal(), config);
  // El dobladillo del principio (180°) no lleva ángulo: quedan los dos pliegues de 90°.
  assert.deepEqual(canaleta.angulos.map((a) => a.indice), [2, 3]);
});

test('cotas: ángulo de 120° escrito con su valor', () => {
  const perfil = babetaL();
  perfil.tramos[1].anguloPliegue = 120;
  const angulo = cotasDelPerfil(perfil, config).angulos[0];
  assert.equal(angulo.texto, '120°');
  assert.equal(Math.abs(angulo.barridoGrados), 120);
});

test('cotas: las dos puntas libres para el botón "+"', () => {
  const cotas = cotasDelPerfil(babetaL(), config);
  assert.deepEqual(cotas.extremos.map((e) => e.extremo), ['inicio', 'fin']);
  assert.deepEqual(cotas.extremos[0].punto, { x: 0, y: 0 });
  assert.deepEqual(cotas.extremos[0].direccion, { x: -1, y: 0 });
  assert.deepEqual(cotas.extremos[1].punto, { x: 15, y: 15 });
  assert.deepEqual(cotas.extremos[1].direccion, { x: 0, y: 1 });
  assert.deepEqual(cotasDelPerfil({ direccionInicial: 'arriba', tramos: [] }, config).extremos, []);
});

test('cotas: la separación crece con la pieza y nunca es menor a 1 cm', () => {
  assert.equal(cotasDelPerfil(babetaL(), config).separacionCm, 1.8);
  const chica = { direccionInicial: 'arriba', tramos: [{ medidaCm: 2, tipo: 'normal' }] };
  assert.equal(cotasDelPerfil(chica, config).separacionCm, 1);
});

test('texto de la cota de un tramo con corte láser', () => {
  assert.equal(textoCotaTramo({ medidaCm: 7.5, tipo: 'normal', corteLaser: { tipo: 'sinusoidal' } }), '7,5 · láser sinus.');
  assert.equal(textoCotaTramo({ medidaCm: 'x', tipo: 'pestana_engrafe' }), '? engrafe');
});

test('leer el valor escrito en una cota', () => {
  assert.deepEqual(leerValorDeCota('12,5', 'medida', config), { ok: true, valor: 12.5 });
  assert.equal(leerValorDeCota('0', 'medida', config).ok, false);
  assert.equal(leerValorDeCota('abc', 'medida', config).ok, false);
  assert.deepEqual(leerValorDeCota('135', 'angulo', config), { ok: true, valor: 135 });
  assert.match(leerValorDeCota('200', 'angulo', config).mensaje, /entre 1° y 179°/);
  assert.deepEqual(leerValorDeCota('0', 'posicion', config), { ok: true, valor: 0 });
});

test('editar desde el 3D: cambiar la medida de un tramo no toca el original', () => {
  const perfil = babetaL();
  const nuevo = cambiarTramo(perfil, 1, { medidaCm: 25 });
  assert.equal(nuevo.tramos[1].medidaCm, 25);
  assert.equal(perfil.tramos[1].medidaCm, 15);
  assert.deepEqual(cambiarTramo(perfil, 9, { medidaCm: 1 }), perfil); // índice que no existe: no cambia nada
});

test('editar desde el 3D: insertar después y agregar en una punta', () => {
  const perfil = babetaL();
  const despuesDelPrimero = insertarTramoDespues(perfil, 0, { medidaCm: 4 });
  assert.deepEqual(despuesDelPrimero.tramos.map((t) => t.medidaCm), [15, 4, 15]);
  const despuesDelUltimo = insertarTramoDespues(perfil, 1, { medidaCm: 4 });
  assert.deepEqual(despuesDelUltimo.tramos.map((t) => t.medidaCm), [15, 15, 4]);

  // Agregar al inicio no mueve el resto del dibujo.
  const conAleta = agregarTramoEnExtremo(perfil, 'inicio', { medidaCm: 3, anguloPliegue: 90, sentido: 'izquierda' });
  assert.equal(conAleta.tramos.length, 3);
  const antes = calcularGeometria(perfil, config).segmentos[1];
  const despues = calcularGeometria(conAleta, config).segmentos[2];
  assert.ok(Math.abs((antes.fin.x - antes.inicio.x) - (despues.fin.x - despues.inicio.x)) < 1e-6);
  assert.ok(Math.abs((antes.fin.y - antes.inicio.y) - (despues.fin.y - despues.inicio.y)) < 1e-6);
  assert.equal(agregarTramoEnExtremo(perfil, 'fin', { medidaCm: 2 }).tramos[2].medidaCm, 2);
});
