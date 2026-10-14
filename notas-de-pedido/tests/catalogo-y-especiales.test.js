import { test } from 'node:test';
import assert from 'node:assert/strict';

import { calcularDesarrollo } from '../src/logica/desarrollo.js';
import { calcularDesarrolloEspecial, validarParametros } from '../src/logica/piezasEspeciales.js';
import { crearRenglonDesdePlantilla, vincularAccesorio, duplicarRenglon, filtrarPlantillas, agruparPlantillas, buscarPlantilla, accesoriosDe } from '../src/logica/renglones.js';
import { calcularRenglon } from '../src/logica/calculoRenglon.js';
import { validarTramos } from '../src/logica/validaciones.js';
import { calcularGeometria } from '../src/logica/geometria.js';
import { completarTexto } from '../src/logica/descripcion.js';
import { datosCompletos } from './ayudante.js';

const datos = datosCompletos();
const { config, catalogo } = datos;

test('catálogo: ids únicos y grupos existentes', () => {
  const ids = catalogo.plantillas.map((p) => p.id);
  assert.equal(new Set(ids).size, ids.length, 'hay ids repetidos');
  const grupos = new Set(catalogo.grupos.map((g) => g.id));
  for (const plantilla of catalogo.plantillas) {
    assert.ok(grupos.has(plantilla.grupo), `${plantilla.id}: grupo desconocido ${plantilla.grupo}`);
    assert.ok(['plegada', 'especial'].includes(plantilla.tipoPieza), `${plantilla.id}: tipoPieza inválido`);
  }
  // Están todos los grupos pedidos en la sección 8.3.
  for (const nombre of ['Canaletas', 'Babetas', 'Cumbreras y limahoyas', 'Boquetas y caños', 'Tapas', 'Ventilación', 'Pieza especial a medida']) {
    assert.ok(catalogo.grupos.some((g) => g.nombre === nombre), `falta el grupo ${nombre}`);
  }
});

test('catálogo: desarrollos de la tabla 7.1', () => {
  const esperados = {
    canaleta_nota_real: 60,
    canaleta_americana_chica: 33,
    canaleta_galponera: 60,
    canaleta_contramuro: 47,
    babeta_l_15: 30,
    babeta_l_20: 40,
    babeta_lateral_15x10: 25,
    babeta_sobre_chapa_lisa: 25,
    babeta_sobre_chapa_sinusoidal: 25,
    babeta_sobre_chapa_trapezoidal: 25,
    cumbrera_lisa_15: 30,
    cumbrera_lisa_20: 40,
    media_cumbrera: 30,
    limahoya: 52,
    cenefa_lisa: 24,
  };
  for (const [id, desarrollo] of Object.entries(esperados)) {
    const plantilla = buscarPlantilla(catalogo, id);
    assert.ok(plantilla, `falta la plantilla ${id}`);
    assert.equal(calcularDesarrollo(plantilla.perfil.tramos), desarrollo, id);
  }
});

test('catálogo: todas las piezas plegadas tienen tramos válidos y se pueden dibujar', () => {
  for (const plantilla of catalogo.plantillas.filter((p) => p.tipoPieza === 'plegada' && p.id !== 'pieza_libre')) {
    const errores = validarTramos(plantilla.perfil.tramos, config).filter((p) => p.nivel === 'error');
    assert.deepEqual(errores, [], plantilla.id);
    const geometria = calcularGeometria(plantilla.perfil, config);
    assert.equal(geometria.segmentos.length, plantilla.perfil.tramos.length, plantilla.id);
  }
});

test('catálogo: cada plantilla crea un renglón que se calcula sin errores (salvo código por unidad)', () => {
  for (const plantilla of catalogo.plantillas) {
    const renglon = crearRenglonDesdePlantilla(plantilla, config);
    const r = calcularRenglon(renglon, datos);
    const erroresEsperables = (mensaje) =>
      mensaje.startsWith('Código no encontrado') ||       // piezas por unidad: sin fila en la tabla de ejemplo
      mensaje.startsWith('La tapa necesita') ||           // tapas sin vincular
      mensaje.startsWith('Agregá al menos un tramo');     // pieza libre vacía
    const erroresRaros = r.errores.filter((e) => !erroresEsperables(e));
    assert.deepEqual(erroresRaros, [], `${plantilla.id}: ${erroresRaros.join(' | ')}`);
    assert.ok(r.descripcion.length > 0);
    if (plantilla.tipoPieza === 'especial') {
      assert.equal(validarParametros(plantilla, renglon.parametros).length, 0, plantilla.id);
    }
  }
});

test('buscador de plantillas: sin tildes ni mayúsculas', () => {
  const resultado = filtrarPlantillas(catalogo, 'CAÑO');
  assert.ok(resultado.some((p) => p.id === 'cano_redondo'));
  const conTilde = filtrarPlantillas(catalogo, 'alfeizar');
  assert.ok(conTilde.some((p) => p.id === 'alfeizar'));
  const grupos = agruparPlantillas(catalogo);
  assert.equal(grupos[0].nombre, 'Canaletas');
});

