import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';

import { buscarCodigo, convertirCsvEnTabla } from '../src/logica/codigos.js';
import { generarCodigosEjemplo } from '../herramientas/generar-codigos-ejemplo.js';
import * as almacenamiento from '../src/datos/almacenamiento.js';
import { leerDatos, crearMotorEnMemoria } from './ayudante.js';

test('la tabla de ejemplo incluye CG05P60 y coincide con el generador', () => {
  const generada = generarCodigosEjemplo(leerDatos('materiales.json'), leerDatos('config.json'));
  assert.ok(generada.some((f) => f.codigo === 'CG05P60'));
  assert.deepEqual(leerDatos('codigos.json'), generada, 'datos/codigos.json está desactualizado: correr npm run generar-codigos');
});

test('una fila para un elemento exacto gana sobre la genérica "*"', () => {
  const tabla = [
    { elemento: '*', material: 'CG', espesor: '05', terminacion: 'P', banda: '60', codigo: 'CG05P60' },
    { elemento: 'cumbrera', material: 'CG', espesor: '05', terminacion: 'P', banda: '60', codigo: 'CUM-0560' },
  ];
  const criterio = { material: 'CG', espesor: '05', terminacion: 'P', banda: 60 };
  assert.equal(buscarCodigo(tabla, { ...criterio, elemento: 'cumbrera' }).codigo, 'CUM-0560');
  assert.equal(buscarCodigo(tabla, { ...criterio, elemento: 'canaleta' }).codigo, 'CG05P60');
  assert.equal(buscarCodigo(tabla, { ...criterio, elemento: 'canaleta', banda: null }).encontrado, false);
});

test('importar CSV con punto y coma (Excel en español)', () => {
  const csv = 'elemento;material;espesor;terminacion;banda;codigo\n*;CG;05;P;60;CG05P60\ncanaleta;CG;05;N;30;\n';
  const { filas, errores } = convertirCsvEnTabla(csv);
  assert.equal(filas.length, 1);
  assert.equal(filas[0].codigo, 'CG05P60');
  assert.equal(errores.length, 1);
  assert.match(convertirCsvEnTabla('a,b\n1,2').errores[0], /Faltan columnas/);
});

// ---------- almacenamiento (con un localStorage falso en memoria) ----------

const sucursales = leerDatos('sucursales.json').sucursales;

beforeEach(() => {
  almacenamiento.configurarAlmacenamiento({
    motor: crearMotorEnMemoria(),
    leerArchivo: async (nombre) => leerDatos(nombre),
  });
});

test('cargar datos base', async () => {
  const datos = await almacenamiento.cargarDatosBase();
  assert.equal(datos.sucursales.length, 10);
  assert.equal(datos.vendedores.length, 30);
  assert.ok(datos.codigos.length > 0);
  assert.ok(datos.glosario.length > 0);
});

test("numeración por sucursal al emitir: Colón 1 y 2, O'Higgins 1", async () => {
  const n1 = await almacenamiento.emitirNota(await almacenamiento.crearNotaVacia({ sucursalId: 'colon', vendedorId: 'v01' }), sucursales);
  const n2 = await almacenamiento.emitirNota(await almacenamiento.crearNotaVacia({ sucursalId: 'colon', vendedorId: 'v01' }), sucursales);
  const n3 = await almacenamiento.emitirNota(await almacenamiento.crearNotaVacia({ sucursalId: 'ohiggins', vendedorId: 'v10' }), sucursales);
  assert.deepEqual([n1.numero, n2.numero, n3.numero], [1, 2, 1]);
  assert.equal(n1.estado, 'emitida');
});

test('el número se asigna al emitir, no al guardar el borrador', async () => {
  const nota = await almacenamiento.crearNotaVacia({ sucursalId: 'colon', vendedorId: 'v01' });
  const borrador = await almacenamiento.guardarBorrador({ ...nota, cliente: 'Cliente A' });
  assert.equal(borrador.numero, null);
  const contadores = await almacenamiento.leerContadores(sucursales);
  assert.equal(contadores.colon, 0);
});

