// Rediseño para el comercial (etapa D): lo que el programa recuerda del vendedor, repetir una nota,
// lo que falta para emitir (con su lugar) y la hoja impresa sin datos repetidos.
import { test } from 'node:test';
import assert from 'node:assert/strict';

import * as almacenamiento from '../src/datos/almacenamiento.js';
import { preferenciasVacias, registrarUso, materialPorDefecto, aplicarMaterial, recientesYFrecuentes, clientesConocidos, MAXIMO_RECIENTES } from '../src/logica/preferencias.js';
import { crearRenglonDesdePlantilla, buscarPlantilla, datosParaRepetir } from '../src/logica/renglones.js';
import { calcularRenglon } from '../src/logica/calculoRenglon.js';
import { fotoDelCalculo } from '../src/logica/fotoCalculo.js';
import { validarNota, faltantesDeNota } from '../src/logica/validaciones.js';
import { armarHoja, armarRenglonDeHoja, fichaDeMaterial, textosDeRenglon, llevaDibujo } from '../src/logica/hojaImpresa.js';
import { dibujosDeRenglon, textosDeSvg } from '../src/vistas2d/hojaSvg.js';
import { plantillasVisibles } from '../src/logica/empresas.js';
import { prepararModelo } from '../src/logica/tiempos.js';
import { tiempoDeNota } from '../src/logica/tiemposRenglon.js';
import { armarTrabajos } from '../src/logica/produccion.js';
import { leerDatos, datosCompletos, crearMotorEnMemoria, renglonCanaletaNotaReal } from './ayudante.js';

const datos = datosCompletos();
const { catalogo, config, materiales } = datos;
const nuevo = (id) => crearRenglonDesdePlantilla(buscarPlantilla(catalogo, id), config);
const contar = (textos, patron) => textos.filter((t) => patron.test(t)).length;

/** Caso 1 del diagnóstico: canaleta de 2,44 m, prepintada negra, tapa izquierda soldada, derecha engrampada y una boqueta. */
function canaletaConTapasYBoqueta() {
  const r = nuevo('canaleta_nota_real');
  Object.assign(r, { id: 'r1', terminacion: 'P', colorId: 'negro', ladoPintura: 'afuera', largoCm: 244, cantidad: 1 });
  r.accesorios.tapaIzquierda = 'soldada';
  r.accesorios.tapaDerecha = 'engrampada';
  r.accesorios.boquetas.push({ ...config.accesoriosCanaleta.boquetaPorDefecto, posicionCm: 30 });
  return r;
}
function notaCon(renglones, extra = {}) {
  return { id: 'n1', estado: 'borrador', numero: null, sucursalId: 'colon', empresaId: 'abasto', vendedorId: 'v01', cliente: 'Cliente', factura: 'A-1', fechaCreacion: '2026-11-13T12:52:00', mostrar3d: 'auto', renglones, ...extra };
}

// ---------- lo que se recuerda del vendedor ----------

test('preferencias: se recuerda el último material y arranca con el de la pieza anterior de la nota', () => {
  let pref = preferenciasVacias();
  assert.equal(materialPorDefecto(notaCon([]), pref, materiales), null, 'la primera vez no hay nada que recordar');
  const canaleta = { ...renglonCanaletaNotaReal(), calibreId: 'C27', terminacion: 'P', colorId: 'rojo_teja', ladoPintura: 'adentro' };
  pref = registrarUso(pref, canaleta);
  assert.deepEqual(pref.material, { materialId: 'galvanizado', calibreId: 'C27', terminacion: 'P', colorId: 'rojo_teja', ladoPintura: 'adentro' });
  // Nota nueva: el último del vendedor.
  assert.equal(materialPorDefecto(notaCon([]), pref, materiales).origen, 'vendedor');
  const babeta = aplicarMaterial(nuevo('babeta_l_15'), materialPorDefecto(notaCon([]), pref, materiales));
  assert.deepEqual([babeta.calibreId, babeta.terminacion, babeta.colorId, babeta.ladoPintura], ['C27', 'P', 'rojo_teja', 'adentro']);
  assert.deepEqual(calcularRenglon(babeta, datos).errores, [], 'el material recordado da una pieza válida');
  // En la misma nota manda la pieza anterior (aunque el vendedor haya usado otra cosa en otra nota).
  const otra = { ...renglonCanaletaNotaReal(), calibreId: 'C25', terminacion: 'N', colorId: null };
  const deLaNota = materialPorDefecto(notaCon([otra, nuevo('compriband')]), pref, materiales);
  assert.equal(deLaNota.origen, 'nota');
  assert.deepEqual([deLaNota.calibreId, deLaNota.terminacion], ['C25', 'N']);
  // Un artículo no lleva material: ni se le pone ni cambia lo recordado.
  const articulo = aplicarMaterial(nuevo('compriband'), pref.material);
  assert.equal(articulo.sinMaterial, true);
  assert.deepEqual(registrarUso(pref, articulo).material, pref.material);
  // Si el color recordado ya no existe en la lista, no se usa (queda el valor por defecto).
  assert.equal(materialPorDefecto(notaCon([]), { material: { ...pref.material, colorId: 'color_borrado' } }, materiales), null);
  // No modifica el objeto recibido.
  const copia = JSON.parse(JSON.stringify(pref));
  registrarUso(pref, canaleta);
  assert.deepEqual(pref, copia);
});

