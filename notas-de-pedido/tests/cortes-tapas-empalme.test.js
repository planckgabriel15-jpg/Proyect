// Pruebas de cortes en las caras, boquetas de cualquier tipo (en el fondo o en una tapa),
// tapas a medida y empalme de tramos de chapa.
import { test } from 'node:test';
import assert from 'node:assert/strict';

import { crearCorte, huecosEnCaras, validarCortes, describirCortes, detalleDeCortes, huellaDeCorte } from '../src/logica/cortes.js';
import {
  crearBoqueta, normalizarBoqueta, huellaDeBoqueta, nombreDeBoqueta, validarAccesorios, describirAccesorios,
  tapaEntra, ubicarTapa, cambiarMedidasTapa, perfilDeTapa, detalleDeAccesorios,
} from '../src/logica/accesoriosCanaleta.js';
import {
  tramosAutomaticos, tramosIguales, ajustarTramoDeChapa, tramosDeChapa, validarEmpalme, textoEmpalme,
  posicionesDeUniones, necesitaEmpalme, cantidadMinimaDeTramos,
} from '../src/logica/empalme.js';
import { puntoEnPoligono } from '../src/logica/poligonos.js';
import { calcularRenglon } from '../src/logica/calculoRenglon.js';
import { crearRenglonDesdePlantilla, buscarPlantilla } from '../src/logica/renglones.js';
import { copiarPerfil } from '../src/logica/perfil.js';
import { leerDatos } from './ayudante.js';

const datos = {
  config: leerDatos('config.json'),
  materiales: leerDatos('materiales.json'),
  codigos: leerDatos('codigos.json'),
  catalogo: leerDatos('catalogo.json'),
};
const { config } = datos;
const nuevo = (id) => crearRenglonDesdePlantilla(buscarPlantilla(datos.catalogo, id), config);

// ---------- polígonos ----------

test('punto en polígono: adentro, afuera y sobre el borde', () => {
  const cuadrado = [{ x: 0, y: 0 }, { x: 10, y: 0 }, { x: 10, y: 10 }, { x: 0, y: 10 }];
  assert.equal(puntoEnPoligono({ x: 5, y: 5 }, cuadrado), true);
  assert.equal(puntoEnPoligono({ x: 11, y: 5 }, cuadrado), false);
  assert.equal(puntoEnPoligono({ x: 10, y: 5 }, cuadrado), true);
});

// ---------- cortes ----------

test('corte nuevo: va en el fondo de la canaleta, al medio del largo', () => {
  const canaleta = nuevo('canaleta_nota_real'); // 1 dobl. + 20 + 32 (fondo) + 7
  const corte = crearCorte(canaleta, config);
  assert.equal(corte.tramo, 2);
  assert.equal(corte.posicionCm, 122);
  assert.equal(corte.forma, 'redonda');
});

test('corte: huecos en la cara, descripción y detalle', () => {
  const canaleta = nuevo('canaleta_nota_real');
  canaleta.cortes = [{ ...crearCorte(canaleta, config), posicionCm: 60, diametroCm: 10 }];
  const [hueco] = huecosEnCaras(canaleta, config);
  assert.deepEqual({ tramo: hueco.tramo, centroU: hueco.centroU, centroZ: hueco.centroZ }, { tramo: 2, centroU: 16, centroZ: 60 });
  assert.deepEqual(hueco.huella, { forma: 'circulo', diametro: 10 });
  assert.deepEqual(validarCortes(canaleta, config), []);
  const r = calcularRenglon(canaleta, datos);
  assert.equal(r.descripcion, '2,44 mts canaleta galv D60 CH 25 c/ corte Ø10');
  assert.equal(r.desarrolloCm, 60); // el corte no cambia el desarrollo
  assert.match(detalleDeCortes(canaleta, config)[0], /^Corte 1: redondo Ø10 en la cara 3 \(32 cm\), centro a 60 cm de la punta izquierda y a 16 cm del comienzo de la cara$/);
});

test('corte con pared (cuello) en una chapa lisa', () => {
  const chapa = { ...nuevo('chapa_lisa'), largoCm: 50 };
  chapa.perfil.tramos[0].medidaCm = 40;
  chapa.cortes = [{ ...crearCorte(chapa, config), forma: 'rectangular', ladoACm: 12, ladoBCm: 8, paredAlturaCm: 3, paredLado: 'afuera' }];
  assert.deepEqual(huellaDeCorte(chapa.cortes[0]), { forma: 'rect', ancho: 12, alto: 8 });
  assert.deepEqual(validarCortes(chapa, config), []);
  assert.equal(describirCortes(chapa.cortes), 'c/ corte 12x8 c/ pared 3 cm');
  assert.match(detalleDeCortes(chapa, config)[0], /pared de 3 cm hacia afuera$/);
  assert.equal(describirCortes([{ forma: 'redonda', diametroCm: 5 }, { forma: 'cuadrada', ladoACm: 4 }]), 'c/ 2 cortes (Ø5, 4x4)');
});

