import { test } from 'node:test';
import assert from 'node:assert/strict';

import { calcularDesarrollo } from '../src/logica/desarrollo.js';
import { calcularDesarrolloEspecial, validarParametros, parametrosVisibles } from '../src/logica/piezasEspeciales.js';
import { crearRenglonDesdePlantilla, duplicarRenglon, filtrarPlantillas, agruparPlantillas, buscarPlantilla } from '../src/logica/renglones.js';
import { calcularRenglon } from '../src/logica/calculoRenglon.js';
import { validarTramos } from '../src/logica/validaciones.js';
import { calcularGeometria } from '../src/logica/geometria.js';
import { completarTexto, textoDeTramos } from '../src/logica/descripcion.js';
import { armarCodigoGenerico, medidaParaCodigo } from '../src/logica/codigoGenerico.js';
import { crearBoqueta, describirAccesorios, detalleDeAccesorios, validarAccesorios } from '../src/logica/accesoriosCanaleta.js';
import { datosCompletos } from './ayudante.js';

const datos = datosCompletos();
const { config, catalogo, materiales } = datos;
const nuevo = (id) => crearRenglonDesdePlantilla(buscarPlantilla(catalogo, id), config);

test('catálogo: ids únicos, grupos existentes y solo productos de la empresa', () => {
  const ids = catalogo.plantillas.map((p) => p.id);
  assert.equal(new Set(ids).size, ids.length, 'hay ids repetidos');
  const grupos = new Set(catalogo.grupos.map((g) => g.id));
  for (const plantilla of catalogo.plantillas) {
    assert.ok(grupos.has(plantilla.grupo), `${plantilla.id}: grupo desconocido`);
    assert.ok(['plegada', 'especial'].includes(plantilla.tipoPieza));
  }
  for (const id of ['canaleta_nota_real', 'babeta_l_15', 'cumbrera_lisa_20', 'media_cumbrera', 'limahoya', 'tronera',
    'boqueta_suelta', 'tapa_suelta', 'curva_articulada', 'ramal', 'codo_rectangular', 'cano_redondo', 'sombrero_h', 'chapa_lisa', 'pieza_libre']) {
    assert.ok(buscarPlantilla(catalogo, id), `falta ${id}`);
  }
  // Productos que la empresa no publica, fuera del catálogo.
  for (const id of ['cupertina', 'alfeizar', 'perfil_z', 'sombrero_venturi', 'reduccion', 'canaleta_pecho_paloma']) {
    assert.equal(buscarPlantilla(catalogo, id), null, `${id} no debería estar`);
  }
});

test('catálogo: desarrollos de las plantillas plegadas', () => {
  const esperados = {
    canaleta_nota_real: 60, canaleta_americana: 33, babeta_l_15: 30, babeta_l_20: 40,
    babeta_sobre_chapa_sinusoidal: 25, babeta_sobre_chapa_trapezoidal: 25,
    cumbrera_lisa_15: 30, cumbrera_lisa_20: 40, media_cumbrera: 30, limahoya: 52, cenefa_lisa: 24, chapa_lisa: 10,
  };
  for (const [id, desarrollo] of Object.entries(esperados)) {
    assert.equal(calcularDesarrollo(buscarPlantilla(catalogo, id).perfil.tramos), desarrollo, id);
  }
});

test('catálogo: piezas plegadas con tramos válidos', () => {
  for (const plantilla of catalogo.plantillas.filter((p) => p.tipoPieza === 'plegada' && p.id !== 'pieza_libre')) {
    assert.deepEqual(validarTramos(plantilla.perfil.tramos, config).filter((p) => p.nivel === 'error'), [], plantilla.id);
    assert.equal(calcularGeometria(plantilla.perfil, config).segmentos.length, plantilla.perfil.tramos.length);
  }
});

test('catálogo: cada plantilla da un renglón sin errores y con código (de la tabla o genérico)', () => {
  for (const plantilla of catalogo.plantillas.filter((p) => p.id !== 'pieza_libre')) {
    const renglon = crearRenglonDesdePlantilla(plantilla, config);
    const r = calcularRenglon(renglon, datos);
    assert.deepEqual(r.errores, [], `${plantilla.id}: ${r.errores.join(' | ')}`);
    assert.ok(r.codigo.codigo, `${plantilla.id} sin código`);
    assert.ok(!r.descripcion.includes('?'), `${plantilla.id}: descripción incompleta "${r.descripcion}"`);
  }
});

test('buscador de plantillas', () => {
  assert.ok(filtrarPlantillas(catalogo, 'CAÑO').some((p) => p.id === 'cano_redondo'));
  assert.ok(filtrarPlantillas(catalogo, 'salamandra').some((p) => p.id === 'sombrero_canadiense'));
  assert.equal(agruparPlantillas(catalogo)[0].nombre, 'Canaletas');
});

// ---------- código genérico ----------