test('preferencias: recientes (lo último primero, sin repetir) y frecuentes (lo más usado)', () => {
  let pref = preferenciasVacias();
  for (const id of ['canaleta_nota_real', 'babeta_l_15', 'canaleta_nota_real', 'compriband', 'canaleta_nota_real', 'babeta_l_15']) pref = registrarUso(pref, nuevo(id));
  assert.deepEqual(pref.recientes, ['babeta_l_15', 'canaleta_nota_real', 'compriband']);
  assert.deepEqual(pref.usos, { canaleta_nota_real: 3, babeta_l_15: 2, compriband: 1 });
  const visibles = plantillasVisibles(catalogo, 'abasto');
  let listas = recientesYFrecuentes(pref, visibles, 2);
  assert.deepEqual(listas.recientes.map((p) => p.id), ['babeta_l_15', 'canaleta_nota_real']);
  assert.deepEqual(listas.frecuentes.map((p) => p.id), [], 'lo que ya está en recientes no se repite en frecuentes');
  listas = recientesYFrecuentes(pref, visibles, 1);
  assert.deepEqual(listas.frecuentes.map((p) => p.id), ['canaleta_nota_real']);
  // Solo lo que el vendedor puede ver ahora (un vendedor de G-TEC no ve los plegados de Abasto).
  assert.deepEqual(recientesYFrecuentes(pref, plantillasVisibles(catalogo, 'gtec')).recientes, []);
  // Tope de recientes.
  for (const p of catalogo.plantillas.slice(0, 30)) pref = registrarUso(pref, crearRenglonDesdePlantilla(p, config));
  assert.equal(pref.recientes.length, MAXIMO_RECIENTES);
  // La última boqueta cargada (forma y medidas, no la posición).
  const conBoqueta = nuevo('canaleta_nota_real');
  conBoqueta.accesorios.boquetas.push({ tipo: 'boqueta', forma: 'rectangular', ladoACm: 15, ladoBCm: 10, largoBocaCm: 12, posicionCm: 80 });
  assert.deepEqual(registrarUso(pref, conBoqueta).boqueta, { tipo: 'boqueta', forma: 'rectangular', ladoACm: 15, ladoBCm: 10, largoBocaCm: 12 });
});

test('preferencias: se guardan por vendedor y entran en la copia de seguridad', async () => {
  almacenamiento.configurarAlmacenamiento({ motor: crearMotorEnMemoria(), leerArchivo: async (nombre) => leerDatos(nombre) });
  assert.deepEqual(await almacenamiento.leerPreferencias('v01'), preferenciasVacias());
  const pref = registrarUso(preferenciasVacias(), renglonCanaletaNotaReal());
  await almacenamiento.guardarPreferencias('v01', pref);
  assert.deepEqual((await almacenamiento.leerPreferencias('v01')).recientes, ['canaleta_nota_real']);
  assert.deepEqual((await almacenamiento.leerPreferencias('v02')).recientes, [], 'cada vendedor tiene las suyas');
  assert.deepEqual((await almacenamiento.exportarTodo()).preferencias.v01.recientes, ['canaleta_nota_real']);
});