test('corte que no entra en la cara o en el largo → error', () => {
  const canaleta = nuevo('canaleta_nota_real');
  canaleta.cortes = [{ ...crearCorte(canaleta, config), tramo: 3, diametroCm: 10 }]; // la cara 4 mide 7 cm
  assert.ok(validarCortes(canaleta, config).some((p) => /no entra a lo ancho de la cara 4/.test(p.mensaje)));
  canaleta.cortes = [{ ...crearCorte(canaleta, config), posicionCm: 2 }];
  assert.ok(validarCortes(canaleta, config).some((p) => /no entra a lo largo/.test(p.mensaje)));
  canaleta.cortes = [{ ...crearCorte(canaleta, config), tramo: 9 }];
  assert.ok(validarCortes(canaleta, config).some((p) => /ya no existe/.test(p.mensaje)));
  assert.equal(calcularRenglon(canaleta, datos).puedeEmitirse, false);
});

// ---------- boquetas ----------

test('boqueta en el fondo: también corta la chapa', () => {
  const canaleta = nuevo('canaleta_nota_real');
  canaleta.accesorios.boquetas.push({ ...crearBoqueta(config), posicionCm: 60 });
  const huecos = huecosEnCaras(canaleta, config);
  assert.equal(huecos.length, 1);
  assert.deepEqual(huecos[0].origen, { tipo: 'boqueta', indice: 0 });
  assert.equal(huecos[0].tramo, 2);
  assert.equal(huecos[0].centroZ, 60);
});

test('boqueta: los tipos que se venden sueltos, con su código', () => {
  const canaleta = nuevo('canaleta_nota_real');
  canaleta.accesorios.boquetas = [
    { ...crearBoqueta(config), posicionCm: 40 },
    { ...crearBoqueta(config), tipo: 'tronera', bocaACm: 20, bocaBCm: 10, diametroSalidaCm: 10, posicionCm: 120 },
    { ...crearBoqueta(config), tipo: 'colector_recto', ladoACm: 10, ladoBCm: 5, posicionCm: 200 },
  ];
  const r = calcularRenglon(canaleta, datos);
  assert.deepEqual(r.errores, []);
  assert.deepEqual(r.codigosAdicionales.map((c) => [c.codigo, c.descripcion]), [
    ['BQ10Z', 'boqueta redonda Ø10'],
    ['TR201010Z', 'tronera 20x10 salida Ø10'],
    ['COL510', 'colector recto 10x5'],
  ]);
  assert.match(r.descripcion, /c\/ 1 boqueta, 1 tronera y 1 colector recto$/);
  assert.deepEqual(huellaDeBoqueta(canaleta.accesorios.boquetas[1]), { forma: 'rect', ancho: 20, alto: 10 });
  assert.equal(nombreDeBoqueta({ tipo: 'boqueta', forma: 'cuadrada', ladoACm: 8 }), 'boqueta cuadrada 8x8');
  // Una boqueta guardada antes (sin tipo ni ubicación) se completa sola.
  assert.deepEqual([normalizarBoqueta({ forma: 'redonda' }, config).tipo, normalizarBoqueta({}, config).ubicacion], ['boqueta', 'fondo']);
});

test('boqueta en la tapa: necesita la tapa y tiene que entrar en ella', () => {
  const canaleta = nuevo('canaleta_nota_real');
  canaleta.accesorios.boquetas = [{ ...crearBoqueta(config), ubicacion: 'tapaDerecha', diametroCm: 10, alturaCm: 7 }];
  assert.ok(validarAccesorios(canaleta.accesorios, 244, config, canaleta).some((p) => /no tiene tapa derecha/.test(p.mensaje)));
  canaleta.accesorios.tapaDerecha = 'soldada';
  assert.deepEqual(validarAccesorios(canaleta.accesorios, 244, config, canaleta), []);
  // Más alta que la tapa (la canaleta tiene 20 cm de frente y 7 de atrás) → no entra.
  canaleta.accesorios.boquetas[0].alturaCm = 18;
  assert.ok(validarAccesorios(canaleta.accesorios, 244, config, canaleta).some((p) => /no entra en la tapa derecha/.test(p.mensaje)));
  // En la tapa no corta el fondo.
  assert.deepEqual(huecosEnCaras(canaleta, config), []);
  assert.match(detalleDeAccesorios({ ...canaleta.accesorios, boquetas: [{ ...canaleta.accesorios.boquetas[0], alturaCm: 6, desplazamientoCm: -4 }] }, canaleta, config)[1],
    /en la tapa derecha: centro a 6 cm del fondo, corrida -4 cm del medio$/);
});

