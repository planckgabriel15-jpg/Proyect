import { test } from 'node:test';
import assert from 'node:assert/strict';

import { calcularGeometria, calcularPuntos, puntosATramos, imantarPunto, direccionEnGrados } from '../src/logica/geometria.js';
import { agregarTramoAlInicio, agregarDobladillo, agregarAleta, borrarTramo, insertarTramoAntes, espejarPerfil } from '../src/logica/perfil.js';
import { calcularDesarrollo } from '../src/logica/desarrollo.js';
import { leerDatos } from './ayudante.js';

const config = leerDatos('config.json');

/** Compara dos puntos con tolerancia (las cuentas con decimales no son exactas). */
function cerca(punto, esperado, tolerancia = 0.001) {
  assert.ok(Math.abs(punto.x - esperado.x) < tolerancia && Math.abs(punto.y - esperado.y) < tolerancia,
    `esperaba (${esperado.x}, ${esperado.y}) y dio (${punto.x}, ${punto.y})`);
}

test('dirección inicial: nombres y grados', () => {
  assert.equal(direccionEnGrados('derecha'), 0);
  assert.equal(direccionEnGrados('arriba'), 90);
  assert.equal(direccionEnGrados('izquierda'), 180);
  assert.equal(direccionEnGrados('abajo'), 270);
  assert.equal(direccionEnGrados('45'), 45);
  assert.equal(direccionEnGrados(-90), 270);
});

test('giro a la izquierda con ángulo 90', () => {
  const puntos = calcularPuntos({ direccionInicial: 'derecha', tramos: [
    { medidaCm: 10, tipo: 'normal' },
    { medidaCm: 5, anguloPliegue: 90, sentido: 'izquierda', tipo: 'normal' },
  ] }, config);
  cerca(puntos[2], { x: 10, y: 5 });
});

test('ángulo interior de 120° gira 60°', () => {
  const puntos = calcularPuntos({ direccionInicial: 'derecha', tramos: [
    { medidaCm: 10, tipo: 'normal' },
    { medidaCm: 10, anguloPliegue: 120, sentido: 'izquierda', tipo: 'normal' },
  ] }, config);
  cerca(puntos[2], { x: 10 + 10 * Math.cos(Math.PI / 3), y: 10 * Math.sin(Math.PI / 3) });
});

test('dobladillo al principio: el segundo tramo vuelve 180° con una luz visual chica', () => {
  const geometria = calcularGeometria({ direccionInicial: 'arriba', tramos: [
    { medidaCm: 1, tipo: 'dobladillo_aplastado' },
    { medidaCm: 20, anguloPliegue: 90, sentido: 'derecha', tipo: 'normal' },
  ] }, config);
  // (0,0) → (0,1) → luz a la derecha → baja 20
  cerca(geometria.puntos[1], { x: 0, y: 1 });
  cerca(geometria.puntos[2], { x: config.dibujo.luzDobladilloAplastadoCm, y: 1 });
  cerca(geometria.puntos[3], { x: config.dibujo.luzDobladilloAplastadoCm, y: -19 });
  assert.equal(geometria.pliegues[0].esVuelta, true);
  // La luz NO suma al desarrollo.
  assert.equal(calcularDesarrollo(geometria.segmentos.map((s) => s.tramo)), 21);
});

test('dobladillo al final: el último tramo vuelve 180°', () => {
  const geometria = calcularGeometria({ direccionInicial: 'derecha', tramos: [
    { medidaCm: 10, tipo: 'normal' },
    { medidaCm: 1, sentido: 'izquierda', tipo: 'dobladillo' },
  ] }, config);
  const ultimo = geometria.segmentos[1];
  assert.equal(ultimo.direccion, 180);
  cerca(ultimo.inicio, { x: 10, y: config.dibujo.luzDobladilloAbiertoCm });
});

test('dibujo a mano: puntos → tramos (une segmentos que siguen derecho)', () => {
  const perfil = puntosATramos([
    { x: 0, y: 0 }, { x: 0, y: 5 }, { x: 0, y: 10 }, // dos segmentos en línea = un tramo de 10
    { x: 10, y: 10 },                                 // gira a la derecha 90°
    { x: 10, y: 10 },                                 // punto repetido: se ignora
  ]);
  assert.equal(perfil.direccionInicial, 'arriba');
  assert.equal(perfil.tramos.length, 2);
  assert.equal(perfil.tramos[0].medidaCm, 10);
  assert.equal(perfil.tramos[1].medidaCm, 10);
  assert.equal(perfil.tramos[1].anguloPliegue, 90);
  assert.equal(perfil.tramos[1].sentido, 'derecha');
  // Ida y vuelta: los tramos generan los mismos puntos.
  assert.deepEqual(calcularPuntos(perfil, config), [{ x: 0, y: 0 }, { x: 0, y: 10 }, { x: 10, y: 10 }]);
});