test('último número configurado en 4520 → próxima 4521', async () => {
  await almacenamiento.fijarUltimoNumero(sucursales, 'colon', 4520);
  const emitida = await almacenamiento.emitirNota(await almacenamiento.crearNotaVacia({ sucursalId: 'colon', vendedorId: 'v01' }), sucursales);
  assert.equal(emitida.numero, 4521);
});

test('una nota emitida no se modifica ni se borra ni se emite dos veces', async () => {
  const emitida = await almacenamiento.emitirNota(await almacenamiento.crearNotaVacia({ sucursalId: 'colon', vendedorId: 'v01' }), sucursales);
  await assert.rejects(() => almacenamiento.guardarBorrador(emitida));
  await assert.rejects(() => almacenamiento.borrarBorrador(emitida.id));
  await assert.rejects(() => almacenamiento.emitirNota(emitida, sucursales));
});

test('listar y buscar notas por cliente, número o factura', async () => {
  const a = await almacenamiento.crearNotaVacia({ sucursalId: 'colon', vendedorId: 'v01' });
  await almacenamiento.guardarBorrador({ ...a, cliente: 'Constructora Ejemplo', factura: 'A-0001-0000123' });
  const b = await almacenamiento.crearNotaVacia({ sucursalId: 'ohiggins', vendedorId: 'v10' });
  await almacenamiento.emitirNota({ ...b, cliente: 'Cliente Ficticio', factura: 'B-77' }, sucursales);

  assert.equal((await almacenamiento.listarNotas({ texto: 'constructora' })).length, 1);
  assert.equal((await almacenamiento.listarNotas({ texto: '0000123' })).length, 1);
  assert.equal((await almacenamiento.listarNotas({ sucursalId: 'ohiggins' })).length, 1);
  assert.equal((await almacenamiento.listarNotas({ estado: 'emitida' }))[0].cliente, 'Cliente Ficticio');
  assert.equal((await almacenamiento.listarNotas({ desde: '2999-01-01' })).length, 0);

  await almacenamiento.borrarBorrador(a.id);
  assert.equal((await almacenamiento.listarNotas()).length, 1);
});

test('tabla de códigos importada reemplaza a la de ejemplo (y se puede descartar)', async () => {
  await almacenamiento.guardarTablaCodigos([{ elemento: '*', material: 'CG', espesor: '05', terminacion: 'P', banda: '60', codigo: 'REAL-1' }]);
  assert.equal((await almacenamiento.cargarDatosBase()).codigos[0].codigo, 'REAL-1');
  await almacenamiento.descartarTablaCodigosImportada();
  assert.ok((await almacenamiento.cargarDatosBase()).codigos.length > 1);
});

test('sesión: vendedor y sucursal de hoy (una sesión vieja sin rol es de comercial)', async () => {
  assert.deepEqual(await almacenamiento.leerSesion(), { rol: null, operarioId: null, vendedorId: null, sucursalHoyId: null });
  await almacenamiento.guardarSesion({ vendedorId: 'v01', sucursalHoyId: 'ohiggins' });
  assert.equal((await almacenamiento.leerSesion()).sucursalHoyId, 'ohiggins');
  assert.equal((await almacenamiento.leerSesion()).rol, 'comercial');
});

test('exportar todo y borrar notas de prueba', async () => {
  await almacenamiento.emitirNota(await almacenamiento.crearNotaVacia({ sucursalId: 'colon', vendedorId: 'v01' }), sucursales);
  const copia = await almacenamiento.exportarTodo();
  assert.equal(copia.notas.length, 1);
  assert.equal(copia.contadores.colon, 1);
  await almacenamiento.borrarNotasYContadores();
  assert.equal((await almacenamiento.listarNotas()).length, 0);
  assert.equal((await almacenamiento.leerContadores(sucursales)).colon, 0);
});