test('clientes conocidos: de notas anteriores, el más reciente primero y sin repetir', () => {
  const notas = [
    { cliente: 'Pérez Construcciones', fechaEmision: '2026-10-01T10:00:00Z' },
    { cliente: '  pérez   construcciones ', fechaEmision: '2026-11-01T10:00:00Z' },
    { cliente: 'Gómez', fechaCreacion: '2026-11-10T10:00:00Z' },
    { cliente: '', fechaCreacion: '2026-11-12T10:00:00Z' },
  ];
  assert.deepEqual(clientesConocidos(notas), ['Gómez', 'pérez construcciones']);
  assert.deepEqual(clientesConocidos([]), []);
  assert.equal(clientesConocidos(notas, 1).length, 1);
});

// ---------- repetir una nota ----------

test('repetir una nota: mismas piezas en una nota nueva, sin foto, sin número y sin tocar la original', () => {
  const canaleta = canaletaConTapasYBoqueta();
  canaleta.calculado = fotoDelCalculo(canaleta, calcularRenglon(canaleta, datos), config);
  canaleta.mostrar3d = true;
  const original = notaCon([canaleta, { ...nuevo('compriband'), id: 'r2', cantidad: 6 }], { estado: 'emitida', numero: 123, factura: 'A-9', fechaEntrega: '2026-11-20', prioridad: 'urgente' });
  const copiaOriginal = JSON.parse(JSON.stringify(original));
  const copia = datosParaRepetir(original);
  assert.deepEqual(Object.keys(copia).sort(), ['cliente', 'mostrar3d', 'renglones'], 'no se copian número, factura, entrega ni prioridad');
  assert.equal(copia.cliente, 'Cliente');
  assert.equal(copia.renglones.length, 2);
  assert.ok(copia.renglones.every((r, i) => r.id !== original.renglones[i].id), 'ids nuevos');
  assert.ok(copia.renglones.every((r) => r.calculado === undefined), 'se vuelve a calcular con los códigos de hoy');
  assert.equal(copia.renglones[1].cantidad, 6);
  // Lo que producción necesita viaja completo.
  assert.deepEqual(copia.renglones[0].perfil, canaleta.perfil);
  assert.deepEqual(copia.renglones[0].accesorios, canaleta.accesorios);
  assert.equal(calcularRenglon(copia.renglones[0], datos).descripcion, canaleta.calculado.descripcion);
  assert.deepEqual(original, copiaOriginal, 'la nota original queda igual');
});

// ---------- lo que falta para emitir ----------

test('faltantes: dicen DÓNDE se corrige cada cosa y coinciden con la validación de siempre', () => {
  const sinLargo = { ...renglonCanaletaNotaReal(), id: 'ra', largoCm: null };
  const servicio = { ...nuevo('gt_corte_laser'), id: 'rb' };
  const nota = notaCon([renglonCanaletaNotaReal(), sinLargo, servicio], { cliente: ' ', factura: '' });
  const resultados = nota.renglones.map((r) => calcularRenglon(r, datos));
  const faltantes = faltantesDeNota(nota, resultados);
  assert.deepEqual(faltantes.map((f) => [f.donde, f.campo, f.numero ?? null]), [
    ['encabezado', 'cliente', null], ['encabezado', 'factura', null],
    ['renglon', 'largoCm', 2], ['renglon', 'alcance', 3],
  ]);
  assert.equal(faltantes[2].renglonId, 'ra');
  // Mismos errores que validarNota (que no se tocó): ni uno más ni uno menos.
  const validacion = validarNota(nota, resultados);
  assert.equal(validacion.puedeEmitir, false);
  assert.equal(faltantes.length, validacion.errores.length);
  // Nota vacía y nota completa.
  assert.deepEqual(faltantesDeNota(notaCon([]), []).map((f) => f.donde), ['nota']);
  const completa = notaCon([renglonCanaletaNotaReal()]);
  assert.deepEqual(faltantesDeNota(completa, completa.renglones.map((r) => calcularRenglon(r, datos))), []);
  // Un tramo sin medida lleva al tramo.
  const roto = renglonCanaletaNotaReal();
  roto.perfil.tramos[2].medidaCm = '';
  assert.equal(calcularRenglon(roto, datos).problemas.find((p) => p.nivel === 'error').campo, 'tramo2');
});