test('dibujo a mano: un giro de 180° se carga como dobladillo', () => {
  const perfil = puntosATramos([{ x: 0, y: 0 }, { x: 10, y: 0 }, { x: 9, y: 0 }]);
  assert.equal(perfil.tramos[1].tipo, 'dobladillo');
});

test('imán: cuadrícula de 1 cm y ángulos de 15°', () => {
  assert.deepEqual(imantarPunto({ x: 2.4, y: 3.6 }, null, config), { x: 2, y: 4 });
  const p = imantarPunto({ x: 10.2, y: 0.9 }, { x: 0, y: 0 }, config); // ~5° → 0°, ~10,2 cm → 10
  cerca(p, { x: 10, y: 0 });
  const q = imantarPunto({ x: 7.3, y: 6.9 }, { x: 0, y: 0 }, config); // ~43° → 45°, ~10 cm
  cerca(q, { x: 10 * Math.cos(Math.PI / 4), y: 10 * Math.sin(Math.PI / 4) });
});

test('agregar tramo al principio no mueve la forma del resto', () => {
  const original = { direccionInicial: 'arriba', tramos: [
    { medidaCm: 10, tipo: 'normal' },
    { medidaCm: 10, anguloPliegue: 90, sentido: 'derecha', tipo: 'normal' },
  ] };
  const nuevo = agregarAleta(original, 'inicio', 3, 90, 'izquierda');
  assert.equal(nuevo.tramos.length, 3);
  const geo = calcularGeometria(nuevo, config);
  // El que era primero sigue yendo hacia arriba y el segundo hacia la derecha.
  assert.equal(geo.segmentos[1].direccion, 90);
  assert.equal(geo.segmentos[2].direccion, 0);
  // El original no se tocó.
  assert.equal(original.tramos.length, 2);
});

test('agregar dobladillo al principio y al final', () => {
  const babeta = { direccionInicial: 'arriba', tramos: [
    { medidaCm: 15, tipo: 'normal' },
    { medidaCm: 15, anguloPliegue: 90, sentido: 'derecha', tipo: 'normal' },
  ] };
  let perfil = agregarDobladillo(babeta, 'inicio', true);
  perfil = agregarDobladillo(perfil, 'fin', false);
  assert.equal(perfil.tramos[0].tipo, 'dobladillo_aplastado');
  assert.equal(perfil.tramos[3].tipo, 'dobladillo');
  assert.equal(calcularDesarrollo(perfil.tramos), 32);
  const geo = calcularGeometria(perfil, config);
  assert.equal(geo.segmentos[1].direccion, 90); // el ala de 15 sigue para arriba
  assert.equal(geo.segmentos[2].direccion, 0);
});

test('borrar el primer tramo conserva la dirección del que queda', () => {
  const perfil = { direccionInicial: 'arriba', tramos: [
    { medidaCm: 10, tipo: 'normal' },
    { medidaCm: 10, anguloPliegue: 90, sentido: 'derecha', tipo: 'normal' },
  ] };
  const nuevo = borrarTramo(perfil, 0, config);
  assert.equal(nuevo.tramos.length, 1);
  assert.equal(nuevo.direccionInicial, 'derecha');
});

test('insertar antes y espejar', () => {
  const perfil = { direccionInicial: 'arriba', tramos: [
    { medidaCm: 10, tipo: 'normal' },
    { medidaCm: 10, anguloPliegue: 90, sentido: 'derecha', tipo: 'normal' },
  ] };
  const insertado = insertarTramoAntes(perfil, 1, { medidaCm: 4 });
  assert.equal(insertado.tramos[1].medidaCm, 4);
  const espejado = espejarPerfil(perfil);
  assert.equal(espejado.tramos[1].sentido, 'izquierda');
  assert.deepEqual(calcularPuntos(espejado, config), [{ x: 0, y: 0 }, { x: 0, y: 10 }, { x: -10, y: 10 }]);
});