// ---------- tapas a medida ----------

test('tapa a medida: más baja que la canaleta entra; más grande no', () => {
  const canaleta = nuevo('canaleta_nota_real'); // 1 + 20 + 32 + 7
  canaleta.accesorios.tapaIzquierda = 'soldada';
  const baja = copiarPerfil(canaleta.perfil);
  baja.tramos[1].medidaCm = 12; // el frente baja de 20 a 12
  canaleta.accesorios = cambiarMedidasTapa(canaleta.accesorios, 'izquierda', { aMedida: true, perfil: baja });
  assert.equal(tapaEntra(canaleta, 'izquierda', config).entra, true);
  assert.equal(ubicarTapa(canaleta, 'izquierda', config).dy, -8); // se baja hasta apoyar en el fondo
  assert.equal(perfilDeTapa(canaleta, 'izquierda', config), baja);

  const ancha = copiarPerfil(canaleta.perfil);
  ancha.tramos[2].medidaCm = 40; // fondo más ancho que la canaleta
  canaleta.accesorios = cambiarMedidasTapa(canaleta.accesorios, 'izquierda', { perfil: ancha });
  const revision = tapaEntra(canaleta, 'izquierda', config);
  assert.equal(revision.entra, false);
  assert.match(revision.mensaje, /no entra en la canaleta/);
  assert.ok(calcularRenglon(canaleta, datos).errores.some((e) => /no entra en la canaleta/.test(e)));
});

test('tapa a medida: factura con el código de su propio perfil y se describe', () => {
  const canaleta = nuevo('canaleta_nota_real');
  canaleta.accesorios.tapaIzquierda = 'soldada';
  canaleta.accesorios.tapaDerecha = 'soldada';
  const baja = copiarPerfil(canaleta.perfil);
  baja.tramos[1].medidaCm = 12; // 1 + 12 + 32 + 7 = 52
  canaleta.accesorios = cambiarMedidasTapa(canaleta.accesorios, 'derecha', { aMedida: true, perfil: baja, pestanaCm: 2 });
  const r = calcularRenglon(canaleta, datos);
  assert.deepEqual(r.codigosAdicionales.map((c) => [c.codigo, c.cantidad]), [['TS60Z', 1], ['TS52Z', 1]]);
  assert.match(r.descripcion, /c\/ tapa izq\. soldada y tapa der\. soldada a medida$/);
  assert.equal(detalleDeAccesorios(canaleta.accesorios, canaleta, config)[1], 'Tapa derecha: soldada, a medida (1 + 12 + 32 + 7 = 52 cm), pestaña 2 cm');
  assert.equal(describirAccesorios({ tapaIzquierda: 'soldada', tapaDerecha: 'soldada', boquetas: [] }), 'c/ 2 tapas soldadas');
});

// ---------- empalme ----------

test('empalme automático: 3 m → 2,44 + 0,56 (ejemplo del área comercial)', () => {
  assert.deepEqual(tramosAutomaticos(300, 244), [244, 56]);
  assert.deepEqual(tramosAutomaticos(600, 244), [244, 244, 112]);
  assert.deepEqual(tramosAutomaticos(244, 244), [244]);
  assert.equal(cantidadMinimaDeTramos(489, 244), 3);
  assert.equal(textoEmpalme([244, 56]), '2 tramos de chapa: 2,44 + 0,56 m');
  assert.equal(textoEmpalme([200]), '');
  assert.deepEqual(posicionesDeUniones([244, 56]), [244]);
});

test('empalme en partes iguales y a mano: 3 m → 1,50 + 1,50, o lo que pida el cliente', () => {
  assert.deepEqual(tramosIguales(300, 244), [150, 150]);
  assert.deepEqual(tramosIguales(300, 244, 3), [100, 100, 100]);
  assert.deepEqual(tramosIguales(300, 244, 1), [150, 150]); // menos de 2 no alcanza
  assert.deepEqual(tramosIguales(100, 244, 3), [33.3, 33.3, 33.4]);
  // A mano: se cambia uno y el último completa el largo.
  assert.deepEqual(ajustarTramoDeChapa([244, 56], 0, 180, 300), [180, 120]);
  assert.deepEqual(ajustarTramoDeChapa([100, 100, 100], 2, 50, 300), [100, 150, 50]);
});

