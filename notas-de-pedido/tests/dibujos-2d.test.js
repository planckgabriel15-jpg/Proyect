// Pruebas de los dibujos 2D (SVG). Son texto, así que se prueban sin navegador.
import { test } from 'node:test';
import assert from 'node:assert/strict';

import { svgDelPerfil } from '../src/vistas2d/perfilSvg.js';
import { svgCorteLaser } from '../src/vistas2d/corteLaserSvg.js';
import { svgDeEspecial } from '../src/vistas2d/especialSvg.js';
import { svgPlantaCanaleta } from '../src/vistas2d/plantaCanaletaSvg.js';
import { crearRenglonDesdePlantilla, buscarPlantilla } from '../src/logica/renglones.js';
import { datosCompletos } from './ayudante.js';

const { config, catalogo } = datosCompletos();
const textos = (svg) => [...svg.matchAll(/<text[^>]*>([^<]*)<\/text>/g)].map((m) => m[1]);

test('2D de la canaleta de la nota real: medidas, dobladillo y leyenda', () => {
  const svg = svgDelPerfil(buscarPlantilla(catalogo, 'canaleta_nota_real').perfil, { config, ladoPintura: 'afuera' });
  const t = textos(svg);
  assert.ok(t.includes('1 dobl. aplast.'));
  assert.ok(t.includes('20'));
  assert.ok(t.includes('32'));
  assert.ok(t.includes('7'));
  assert.ok(t.includes('pintura'), 'falta la flecha del lado pintado');
  assert.ok(t.some((x) => x.includes('Pintura AFUERA')), 'la leyenda dice el lado de la pintura (para blanco y negro)');
  assert.ok(t.some((x) => x.includes('EXTERIORES')));
  // Ángulos de 90° no se escriben.
  assert.ok(!t.some((x) => x.endsWith('°')));
  // Un segmento por tramo, con data-tramo para resaltar.
  assert.equal((svg.match(/class="perfil-tramo[^"]*" data-tramo=/g) || []).length, 4);
});

test('2D: el ángulo se escribe cuando no es 90°', () => {
  const svg = svgDelPerfil(buscarPlantilla(catalogo, 'canaleta_americana').perfil, { config });
  assert.ok(textos(svg).includes('100°'));
});

test('2D: tramo resaltado y corte láser marcado', () => {
  const svg = svgDelPerfil(buscarPlantilla(catalogo, 'cumbrera_sinusoidal_20').perfil, { config, resaltado: 1 });
  assert.match(svg, /perfil-tramo[^"]*resaltado[^"]*" data-tramo="1"/);
  assert.ok(textos(svg).some((x) => x.includes('láser sinus.')));
  assert.match(svg, /class="perfil-laser"/);
});

test('2D: perfil vacío y miniatura', () => {
  assert.match(svgDelPerfil({ direccionInicial: 'arriba', tramos: [] }, { config }), /Agregá tramos/);
  const mini = svgDelPerfil(buscarPlantilla(catalogo, 'babeta_l_15').perfil, { config, miniatura: true });
  assert.equal(textos(mini).length, 0, 'la miniatura no lleva textos');
});

test('vista de la cara con corte láser: acota onda, valles y ancho', () => {
  const tramo = { medidaCm: 12, corteLaser: { tipo: 'sinusoidal', alturaOndaCm: 3.6, separacionVallesCm: 7.6 } };
  const t = textos(svgCorteLaser(tramo, 3, 244, config));
  assert.ok(t.some((x) => x.includes('Tramo 3') && x.includes('tercerizado')));
  assert.ok(t.includes('onda 3,6'));
  assert.ok(t.includes('valles cada 7,6'));
  assert.ok(t.includes('12'));
});

test('esquema 2D de todas las piezas especiales (salvo tapas, que usan el perfil)', () => {
  for (const plantilla of catalogo.plantillas.filter((p) => p.tipoPieza === 'especial' && !p.usaPerfil)) {
    const svg = svgDeEspecial(crearRenglonDesdePlantilla(plantilla, config));
    assert.ok(!svg.includes('Sin esquema'), `${plantilla.id} no tiene esquema 2D`);
    assert.ok(!textos(svg).some((x) => x.includes('?')), `${plantilla.id}: hay medidas sin completar`);
  }
});

test('vista desde arriba de la canaleta: tapas y posición de boquetas acotadas', () => {
  const canaleta = crearRenglonDesdePlantilla(buscarPlantilla(catalogo, 'canaleta_nota_real'), config);
  assert.equal(svgPlantaCanaleta(canaleta), '', 'sin tapas ni boquetas no se dibuja');
  canaleta.accesorios.tapaIzquierda = 'engrampada';
  canaleta.accesorios.boquetas.push({ forma: 'cuadrada', ladoACm: 10, largoBocaCm: 10, posicionCm: 60 });
  const t = textos(svgPlantaCanaleta(canaleta));
  assert.ok(t.includes('tapa izq.'));
  assert.ok(t.includes('engrampada'));
  assert.ok(t.includes('B1 10x10'));
  assert.ok(t.includes('60'));
});