// ---------- hoja impresa: cada dato una sola vez ----------

test('hoja impresa: ningún dato aparece dos veces (canaleta con tapas y boqueta)', () => {
  const renglon = canaletaConTapasYBoqueta();
  const nota = notaCon([renglon]);
  const hoja = armarHoja(nota, datos);
  const r = hoja.renglones[0];
  const dibujos = dibujosDeRenglon(renglon, r.dibujo, datos);
  const textosDibujos = textosDeSvg(dibujos.principal + dibujos.extras);
  const { facturacion, fabricacion } = textosDeRenglon(r, textosDibujos);

  // Zona de facturación: la descripción (regla confirmada, no se toca) y una fila con código por cada accesorio.
  assert.equal(r.descripcion, '2,44 mts canaleta pp negro D60 CH 25 c/ tapa izq. soldada, tapa der. engrampada y 1 boqueta');
  assert.deepEqual(r.adicionales.map((x) => x.codigo), ['TS60N', 'BQ10N']);
  assert.equal(r.codigo, 'CG05P60');

  // R1 Desarrollo: una vez (en la descripción); no hay línea "Desarrollo" ni suma de tramos.
  assert.equal(contar(facturacion, /\bD60\b/), 1);
  assert.equal(contar(fabricacion, /desarrollo/i), 0);
  // R2 Medidas de los tramos: solo las cotas del 2D (no hay texto "Tramos: 1 + 20 + 32 + 7").
  assert.equal(contar(fabricacion, /^Tramos/), 0);
  assert.equal(contar(fabricacion, /\+ 20 \+/), 0);
  for (const cota of ['20', '32', '7']) assert.equal(contar(textosDeSvg(dibujos.principal), new RegExp(`^${cota}$`)), 1, `cota ${cota}`);
  assert.equal(contar(fabricacion, /dobl\. aplast\./), 1, 'el tipo de tramo está escrito en el 2D');
  // R3 Lado de la pintura: una vez como texto (ficha); en el dibujo queda la flecha "pintura", sin leyenda.
  assert.equal(contar(fabricacion, /AFUERA/), 1);
  assert.deepEqual(r.ficha.at(-1), { rotulo: 'Pintura', valor: 'AFUERA' });
  assert.equal(contar(textosDibujos, /Pintura AFUERA/i), 0);
  assert.equal(contar(textosDibujos, /^pintura$/), 1);
  // R4 Ficha de material junto al 2D (material completo, calibre con su espesor, color).
  assert.deepEqual(r.ficha.map((x) => `${x.rotulo}: ${x.valor}`), ['Material: Chapa galvanizada prepintada', 'Calibre: C25 (0,5 mm)', 'Color: negro', 'Pintura: AFUERA']);
  // R6 Tapas: en fabricación, una vez cada una (vista desde arriba); sin líneas "Tapa izquierda: soldada".
  assert.equal(contar(fabricacion, /soldada/), 1);
  assert.equal(contar(fabricacion, /engrampada/), 1);
  assert.equal(contar(fabricacion, /^Tapa (izquierda|derecha):/), 0);
  // R7 Boqueta: tamaño y posición una vez (vista desde arriba); en la cara, su nombre y la cota a través; en notas, solo la boca.
  assert.equal(contar(fabricacion, /Ø10/), 1);
  assert.equal(contar(fabricacion, /^30$/), 1, 'posición a lo largo: una sola cota');
  assert.equal(contar(fabricacion, /^16$/), 1, 'posición a través de la cara');
  assert.deepEqual(r.notas, [{ rotulo: 'Boqueta 1', valor: 'boca 10 cm' }]);
  // R9 Largo: en la descripción y en UNA vista.
  assert.equal(contar(fabricacion, /largo 2,44 m/), 1);
  // R13 Fecha en el encabezado; en el pie solo la hora. R14 vendedor una vez.
  assert.equal(hoja.fecha, '13/11/2026');
  assert.equal(hoja.pie.emision, 'BORRADOR (sin emitir)');
  assert.equal(armarHoja({ ...nota, estado: 'emitida', numero: 5, fechaEmision: '2026-11-13T12:52:00' }, datos).pie.emision, 'Emitida a las 12:52');
  assert.equal(hoja.pie.vendedor, 'Vendedor 1');

  // Y nada de producción se perdió: todo lo que antes se escribía sigue en algún lugar de la hoja.
  const todo = facturacion.concat(fabricacion).join(' | ');
  for (const dato of ['2,44', 'D60', 'CH 25', 'negro', 'AFUERA', '20', '32', '7', 'dobl. aplast.', 'soldada', 'engrampada', 'Ø10', 'boca 10 cm', '30', '16', 'CG05P60', 'TS60N', 'BQ10N']) {
    assert.ok(todo.includes(dato), `falta ${dato}`);
  }
});

