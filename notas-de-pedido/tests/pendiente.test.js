// Pruebas de los plegados con pendiente (el perfil cambia de una punta a la otra).
import { test } from 'node:test';
import assert from 'node:assert/strict';

import { perfilFinal, activarPendiente, calcularPendiente, validarPendiente, tienePendiente, medidaFinal } from '../src/logica/pendiente.js';
import { calcularRenglon } from '../src/logica/calculoRenglon.js';
import { crearRenglonDesdePlantilla, buscarPlantilla } from '../src/logica/renglones.js';
import { insertarTramoAntes } from '../src/logica/perfil.js';
import { leerDatos } from './ayudante.js';

const datos = {
  config: leerDatos('config.json'),
  materiales: leerDatos('materiales.json'),
  codigos: leerDatos('codigos.json'),
  catalogo: leerDatos('catalogo.json'),
};

/** Canaleta de la nota real (1 dobl. aplastado + 20 + 32 + 7 = 60) con pendiente: el frente pasa de 20 a 25. */
function canaletaConPendiente() {
  const renglon = crearRenglonDesdePlantilla(buscarPlantilla(datos.catalogo, 'canaleta_nota_real'), datos.config);
  renglon.conPendiente = true;
  renglon.perfil = activarPendiente(renglon.perfil);
  renglon.perfil.tramos[1].medidaFinalCm = 25;
  return renglon;
}

test('pendiente: por defecto las piezas no tienen pendiente', () => {
  const renglon = crearRenglonDesdePlantilla(buscarPlantilla(datos.catalogo, 'canaleta_nota_real'), datos.config);
  assert.equal(renglon.conPendiente, false);
  assert.equal(tienePendiente(renglon), false);
});

test('pendiente: al prenderla, la punta final copia las medidas del inicio', () => {
  const perfil = activarPendiente({ direccionInicial: 'arriba', tramos: [{ medidaCm: 10, anguloPliegue: 90 }, { medidaCm: 5, anguloPliegue: 120 }] });
  assert.deepEqual(perfil.tramos.map((t) => [t.medidaFinalCm, t.anguloPliegueFinal]), [[10, 90], [5, 120]]);
});

test('pendiente: perfil final con las medidas finales (y las del inicio donde no hay)', () => {
  const renglon = canaletaConPendiente();
  const final = perfilFinal(renglon.perfil);
  assert.deepEqual(final.tramos.map((t) => t.medidaCm), [1, 25, 32, 7]);
  assert.equal(final.tramos[1].medidaFinalCm, undefined);
  // Un tramo insertado después (sin valor final) es igual en las dos puntas.
  const conNuevo = insertarTramoAntes(renglon.perfil, 3, { medidaCm: 4 });
  assert.equal(medidaFinal(conNuevo.tramos[3]), 4);
});

test('pendiente: desarrollo = el mayor de los dos y cuánto baja el fondo', () => {
  const calculo = calcularPendiente(canaletaConPendiente(), datos.config);
  assert.equal(calculo.desarrolloInicialCm, 60);
  assert.equal(calculo.desarrolloFinalCm, 65);
  assert.equal(calculo.desarrolloCm, 65);
  assert.equal(calculo.bajadaCm, 5);              // el frente es 5 cm más alto → el fondo baja 5 cm
  assert.equal(calculo.milimetrosPorMetro, 20.5); // 50 mm en 2,44 m
  assert.equal(calculo.relacion, '1:49');
  assert.equal(calculo.texto, 'baja 5 cm en 2,44 m (20,5 mm/m · 1:49)');
});

test('pendiente: el renglón cotiza por el desarrollo mayor y lo dice en la descripción', () => {
  const renglon = canaletaConPendiente();
  const resultado = calcularRenglon(renglon, datos);
  assert.equal(resultado.desarrolloCm, 65);
  assert.equal(resultado.banda.numero, 120); // 65 cm ya no entra en 1/2 chapa
  assert.equal(resultado.descripcion, '2,44 mts canaleta galv D65 CH 25 con pendiente D60 a D65');
  assert.ok(resultado.pendiente);
  // Sin pendiente vuelve a ser la nota real: CG05N60, D60.
  renglon.conPendiente = false;
  const sinPendiente = calcularRenglon(renglon, datos);
  assert.equal(sinPendiente.desarrolloCm, 60);
  assert.equal(sinPendiente.pendiente, null);
});

test('pendiente: avisa si las dos puntas son iguales y marca medidas finales que faltan', () => {
  const renglon = canaletaConPendiente();
  renglon.perfil.tramos[1].medidaFinalCm = 20;
  assert.match(validarPendiente(renglon, datos.config).map((p) => p.mensaje).join(), /las dos puntas son iguales/);
  renglon.perfil.tramos[2].medidaFinalCm = 'x';
  renglon.perfil.tramos[3].anguloPliegueFinal = 200;
  const problemas = validarPendiente(renglon, datos.config);
  assert.ok(problemas.some((p) => p.nivel === 'error' && p.indice === 2 && /punta final/.test(p.mensaje)));
  assert.ok(problemas.some((p) => p.nivel === 'error' && p.indice === 3 && /ángulo/.test(p.mensaje)));
  assert.equal(calcularRenglon(renglon, datos).puedeEmitirse, false);
});

test('pendiente: si sube en vez de bajar, lo dice', () => {
  const renglon = canaletaConPendiente();
  renglon.perfil.tramos[1].medidaFinalCm = 18;
  assert.match(calcularPendiente(renglon, datos.config).texto, /^sube 2 cm/);
});

test('pendiente: cada tapa factura con el código de su punta (TS60 a la izquierda, TS65 a la derecha)', () => {
  const renglon = canaletaConPendiente();
  renglon.accesorios.tapaIzquierda = 'soldada';
  renglon.accesorios.tapaDerecha = 'engrampada';
  renglon.cantidad = 2;
  const extras = calcularRenglon(renglon, datos).codigosAdicionales;
  assert.deepEqual(extras.map((e) => [e.codigo, e.descripcion, e.cantidad]), [
    ['TS60Z', 'tapa izq. soldada', 2],
    ['TS65Z', 'tapa der. engrampada', 2],
  ]);
  // Sin pendiente vuelven a ir juntas.
  renglon.conPendiente = false;
  assert.deepEqual(calcularRenglon(renglon, datos).codigosAdicionales.map((e) => [e.codigo, e.cantidad]), [['TS60Z', 4]]);
});