test('fórmulas de piezas especiales (SUPUESTO)', () => {
  assert.deepEqual(calcularDesarrolloEspecial('perimetroRedondo', { diametroCm: 10 }, config).desarrolloCm, 32.4);
  assert.equal(calcularDesarrolloEspecial('perimetroRectangular', { ladoACm: 10, ladoBCm: 5 }, config).desarrolloCm, 31);
  assert.equal(calcularDesarrolloEspecial('mediaCana', { diametroCm: 12.5, dobladilloCm: 1, pestanaCm: 3 }, config).desarrolloCm, 23.6);
  const unidad = calcularDesarrolloEspecial('unidad', {}, config);
  assert.equal(unidad.porUnidad, true);
  assert.equal(unidad.desarrolloCm, null);
  assert.equal(calcularDesarrolloEspecial('perimetroRedondo', { diametroCm: '' }, config).desarrolloCm, null);
});

test('boqueta redonda Ø10: desarrollo 32,4 → banda 60, código encontrado', () => {
  const plantilla = buscarPlantilla(catalogo, 'boqueta_redonda');
  const renglon = crearRenglonDesdePlantilla(plantilla, config);
  const r = calcularRenglon(renglon, datos);
  assert.equal(r.desarrolloCm, 32.4);
  assert.equal(r.banda.numero, 60);
  assert.equal(r.codigo.codigo, 'CG05N60');
  assert.equal(r.descripcion, 'boqueta redonda Ø10 galv D32,4 CH 25');
});

test('desarrollo corregido a mano queda registrado', () => {
  const plantilla = buscarPlantilla(catalogo, 'cano_redondo');
  const renglon = { ...crearRenglonDesdePlantilla(plantilla, config), desarrolloManualCm: '33,5' };
  const r = calcularRenglon(renglon, datos);
  assert.equal(r.desarrolloCm, 33.5);
  assert.equal(r.desarrolloEsManual, true);
  assert.ok(r.avisos.some((a) => a.includes('corregido a mano')));
});

test('codo: se cotiza por unidad; sin código en la tabla → bloquea salvo "código pendiente"', () => {
  const plantilla = buscarPlantilla(catalogo, 'codo_redondo');
  const renglon = crearRenglonDesdePlantilla(plantilla, config);
  const r = calcularRenglon(renglon, datos);
  assert.equal(r.porUnidad, true);
  assert.equal(r.descripcion, 'codo 90° Ø10 4 gajos galv CH 25');
  assert.equal(r.puedeEmitirse, false);
  const conPendiente = calcularRenglon({ ...renglon, codigoPendiente: true }, datos);
  assert.equal(conPendiente.puedeEmitirse, true);
});

test('parámetros inválidos de una pieza especial → error', () => {
  const plantilla = buscarPlantilla(catalogo, 'codo_redondo');
  const problemas = validarParametros(plantilla, { diametroCm: 0, anguloGrados: 60, gajos: 1 });
  assert.equal(problemas.length, 3);
});

test('tapa vinculada copia el perfil y el material de la canaleta', () => {
  const canaleta = { ...crearRenglonDesdePlantilla(buscarPlantilla(catalogo, 'canaleta_nota_real'), config), terminacion: 'P', colorId: 'negro' };
  const tapa = crearRenglonDesdePlantilla(buscarPlantilla(catalogo, 'tapa_izquierda'), config);
  assert.equal(calcularRenglon(tapa, datos).puedeEmitirse, false); // sin vincular no se puede fabricar
  const vinculada = vincularAccesorio(tapa, canaleta);
  assert.equal(vinculada.vinculadoA, canaleta.id);
  assert.equal(vinculada.perfil.tramos.length, 4);
  assert.equal(vinculada.colorId, 'negro');
  const r = calcularRenglon({ ...vinculada, codigoPendiente: true }, datos);
  assert.equal(r.descripcion, 'tapa izquierda canaleta pp negro CH 25');
  assert.equal(r.puedeEmitirse, true);
  assert.deepEqual(accesoriosDe([canaleta, vinculada], canaleta.id).map((x) => x.id), [vinculada.id]);
});

test('duplicar renglón cambia el id y no comparte el perfil', () => {
  const original = crearRenglonDesdePlantilla(buscarPlantilla(catalogo, 'babeta_l_15'), config);
  const copia = duplicarRenglon(original);
  assert.notEqual(copia.id, original.id);
  copia.perfil.tramos[0].medidaCm = 99;
  assert.equal(original.perfil.tramos[0].medidaCm, 15);
});

test('completar texto de descripción con parámetros', () => {
  assert.equal(completarTexto('reducción Ø{diametroMayorCm} a Ø{diametroMenorCm}', { diametroMayorCm: 15, diametroMenorCm: '12,5' }), 'reducción Ø15 a Ø12,5');
  assert.equal(completarTexto('caño Ø{diametroCm}', {}), 'caño Ø?');
});

test('prepintado sin color ni lado de pintura → errores', () => {
  const renglon = { ...crearRenglonDesdePlantilla(buscarPlantilla(catalogo, 'babeta_l_15'), config), terminacion: 'P', colorId: null, ladoPintura: null };
  const r = calcularRenglon(renglon, datos);
  assert.ok(r.errores.includes('Elegí el color de la chapa prepintada'));
  assert.ok(r.errores.includes('Indicá de qué lado va la pintura (afuera o adentro)'));
});