test('hoja impresa: código pendiente y genérico una sola vez; avisos sin repetir; notas solo con lo que el dibujo no dice', () => {
  // R11 Código pendiente: en la columna y nada más.
  const articulo = armarRenglonDeHoja({ ...nuevo('h_montante'), id: 'a' }, 0, notaCon([]), datos);
  assert.equal(articulo.codigo, 'PENDIENTE');
  assert.deepEqual(articulo.notas, []);
  assert.equal(articulo.dibujo, null, 'un artículo no lleva dibujo');
  assert.deepEqual(articulo.ficha, [], 'ni ficha de material');
  assert.equal(articulo.con3d, false);
  // R12 Código genérico: marcado en la columna.
  const chapa = armarRenglonDeHoja(nuevo('chapa_lisa'), 0, notaCon([]), datos);
  assert.match(chapa.codigo, /^CL\d+\w* \(genérico\)$/);
  assert.equal(chapa.notas.filter((n) => /genérico/i.test(n.valor)).length, 0);
  // R15 Empalme: está en la descripción; no se repite como detalle ni como aviso.
  const larga = { ...renglonCanaletaNotaReal(), largoCm: 300 };
  const conEmpalme = armarRenglonDeHoja(larga, 0, notaCon([]), datos);
  assert.match(conEmpalme.descripcion, /empalme 2,44 \+ 0,56/);
  assert.deepEqual(conEmpalme.notas, []);
  // R8 Corte: la cara acotada lo dibuja; la nota solo aparece si lleva pared.
  const conCorte = renglonCanaletaNotaReal();
  conCorte.cortes = [{ tramo: 2, forma: 'redonda', diametroCm: 10, posicionCm: 50 }];
  assert.deepEqual(armarRenglonDeHoja(conCorte, 0, notaCon([]), datos).notas, []);
  conCorte.cortes[0].paredAlturaCm = 5;
  assert.deepEqual(armarRenglonDeHoja(conCorte, 0, notaCon([]), datos).notas, [{ rotulo: 'Corte 1', valor: 'pared de 5 cm hacia afuera' }]);
  assert.ok(textosDeSvg(dibujosDeRenglon(conCorte, 'perfil', datos).extras).some((t) => t.includes('C1 Ø10')), 'el corte sigue dibujado y acotado');
  // Corte láser: su vista de frente dice la onda y los valles; no hay texto que lo repita.
  const laser = nuevo('cumbrera_sinusoidal_20');
  const hojaLaser = armarRenglonDeHoja(laser, 0, notaCon([]), datos);
  assert.equal(hojaLaser.notas.filter((n) => /onda/.test(n.valor)).length, 0);
  assert.ok(textosDeSvg(dibujosDeRenglon(laser, hojaLaser.dibujo, datos).extras).some((t) => /onda 3,6/.test(t)));
  // Observaciones (del renglón y de un tramo) y desarrollo corregido a mano: se conservan.
  const conObs = { ...renglonCanaletaNotaReal(), observaciones: 'Entregar con la tapa puesta' };
  conObs.perfil.tramos[1].observacion = 'cara vista';
  assert.deepEqual(armarRenglonDeHoja(conObs, 0, notaCon([]), datos).notas, [{ rotulo: 'Tramo 2', valor: 'cara vista' }, { rotulo: 'Observaciones', valor: 'Entregar con la tapa puesta' }]);
  const boqueta = { ...nuevo('boqueta_suelta'), desarrolloManualCm: 40 };
  assert.ok(armarRenglonDeHoja(boqueta, 0, notaCon([]), datos).notas.some((n) => n.rotulo === 'Aviso' && /corregido a mano: 40 cm/.test(n.valor)));
  // Tapa a medida y boqueta en la tapa: lo que no está en la vista desde arriba queda escrito.
  const especial = canaletaConTapasYBoqueta();
  especial.accesorios.tapaIzquierdaMedidas = { pestanaCm: 2 };
  Object.assign(especial.accesorios.boquetas[0], { ubicacion: 'tapaDerecha', alturaCm: 8, desplazamientoCm: 3 });
  assert.deepEqual(armarRenglonDeHoja(especial, 0, notaCon([]), datos).notas, [
    { rotulo: 'Tapa izquierda', valor: 'pestaña 2 cm' },
    { rotulo: 'Boqueta 1', valor: 'boca 10 cm, en la tapa derecha: centro a 8 cm del fondo, corrida 3 cm del medio' },
  ]);
  // Pieza sin pintar: la ficha no inventa color ni lado.
  assert.deepEqual(fichaDeMaterial({ ...renglonCanaletaNotaReal(), terminacion: 'N' }, materiales).map((x) => x.rotulo), ['Material', 'Calibre']);
  assert.equal(llevaDibujo(nuevo('compriband')), false);
  assert.equal(llevaDibujo(renglonCanaletaNotaReal()), true);
});