test('código genérico: chapa lisa 10x10 negra → CL1010N (ejemplo de la empresa)', () => {
  const renglon = { ...nuevo('chapa_lisa'), largoCm: 10, terminacion: 'P', colorId: 'negro' };
  assert.equal(armarCodigoGenerico(renglon.codigoGenerico, renglon, materiales), 'CL1010N');
  const r = calcularRenglon(renglon, datos);
  assert.equal(r.codigo.codigo, 'CL1010N');
  assert.equal(r.codigo.generico, true);
  assert.ok(r.avisos.some((a) => a.startsWith('Código genérico')));
  assert.equal(r.puedeEmitirse, true);
});

test('código genérico: medidas sin coma y letra del material si no es prepintada', () => {
  assert.equal(medidaParaCodigo(7.5), '75');
  assert.equal(medidaParaCodigo(12.5), '125');
  const curva = nuevo('curva_articulada'); // Ø10, 90°, galvanizado natural
  assert.equal(calcularRenglon(curva, datos).codigo.codigo, 'CA1090Z');
  const sombrero = { ...nuevo('sombrero_h'), parametros: { forma: 'rectangular', ladoACm: 20, ladoBCm: 10 } };
  assert.equal(calcularRenglon(sombrero, datos).codigo.codigo, 'SHR2010Z');
  const boqueta = { ...nuevo('boqueta_suelta'), parametros: { forma: 'cuadrada', ladoACm: 10, largoBocaCm: 10, pestanaCm: 2 } };
  assert.equal(calcularRenglon(boqueta, datos).codigo.codigo, 'BQC10Z');
});

test('código genérico: si la tabla tiene una fila para ese elemento, manda la tabla', () => {
  const tabla = [...datos.codigos, { elemento: 'curva', material: 'CG', espesor: '05', terminacion: 'N', banda: 'UN', codigo: 'CURVA-REAL' }];
  const r = calcularRenglon(nuevo('curva_articulada'), { ...datos, codigos: tabla });
  assert.equal(r.codigo.codigo, 'CURVA-REAL');
  assert.equal(r.codigo.generico, false);
});

test('las piezas plegadas comunes siguen buscando en la tabla (no usan código genérico)', () => {
  const r = calcularRenglon({ ...nuevo('canaleta_nota_real'), terminacion: 'P', colorId: 'negro' }, datos);
  assert.equal(r.codigo.codigo, 'CG05P60');
  assert.equal(r.codigo.generico, false);
});

// ---------- tapas y boquetas puestas en la canaleta ----------

test('canaleta con tapas y boquetas: descripción, detalle y validación', () => {
  const canaleta = { ...nuevo('canaleta_nota_real'), terminacion: 'P', colorId: 'negro' };
  assert.deepEqual(canaleta.accesorios, { tapaIzquierda: 'ninguna', tapaDerecha: 'ninguna', boquetas: [] });
  canaleta.accesorios.tapaIzquierda = 'soldada';
  canaleta.accesorios.tapaDerecha = 'soldada';
  canaleta.accesorios.boquetas.push({ ...crearBoqueta(config), forma: 'rectangular', ladoACm: 10, ladoBCm: 5, posicionCm: 60 });
  const r = calcularRenglon(canaleta, datos);
  assert.equal(r.descripcion, '2,44 mts canaleta pp negro D60 CH 25 c/ 2 tapas soldadas y 1 boqueta');
  assert.equal(r.codigo.codigo, 'CG05P60');
  assert.deepEqual(r.errores, []);
  assert.deepEqual(detalleDeAccesorios(canaleta.accesorios), [
    'Tapa izquierda: soldada', 'Tapa derecha: soldada',
    'Boqueta 1: rectangular 10x5, boca 10 cm, centro a 60 cm de la punta izquierda',
  ]);
  assert.equal(describirAccesorios({ tapaIzquierda: 'soldada', tapaDerecha: 'engrampada', boquetas: [] }), 'c/ tapa izq. soldada y tapa der. engrampada');
  assert.equal(describirAccesorios({ tapaIzquierda: 'soldada', tapaDerecha: 'engrampada', boquetas: [{}, {}] }), 'c/ tapa izq. soldada, tapa der. engrampada y 2 boquetas');
});

test('boqueta fuera del largo de la canaleta → error; pegada a la punta → aviso', () => {
  const acc = { tapaIzquierda: 'ninguna', tapaDerecha: 'ninguna', boquetas: [{ ...crearBoqueta(config), posicionCm: 300 }] };
  assert.ok(validarAccesorios(acc, 244, config).some((p) => p.nivel === 'error' && p.mensaje.includes('posición')));
  acc.boquetas[0].posicionCm = 2;
  assert.ok(validarAccesorios(acc, 244, config).some((p) => p.nivel === 'aviso'));
});

// ---------- piezas especiales ----------

