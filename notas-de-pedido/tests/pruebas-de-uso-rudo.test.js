// Errores que aparecieron probando el programa "como un vendedor que quiere romperlo" (14/11/2026).
// Cada prueba reproduce uno y comprueba que ahora está resuelto. Detalle en docs/CAMBIOS.md, "Uso rudo".
import { test } from 'node:test';
import assert from 'node:assert/strict';

import * as almacenamiento from '../src/datos/almacenamiento.js';
import { calcularRenglon } from '../src/logica/calculoRenglon.js';
import { validarNota, avisosDeNota, validarLargo, validarTramos } from '../src/logica/validaciones.js';
import { numeroOTexto, textoDeCantidad } from '../src/logica/numeros.js';
import { crearRenglonDesdePlantilla, buscarPlantilla } from '../src/logica/renglones.js';
import { consumoFisico, explicarDiferencia } from '../src/logica/chapas.js';
import { medidasDibujables } from '../src/logica/fotoCalculo.js';
import { prepararModelo } from '../src/logica/tiempos.js';
import { tiempoDeRenglon } from '../src/logica/tiemposRenglon.js';
import { leerDatos, datosCompletos, crearMotorEnMemoria, renglonCanaletaNotaReal } from './ayudante.js';

const datos = datosCompletos();
const { config, catalogo } = datos;

test('largo fuera de lo razonable: 0,001 m o 99999 m no se pueden emitir', () => {
  const corto = { ...renglonCanaletaNotaReal(), largoCm: 0.1 };
  assert.ok(calcularRenglon(corto, datos).errores.some((e) => e.startsWith('El largo es muy chico')));
  const largo = { ...renglonCanaletaNotaReal(), largoCm: 9999900 };
  const r = calcularRenglon(largo, datos);
  assert.ok(r.errores.some((e) => e.startsWith('El largo es muy grande')));
  assert.ok(r.descripcion.length < 200, 'la descripción no se llena de "2,44 + 2,44 + …"');
  // Lo normal sigue igual: 3 m pide empalme (aviso) y 2,44 m no avisa nada.
  assert.deepEqual(validarLargo(300, config).map((p) => p.nivel), ['aviso']);
  assert.deepEqual(validarLargo(244, config), []);
  assert.deepEqual(validarLargo(3000, config).map((p) => p.nivel), ['aviso'], '30 m es el máximo permitido');
});

test('medida de tramo ínfima (0,0001 cm) no se puede emitir; el dobladillo de 1 cm sí', () => {
  const tramos = renglonCanaletaNotaReal().perfil.tramos;
  tramos[2].medidaCm = 0.0001;
  assert.ok(validarTramos(tramos, config).some((p) => p.nivel === 'error' && p.mensaje === 'Tramo 3: la medida mínima es 0,5 cm'));
  assert.deepEqual(validarTramos(renglonCanaletaNotaReal().perfil.tramos, config).filter((p) => p.nivel === 'error'), []);
});

test('cantidad absurda: 10^20 frena, 1.000 avisa ("¿sobra un cero?"), 200 pasa', () => {
  const r = (cantidad) => calcularRenglon({ ...renglonCanaletaNotaReal(), cantidad }, datos);
  assert.ok(r(1e20).errores.some((e) => e.startsWith('La cantidad es demasiado grande')));
  assert.ok(r(1000).avisos.some((a) => a.includes('sobra un cero')));
  assert.deepEqual(r(1000).errores, []);
  assert.deepEqual(r(200).errores, []);
  assert.ok(!r(200).avisos.some((a) => a.includes('sobra un cero')));
  // También en artículos y servicios.
  const articulo = crearRenglonDesdePlantilla(buscarPlantilla(catalogo, 'compriband'), config);
  articulo.cantidad = 1e9;
  assert.ok(calcularRenglon(articulo, datos).errores.some((e) => e.startsWith('La cantidad es demasiado grande')));
});

test('cantidad escrita con letras: se guarda lo escrito (no "NaN") y la validación lo marca', () => {
  assert.equal(numeroOTexto('diez'), 'diez');
  assert.equal(numeroOTexto('2,5'), 2.5);
  assert.equal(numeroOTexto(' 7 '), 7);
  assert.equal(textoDeCantidad(NaN), '');
  assert.equal(textoDeCantidad(null), '');
  assert.equal(textoDeCantidad(2.5), '2,5');
  assert.equal(textoDeCantidad('diez'), 'diez');
  const renglon = { ...renglonCanaletaNotaReal(), cantidad: numeroOTexto('diez') };
  assert.ok(calcularRenglon(renglon, datos).errores.includes('La cantidad tiene que ser un número entero mayor a 0'));
  // Guardado y leído: sigue diciendo "diez" (JSON convertía NaN en null y el campo mostraba "NaN").
  assert.equal(JSON.parse(JSON.stringify(renglon)).cantidad, 'diez');
});

test('avisos al emitir: entrega ya pasada y factura repetida en otra nota emitida', () => {
  const nota = { id: 'n2', factura: 'A-0001 77', fechaEntrega: '2020-01-01', renglones: [] };
  const otras = [
    { id: 'n1', estado: 'emitida', numero: 15, cliente: 'Gómez', factura: 'a-000177' },
    { id: 'n3', estado: 'borrador', numero: null, factura: 'A-0001-77' },
    { id: 'n4', estado: 'emitida', numero: 9, demo: true, factura: 'A-0001 77' },
  ];
  const avisos = avisosDeNota(nota, otras, '2026-11-14');
  assert.equal(avisos.length, 2);
  assert.match(avisos[0], /01\/01\/2020\) ya pasó/);
  assert.match(avisos[1], /ya está en la nota Nº 15 \(Gómez\)/);
  assert.deepEqual(avisosDeNota({ ...nota, fechaEntrega: '2026-11-20', factura: 'B-1' }, otras, '2026-11-14'), []);
  assert.deepEqual(avisosDeNota({ ...nota, fechaEntrega: null, factura: '' }, otras, '2026-11-14'), []);
  // No frenan: validarNota (lo que bloquea) no cambió.
  assert.equal(validarNota({ sucursalId: 'colon', cliente: 'X', factura: 'A-1', renglones: [renglonCanaletaNotaReal()] }, [calcularRenglon(renglonCanaletaNotaReal(), datos)]).puedeEmitir, true);
});