test('hoja impresa: una nota emitida sigue mostrando la foto, aunque después cambie la tabla de códigos', () => {
  const renglon = canaletaConTapasYBoqueta();
  renglon.calculado = fotoDelCalculo(renglon, calcularRenglon(renglon, datos), config);
  const emitida = notaCon([renglon], { estado: 'emitida', numero: 77, fechaEmision: '2026-11-13T12:52:00', fechaEntrega: '2026-11-20', prioridad: 'urgente' });
  const sinCodigos = { ...datos, codigos: [] };
  const hoja = armarHoja(emitida, sinCodigos);
  assert.equal(hoja.numero, '77');
  assert.equal(hoja.identificador, 'AB-C-77');
  assert.equal(hoja.renglones[0].codigo, 'CG05P60', 'el código es el de la foto');
  assert.equal(hoja.renglones[0].descripcion, renglon.calculado.descripcion);
  assert.equal(hoja.renglones[0].cantidad, '1');
  assert.equal(hoja.renglones[0].piezas, '1');
  // La entrega comprometida y la urgencia (las usa producción) van una vez, en el encabezado.
  assert.equal(hoja.entrega, '20/11/2026');
  assert.equal(hoja.urgente, true);
  assert.equal(armarHoja(notaCon([renglon]), datos).entrega, null);
});

test('producción recibe lo mismo: tiempos y trabajos no dependen de las pantallas nuevas', () => {
  const modelo = prepararModelo(leerDatos('tiempos-mtm.json'), config);
  const prod = leerDatos('produccion.json');
  const renglon = canaletaConTapasYBoqueta();
  const nota = notaCon([renglon], { estado: 'emitida', numero: 1 });
  const antes = tiempoDeNota(nota, datos, modelo).totalEstandarS;
  // Repetir la nota, recordar preferencias o armar la hoja no cambian el renglón.
  const copiaRenglon = JSON.parse(JSON.stringify(renglon));
  registrarUso(preferenciasVacias(), renglon);
  armarHoja(nota, datos);
  datosParaRepetir(nota);
  assert.deepEqual(renglon, copiaRenglon);
  assert.equal(tiempoDeNota(nota, datos, modelo).totalEstandarS, antes);
  const repetida = notaCon(datosParaRepetir(nota).renglones, { id: 'n2', estado: 'emitida', numero: 2 });
  assert.equal(tiempoDeNota(repetida, datos, modelo).totalEstandarS, antes, 'la nota repetida tarda lo mismo');
  const [a, b] = armarTrabajos([nota, repetida], {}, { datos, modelo, prod });
  assert.deepEqual([a.maquina, a.planta, a.atributos.perfil, a.atributos.material], [b.maquina, b.planta, b.atributos.perfil, b.atributos.material], 'y se agrupa igual');
});