test('empalme en el renglón: descripción, aviso y errores', () => {
  const canaleta = { ...nuevo('canaleta_nota_real'), largoCm: 300 };
  assert.equal(necesitaEmpalme(canaleta, config), true);
  let r = calcularRenglon(canaleta, datos);
  assert.deepEqual(r.empalme.tramosCm, [244, 56]);
  assert.equal(r.descripcion, '3,00 mts canaleta galv D60 CH 25 empalme 2,44 + 0,56');
  assert.ok(r.avisos.some((a) => a.includes('requiere empalme')));
  assert.deepEqual(r.errores, []);

  canaleta.empalme = { modo: 'iguales' };
  assert.deepEqual(tramosDeChapa(canaleta, config), [150, 150]);
  canaleta.empalme = { modo: 'manual', tramosCm: [250, 50] };
  assert.ok(validarEmpalme(canaleta, config).some((p) => /tramo de chapa 1 mide 2,50 m/.test(p.mensaje)));
  canaleta.empalme = { modo: 'manual', tramosCm: [150, 100] };
  r = calcularRenglon(canaleta, datos);
  assert.ok(r.errores.some((e) => /suman 2,50 m y la pieza mide 3,00 m/.test(e)));
  // Una pieza corta va en un solo tramo, salvo que se pida otra cosa.
  const corta = nuevo('canaleta_nota_real');
  assert.deepEqual(tramosDeChapa(corta, config), [244]);
  assert.equal(calcularRenglon(corta, datos).empalme, null);
  corta.empalme = { modo: 'iguales', cantidad: 2 };
  assert.deepEqual(tramosDeChapa(corta, config), [122, 122]);
});

// ---------- más medidas ajustables ----------

test('medidas ajustables nuevas: vienen cargadas, son opcionales y se validan si se escriben', async () => {
  const { validarParametros } = await import('../src/logica/piezasEspeciales.js');
  const sombrero = nuevo('sombrero_chino');
  assert.deepEqual([sombrero.parametros.altoCanoCm, sombrero.parametros.alaCm, sombrero.parametros.altoTechoCm], [25, 7, 9]);
  assert.equal(nuevo('ramal').parametros.largoRamalCm, 25);
  const plantilla = buscarPlantilla(datos.catalogo, 'curva_articulada');
  // Un renglón guardado antes (sin radio) sigue siendo válido.
  assert.deepEqual(validarParametros(plantilla, { diametroCm: 10, anguloGrados: 90, gajos: 4 }), []);
  assert.equal(validarParametros(plantilla, { diametroCm: 10, anguloGrados: 90, gajos: 4, radioCurvaCm: -3 }).length, 1);
});

// ---------- dibujos 2D ----------

test('dibujos 2D: cara con cortes, tapa a medida y medidas de los sombreros', async () => {
  const { svgCaras, svgTapa, svgTapasConDetalle } = await import('../src/vistas2d/carasSvg.js');
  const { svgDeEspecial } = await import('../src/vistas2d/especialSvg.js');
  const canaleta = nuevo('canaleta_nota_real');
  assert.equal(svgCaras(canaleta, config), '');
  canaleta.cortes = [{ ...crearCorte(canaleta, config), posicionCm: 70 }];
  canaleta.accesorios.boquetas.push({ ...crearBoqueta(config), posicionCm: 25 });
  const caras = svgCaras(canaleta, config);
  assert.match(caras, /Cara 3 \(32 cm\)/);
  assert.match(caras, /C1 Ø10/);
  assert.match(caras, /B1 Ø10/);
  assert.equal(svgTapa(canaleta, 'izquierda', config), ''); // sin tapa
  canaleta.accesorios.tapaIzquierda = 'soldada';
  assert.equal(svgTapasConDetalle(canaleta, config), ''); // tapa común: no hace falta dibujarla aparte
  canaleta.accesorios = cambiarMedidasTapa(canaleta.accesorios, 'izquierda', { aMedida: true, perfil: copiarPerfil(canaleta.perfil) });
  assert.match(svgTapasConDetalle(canaleta, config), /Tapa izquierda a medida/);
  const sombrero = svgDeEspecial(nuevo('sombrero_chino'));
  assert.match(sombrero, /alto caño: 25 cm/);
  assert.doesNotMatch(sombrero, /&lt;/); // ninguna etiqueta quedó escrita como texto
});