test('dos ventanas con el mismo borrador: la segunda no pisa a la primera (avisa)', async () => {
  almacenamiento.configurarAlmacenamiento({ motor: crearMotorEnMemoria(), leerArchivo: async (nombre) => leerDatos(nombre) });
  const nueva = await almacenamiento.crearNotaVacia({ sucursalId: 'colon', vendedorId: 'v01' });
  const guardada = await almacenamiento.guardarBorrador({ ...nueva, cliente: 'A' });
  // Las dos ventanas abren la misma versión.
  const ventana1 = JSON.parse(JSON.stringify(guardada));
  const ventana2 = JSON.parse(JSON.stringify(guardada));
  const despues1 = await almacenamiento.guardarBorrador({ ...ventana1, renglones: [renglonCanaletaNotaReal()] });
  await assert.rejects(() => almacenamiento.guardarBorrador({ ...ventana2, cliente: 'B' }), { message: almacenamiento.ERROR_NOTA_CAMBIADA });
  assert.equal((await almacenamiento.leerNota(nueva.id)).renglones.length, 1, 'lo de la ventana 1 sigue');
  // La ventana 1 sigue guardando normalmente, aunque guarde dos veces en el mismo milisegundo.
  const otraVez = await almacenamiento.guardarBorrador({ ...despues1, cliente: 'C' });
  await almacenamiento.guardarBorrador({ ...otraVez, cliente: 'D' });
  assert.equal((await almacenamiento.leerNota(nueva.id)).cliente, 'D');
  // Emitida en otra ventana: error claro.
  const actual = await almacenamiento.leerNota(nueva.id);
  await almacenamiento.emitirNota({ ...actual, factura: 'A-1' }, leerDatos('sucursales.json').sucursales);
  await assert.rejects(() => almacenamiento.guardarBorrador(actual), { message: almacenamiento.ERROR_NOTA_EMITIDA });
});

test('configuración: no deja sucursales sin letra ni con la letra repetida en la misma empresa', async () => {
  // configuracion.js usa el navegador al importarse solo a través de util.js (document): se prueba la función sola.
  globalThis.document ??= { createElement: () => ({}), addEventListener: () => {} };
  const { problemaDeLetras } = await import('../src/pantallas/configuracion.js');
  const sucursales = leerDatos('sucursales.json').sucursales;
  assert.equal(problemaDeLetras(sucursales), null, 'las de fábrica están bien');
  assert.match(problemaDeLetras(sucursales.map((s, i) => (i === 0 ? { ...s, letra: ' ' } : s))), /Falta la letra de Colón/);
  assert.match(problemaDeLetras(sucursales.map((s, i) => (i === 1 ? { ...s, letra: 'c' } : s))), /La letra c está repetida \(Colón y Juan B\. Justo\)/);
  // La misma letra en empresas distintas sí se puede (el prefijo las distingue: AB-H y HI-H).
  assert.equal(problemaDeLetras(sucursales.map((s) => (s.id === 'colon' ? { ...s, letra: 'H' } : s))), null);
});

test('cantidad o largo imposibles no congelan la pantalla (el cálculo de chapa y de tiempo termina enseguida)', () => {
  const modelo = prepararModelo(leerDatos('tiempos-mtm.json'), config);
  for (const cambio of [{ cantidad: 1e20 }, { cantidad: 99999999 }, { largoCm: 9999900 }, { largoCm: 9999900, cantidad: 100000 }]) {
    const renglon = { ...renglonCanaletaNotaReal(), ...cambio };
    const inicio = Date.now();
    const r = calcularRenglon(renglon, datos);
    consumoFisico(renglon, r, config);
    explicarDiferencia(renglon, r, config);
    tiempoDeRenglon(renglon, datos, modelo, r);
    assert.ok(Date.now() - inicio < 500, `${JSON.stringify(cambio)} tardó ${Date.now() - inicio} ms`);
    assert.ok(r.errores.length > 0, `${JSON.stringify(cambio)} tiene que quedar marcado`);
  }
});

test('3D: no se intenta dibujar una pieza sin tramos o con medidas que no son números', () => {
  const ok = renglonCanaletaNotaReal();
  assert.equal(medidasDibujables(ok, calcularRenglon(ok, datos)), true);
  const libre = crearRenglonDesdePlantilla(buscarPlantilla(catalogo, 'pieza_libre'), config);
  assert.equal(medidasDibujables(libre, calcularRenglon(libre, datos)), false);
  const conLetra = renglonCanaletaNotaReal();
  conLetra.perfil.tramos[1].medidaCm = 'x';
  assert.equal(medidasDibujables(conLetra, calcularRenglon(conLetra, datos)), false);
  const sinLargo = { ...renglonCanaletaNotaReal(), largoCm: 'abc' };
  assert.equal(medidasDibujables(sinLargo, calcularRenglon(sinLargo, datos)), false);
  // Un error que no es de medidas (cantidad, material) no impide el dibujo.
  const sinCantidad = { ...renglonCanaletaNotaReal(), cantidad: 0 };
  assert.equal(medidasDibujables(sinCantidad, calcularRenglon(sinCantidad, datos)), true);
});
