// =============================================================
// Casos de prueba OBLIGATORIOS (sección 11 de la especificación).
// Correr con:  node --test     (o  npm test)
// =============================================================
import { test } from 'node:test';
import assert from 'node:assert/strict';

import { calcularDesarrollo } from '../src/logica/desarrollo.js';
import { calcularBanda } from '../src/logica/banda.js';
import { buscarCodigo } from '../src/logica/codigos.js';
import { leerNumero } from '../src/logica/numeros.js';
import { validarTramos, validarLargo, validarNota } from '../src/logica/validaciones.js';
import { asignarNumeroNP, siguienteNumeroNP } from '../src/logica/numeracion.js';
import { calcularPuntos } from '../src/logica/geometria.js';
import { calcularRenglon } from '../src/logica/calculoRenglon.js';
import { leerDatos, datosCompletos, renglonCanaletaNotaReal } from './ayudante.js';

const config = leerDatos('config.json');
const codigos = leerDatos('codigos.json');

test('1. Tramos 1 (dobl. aplastado) + 20 + 32 + 7 → desarrollo 60', () => {
  const tramos = [
    { medidaCm: 1, tipo: 'dobladillo_aplastado' },
    { medidaCm: 20, tipo: 'normal' },
    { medidaCm: 32, tipo: 'normal' },
    { medidaCm: 7, tipo: 'normal' },
  ];
  assert.equal(calcularDesarrollo(tramos), 60);
});

test('2. Desarrollo 60, galvanizado prepintado, C25 → banda 60 y código CG05P60', () => {
  const banda = calcularBanda(60, config);
  assert.equal(banda.numero, 60);
  const resultado = buscarCodigo(codigos, { elemento: 'canaleta', material: 'CG', espesor: '05', terminacion: 'P', banda: banda.numero });
  assert.equal(resultado.encontrado, true);
  assert.equal(resultado.codigo, 'CG05P60');

  // Y el renglón completo de la nota real da lo mismo.
  const r = calcularRenglon(renglonCanaletaNotaReal(), datosCompletos());
  assert.equal(r.desarrolloCm, 60);
  assert.equal(r.banda.numero, 60);
  assert.equal(r.codigo.codigo, 'CG05P60');
  assert.deepEqual(r.errores, []);
});

test('3. Desarrollo 20 → banda 30', () => {
  assert.equal(calcularBanda(20, config).numero, 30);
});

test('4. Desarrollo 30 → banda 30', () => {
  assert.equal(calcularBanda(30, config).numero, 30);
});

test('5. Desarrollo 30,1 → banda 60', () => {
  assert.equal(calcularBanda(leerNumero('30,1'), config).numero, 60);
});

test('6. Desarrollo 60,5 → banda 120', () => {
  assert.equal(calcularBanda(leerNumero('60,5'), config).numero, 120);
});

test('7. Desarrollo 120 → banda 120', () => {
  assert.equal(calcularBanda(120, config).numero, 120);
});

test('8. Desarrollo 120,1 → sin banda y aviso "Requiere soldar"', () => {
  const banda = calcularBanda(leerNumero('120,1'), config);
  assert.equal(banda.numero, null);
  assert.equal(banda.requiereSoldar, true);
  assert.match(banda.aviso, /Requiere soldar/);
});

test('9. Medida "2,5" (con coma) → se interpreta 2,5', () => {
  assert.equal(leerNumero('2,5'), 2.5);
  assert.equal(calcularDesarrollo([{ medidaCm: '2,5' }, { medidaCm: '7,5' }]), 10);
});

test('10. Tramo con medida 0 → error de validación', () => {
  const problemas = validarTramos([{ medidaCm: 0, anguloPliegue: 90, sentido: 'izquierda', tipo: 'normal' }], config);
  const errores = problemas.filter((p) => p.nivel === 'error');
  assert.equal(errores.length, 1);
  assert.match(errores[0].mensaje, /mayor a 0/);
});

test('11. Largo 2,45 m → aviso de empalme (no bloquea)', () => {
  const problemas = validarLargo(leerNumero('2,45') * 100, config);
  assert.equal(problemas.length, 1);
  assert.equal(problemas[0].nivel, 'aviso');
  assert.match(problemas[0].mensaje, /requiere empalme/);

  // En el renglón completo aparece como aviso y no como error.
  const renglon = { ...renglonCanaletaNotaReal(), largoCm: 245 };
  const r = calcularRenglon(renglon, datosCompletos());
  assert.ok(r.avisos.some((a) => a.includes('requiere empalme')));
  assert.equal(r.puedeEmitirse, true);
});

test('12. Combinación sin código en la tabla → "Código no encontrado" y emisión bloqueada', () => {
  // Usamos una tabla a la que le falta la fila de CG05P60.
  const tablaSinCG05P60 = codigos.filter((f) => f.codigo !== 'CG05P60');
  const datos = { ...datosCompletos(), codigos: tablaSinCG05P60 };
  const r = calcularRenglon(renglonCanaletaNotaReal(), datos);
  assert.equal(r.codigo.encontrado, false);
  assert.ok(r.errores.some((e) => e.includes('Código no encontrado')));

  const nota = { sucursalId: 'colon', cliente: 'Cliente de prueba', factura: '0001-00001234', renglones: [renglonCanaletaNotaReal()] };
  const validacion = validarNota(nota, [r]);
  assert.equal(validacion.puedeEmitir, false);
  assert.ok(validacion.errores.some((e) => e.includes('Código no encontrado')));

  // Si se marca "código pendiente", deja emitir.
  const conPendiente = calcularRenglon({ ...renglonCanaletaNotaReal(), codigoPendiente: true }, datos);
  assert.equal(validarNota(nota, [conPendiente]).puedeEmitir, true);
});

test("13. Dos notas en Colón y una en O'Higgins → Colón 1 y 2; O'Higgins 1", () => {
  let contadores = { colon: 0, ohiggins: 0 };
  const primeraColon = asignarNumeroNP(contadores, 'colon');
  contadores = primeraColon.contadores;
  const segundaColon = asignarNumeroNP(contadores, 'colon');
  contadores = segundaColon.contadores;
  const primeraOhiggins = asignarNumeroNP(contadores, 'ohiggins');

  assert.equal(primeraColon.numero, 1);
  assert.equal(segundaColon.numero, 2);
  assert.equal(primeraOhiggins.numero, 1);
});

test('14. Último número de Colón configurado en 4520 → próxima nota 4521', () => {
  assert.equal(siguienteNumeroNP({ colon: 4520 }, 'colon'), 4521);
});

test('15. Geometría: 10 hacia arriba y 10 con 90° a la derecha → (0,0) → (0,10) → (10,10)', () => {
  const perfil = {
    direccionInicial: 'arriba',
    tramos: [
      { medidaCm: 10, tipo: 'normal' },
      { medidaCm: 10, anguloPliegue: 90, sentido: 'derecha', tipo: 'normal' },
    ],
  };
  assert.deepEqual(calcularPuntos(perfil, config), [
    { x: 0, y: 0 },
    { x: 0, y: 10 },
    { x: 10, y: 10 },
  ]);
});

test('16. Descripción automática → "2,44 mts canaleta pp negro D60 CH 25"', () => {
  const r = calcularRenglon(renglonCanaletaNotaReal(), datosCompletos());
  assert.equal(r.descripcion, '2,44 mts canaleta pp negro D60 CH 25');
});