test('boqueta suelta: parámetros y desarrollo según la forma', () => {
  const plantilla = buscarPlantilla(catalogo, 'boqueta_suelta');
  assert.deepEqual(parametrosVisibles(plantilla, { forma: 'redonda' }).map((d) => d.id), ['forma', 'diametroCm', 'largoBocaCm', 'pestanaCm']);
  assert.deepEqual(parametrosVisibles(plantilla, { forma: 'rectangular' }).map((d) => d.id), ['forma', 'ladoACm', 'ladoBCm', 'largoBocaCm', 'pestanaCm']);
  assert.equal(calcularDesarrolloEspecial('perimetroSegunForma', { forma: 'redonda', diametroCm: 10 }, config).desarrolloCm, 32.4);
  assert.equal(calcularDesarrolloEspecial('perimetroSegunForma', { forma: 'cuadrada', ladoACm: 10 }, config).desarrolloCm, 41);
  assert.equal(calcularDesarrolloEspecial('perimetroSegunForma', { forma: 'rectangular', ladoACm: 10, ladoBCm: 5 }, config).desarrolloCm, 31);
  const r = calcularRenglon(nuevo('boqueta_suelta'), datos);
  assert.equal(r.descripcion, 'boqueta suelta redonda Ø10 galv D32,4 CH 25');
});

test('sombreros: circulares o rectangulares', () => {
  const circular = calcularRenglon(nuevo('sombrero_canadiense'), datos);
  assert.equal(circular.descripcion, 'sombrero canadiense circular Ø15 galv CH 25');
  const rect = calcularRenglon({ ...nuevo('sombrero_spiro'), parametros: { forma: 'rectangular', ladoACm: 20, ladoBCm: 10 } }, datos);
  assert.equal(rect.descripcion, 'sombrero tipo Spiro rectangular 20x10 galv CH 25');
});

test('fórmulas de piezas especiales (SUPUESTO)', () => {
  assert.equal(calcularDesarrolloEspecial('perimetroRedondo', { diametroCm: 10 }, config).desarrolloCm, 32.4);
  assert.equal(calcularDesarrolloEspecial('perimetroRectangular', { ladoACm: 10, ladoBCm: 5 }, config).desarrolloCm, 31);
  assert.equal(calcularDesarrolloEspecial('unidad', {}, config).porUnidad, true);
});

test('desarrollo corregido a mano queda registrado', () => {
  const r = calcularRenglon({ ...nuevo('cano_redondo'), desarrolloManualCm: '33,5' }, datos);
  assert.equal(r.desarrolloCm, 33.5);
  assert.equal(r.desarrolloEsManual, true);
});

test('parámetros inválidos → error', () => {
  const plantilla = buscarPlantilla(catalogo, 'curva_articulada');
  assert.equal(validarParametros(plantilla, { diametroCm: 0, anguloGrados: 60, gajos: 1 }).length, 3);
});

test('tapa suelta: trae el perfil de la canaleta, se cotiza por unidad', () => {
  const tapa = nuevo('tapa_suelta');
  assert.equal(tapa.perfil.tramos.length, 4);
  const r = calcularRenglon(tapa, datos);
  assert.equal(r.porUnidad, true);
  assert.equal(r.descripcion, 'tapa suelta izquierda canaleta galv CH 25');
  assert.equal(r.codigo.codigo, 'TS60Z');
  const sinPerfil = calcularRenglon({ ...tapa, perfil: { direccionInicial: 'arriba', tramos: [] } }, datos);
  assert.ok(sinPerfil.errores.some((e) => e.startsWith('La tapa necesita')));
});

test('duplicar renglón', () => {
  const original = nuevo('babeta_l_15');
  const copia = duplicarRenglon(original);
  assert.notEqual(copia.id, original.id);
  copia.perfil.tramos[0].medidaCm = 99;
  assert.equal(original.perfil.tramos[0].medidaCm, 15);
});

test('textos: completar parámetros y tramos', () => {
  assert.equal(completarTexto('caño Ø{diametroCm}', {}), 'caño Ø?');
  assert.equal(completarTexto('x {medidas}', { forma: 'cuadrada', ladoACm: 7.5 }), 'x 7,5x7,5');
  assert.equal(textoDeTramos(buscarPlantilla(catalogo, 'canaleta_nota_real').perfil.tramos), '1 (dobl. aplast.) + 20 + 32 + 7 = 60');
  assert.equal(textoDeTramos(buscarPlantilla(catalogo, 'babeta_sobre_chapa_sinusoidal').perfil.tramos), '1 (dobl.) + 12 + 12 (láser sinusoidal) = 25');
});

test('prepintado sin color ni lado de pintura → errores', () => {
  const r = calcularRenglon({ ...nuevo('babeta_l_15'), terminacion: 'P', colorId: null, ladoPintura: null }, datos);
  assert.ok(r.errores.includes('Elegí el color de la chapa prepintada'));
  assert.ok(r.errores.includes('Indicá de qué lado va la pintura (afuera o adentro)'));
});
