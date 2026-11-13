// Grupo de empresas (Abasto · HIPER · G-TEC): empresa y numeración, catálogo por empresa,
// tipos de renglón nuevos (artículo relevado, pieza metalmecánica, servicio), planta de cada
// renglón, migración de notas viejas y demo de las tres empresas.
import { test } from 'node:test';
import assert from 'node:assert/strict';

import * as almacenamiento from '../src/datos/almacenamiento.js';
import {
  listaEmpresas, listaPlantas, empresaDeSucursal, empresaDeNota, sucursalesDeEmpresa, vendedoresDeEmpresa,
  identificadorDeNota, plantillasVisibles, plantillaEsDeEmpresa, tipoDeRenglon, plantaDeRenglon, repartoPorPlanta, maquinaEnPlanta,
} from '../src/logica/empresas.js';
import { crearRenglonDesdePlantilla, buscarPlantilla, filtrarPlantillas } from '../src/logica/renglones.js';
import { calcularRenglon } from '../src/logica/calculoRenglon.js';
import { completarTexto } from '../src/logica/descripcion.js';
import { cantidadDeLaNota } from '../src/logica/chapas.js';
import { fotoDelCalculo } from '../src/logica/fotoCalculo.js';
import { prepararModelo } from '../src/logica/tiempos.js';
import { tiempoDeRenglon } from '../src/logica/tiemposRenglon.js';
import { armarTrabajos } from '../src/logica/produccion.js';
import { motivoParaNoEntrar } from '../src/logica/agrupamiento.js';
import { generarDemo } from '../src/logica/demo.js';
import { leerDatos, datosCompletos, crearMotorEnMemoria, renglonCanaletaNotaReal } from './ayudante.js';

const datos = datosCompletos();
const { catalogo, config } = datos;
const prod = leerDatos('produccion.json');
const modelo = prepararModelo(leerDatos('tiempos-mtm.json'), config);
const nuevo = (id) => crearRenglonDesdePlantilla(buscarPlantilla(catalogo, id), config);
const notaDe = (sucursalId, renglones = []) => ({ id: `n_${sucursalId}`, estado: 'emitida', numero: 7, sucursalId, empresaId: empresaDeSucursal(datos, sucursalId).id, renglones });

function almacenVacio() {
  almacenamiento.configurarAlmacenamiento({ motor: crearMotorEnMemoria(), leerArchivo: async (nombre) => leerDatos(nombre) });
}

// ---------- empresas, sucursales y numeración ----------

test('grupo: tres empresas con prefijo, planta y logo (o texto para mostrar en su lugar)', () => {
  const empresas = listaEmpresas(datos);
  assert.deepEqual(empresas.map((e) => e.id), ['abasto', 'hiper', 'gtec']);
  assert.equal(new Set(empresas.map((e) => e.prefijo)).size, 3, 'prefijos repetidos');
  for (const e of empresas) {
    assert.ok(e.logo || e.logoTexto, `${e.id}: sin logo ni texto de reemplazo`);
    assert.ok(listaPlantas(datos).some((p) => p.id === e.plantaPorDefecto), `${e.id}: planta desconocida`);
    assert.ok(sucursalesDeEmpresa(datos, e.id).length >= 1, `${e.id}: sin sucursales`);
    assert.ok(vendedoresDeEmpresa(datos, e.id).length >= 1, `${e.id}: sin vendedores`);
  }
  // Cada sucursal es de una sola empresa y cada vendedor tiene una sucursal que existe.
  for (const s of datos.sucursales) assert.ok(empresas.some((e) => e.id === s.empresaId), `${s.id}: empresa desconocida`);
  for (const v of datos.vendedores) assert.ok(datos.sucursales.some((s) => s.id === v.sucursalHabitualId), `${v.id}: sucursal desconocida`);
  assert.equal(empresaDeSucursal(datos, 'colon').id, 'abasto');
  assert.equal(empresaDeSucursal(datos, 'hiper_japon').id, 'hiper');
  assert.equal(empresaDeSucursal(datos, 'gtec_ferreyra').id, 'gtec');
});

test('numeración por empresa y sucursal: cada una lleva su correlativo y el identificador lleva el prefijo', async () => {
  almacenVacio();
  const base = await almacenamiento.cargarDatosBase();
  assert.equal(base.grupo.empresas.length, 3);
  const emitir = async (sucursalId, vendedorId) => almacenamiento.emitirNota(
    await almacenamiento.crearNotaVacia({ sucursalId, vendedorId, empresaId: empresaDeSucursal(base, sucursalId).id }), base.sucursales);
  const a1 = await emitir('colon', 'v01');
  const h1 = await emitir('hiper_japon', 'vh01');
  const g1 = await emitir('gtec_ferreyra', 'vg01');
  const a2 = await emitir('colon', 'v01');
  const h2 = await emitir('hiper_japon', 'vh01');
  assert.deepEqual([a1.numero, a2.numero, h1.numero, h2.numero, g1.numero], [1, 2, 1, 2, 1]);
  assert.equal(identificadorDeNota(a2, base), 'AB-C-2');
  assert.equal(identificadorDeNota(h2, base), 'HI-H-2');
  assert.equal(identificadorDeNota(g1, base), 'GT-G-1');
  assert.equal(identificadorDeNota({ sucursalId: 'colon', numero: null }, base), 'AB-C-borrador');
  // Ningún identificador se repite aunque los números sí.
  const ids = [a1, a2, h1, h2, g1].map((n) => identificadorDeNota(n, base));
  assert.equal(new Set(ids).size, ids.length);
  assert.equal(empresaDeNota(h1, base).id, 'hiper');
});

test('sucursales editadas antes del grupo: se les completa la empresa y se suman las de HIPER y G-TEC', () => {
  const delArchivo = leerDatos('sucursales.json').sucursales;
  const viejas = delArchivo.filter((s) => s.empresaId === 'abasto').map(({ empresaId, ...s }) => ({ ...s, nombre: `${s.nombre} (editada)` }));
  const unidas = almacenamiento.unirSucursales(viejas, delArchivo, datos.grupo);
  assert.equal(unidas.length, delArchivo.length);
  assert.equal(unidas.find((s) => s.id === 'colon').nombre, 'Colón (editada)', 'lo editado no se pisa');
  assert.ok(unidas.every((s) => s.empresaId), 'todas con empresa');
  assert.equal(unidas.find((s) => s.id === 'hiper_japon').empresaId, 'hiper');
  assert.equal(almacenamiento.unirSucursales(null, delArchivo, datos.grupo), delArchivo);
});

// ---------- catálogo por empresa ----------

test('catálogo: cada plantilla dice quién la vende y dónde se hace, con valores que existen', () => {
  const empresas = new Set(listaEmpresas(datos).map((e) => e.id));
  const plantas = new Set(listaPlantas(datos).map((p) => p.id));
  for (const p of catalogo.plantillas) {
    assert.ok(Array.isArray(p.empresas), `${p.id}: falta "empresas"`);
    for (const e of p.empresas) assert.ok(empresas.has(e), `${p.id}: empresa desconocida ${e}`);
    assert.ok(p.fabricaEn === null || p.fabricaEn === 'tercero' || plantas.has(p.fabricaEn), `${p.id}: fabricaEn desconocido ${p.fabricaEn}`);
    assert.ok(['stock', 'a_pedido'].includes(p.abastecimiento), `${p.id}: abastecimiento`);
  }
});

test('catálogo filtrado: cada vendedor ve el de su empresa y, con "ver todo el grupo", todo', () => {
  const abasto = plantillasVisibles(catalogo, 'abasto');
  const hiper = plantillasVisibles(catalogo, 'hiper');
  const gtec = plantillasVisibles(catalogo, 'gtec');
  const ids = (lista) => new Set(lista.map((p) => p.id));
  // Abasto: plegados a medida y productos HIPER que revende; no los servicios de G-TEC.
  assert.ok(ids(abasto).has('canaleta_nota_real') && ids(abasto).has('h_perfiles_pgc') && ids(abasto).has('ab_placa_estandar'));
  assert.ok(!ids(abasto).has('gt_corte_laser'));
  // HIPER: sus productos; no los plegados a medida del taller de Abasto ni la reventa de otras marcas.
  assert.ok(ids(hiper).has('h_perfiles_pgc') && ids(hiper).has('h_montante'));
  assert.ok(!ids(hiper).has('canaleta_nota_real') && !ids(hiper).has('ab_placa_estandar') && !ids(hiper).has('gt_corte_laser'));
  // G-TEC: servicios y pieza a medida.
  assert.ok(ids(gtec).has('gt_corte_laser') && ids(gtec).has('gt_pieza_a_medida'));
  assert.ok(!ids(gtec).has('canaleta_nota_real') && !ids(gtec).has('h_montante'));
  // La pieza especial libre es compartida (empresas vacío).
  for (const lista of [abasto, hiper, gtec]) assert.ok(ids(lista).has('pieza_libre'));
  assert.ok(plantillaEsDeEmpresa(buscarPlantilla(catalogo, 'pieza_libre'), 'gtec'));
  // Ver todo el grupo.
  assert.equal(plantillasVisibles(catalogo, 'gtec', true).length, catalogo.plantillas.length);
  assert.ok(abasto.length < catalogo.plantillas.length && hiper.length < abasto.length && gtec.length < hiper.length);
});

test('buscador: varias palabras en cualquier orden, modelos, marca y palabras del mostrador', () => {
  const encontrar = (texto, lista) => filtrarPlantillas(catalogo, texto, lista).map((p) => p.id);
  assert.ok(encontrar('extractor 150').includes('h_extractores_eolicos'), 'busca dentro de los modelos');
  assert.ok(encontrar('150 extractor').includes('h_extractores_eolicos'), 'en cualquier orden');
  assert.ok(encontrar('durlock').includes('h_montante'), 'palabra del mostrador');
  assert.ok(encontrar('laser cano').includes('gt_corte_laser_cano'), 'sin tildes ni eñes');
  assert.deepEqual(encontrar('laser', plantillasVisibles(catalogo, 'hiper')), [], 'solo en la lista que se le pasa');
  assert.equal(encontrar('').length, catalogo.plantillas.length);
  assert.deepEqual(encontrar('zzzz no existe'), []);
});

test('productos relevados: llevan su fuente y NO se les inventó código, medida ni dibujo', () => {
  const relevadas = catalogo.plantillas.filter((p) => p.origen === 'relevamiento');
  assert.ok(relevadas.length > 150);
  for (const p of relevadas) {
    assert.match(p.referencia, /^https:\/\/(hiperargentina\.com|abastosoluciones\.com\.ar|gtecdesarrollosyservicios\.com)\//, `${p.id}: sin fuente`);
    assert.equal(p.codigoPendiente, true, `${p.id}: tiene que salir con código pendiente`);
    assert.equal(p.codigo, undefined, `${p.id}: no se inventa un código`);
    assert.equal(p.codigoGenerico, undefined, `${p.id}: no se arma un código genérico`);
    assert.equal(p.sinDibujo, true, `${p.id}: no se inventa un dibujo`);
    assert.equal(p.perfil, undefined, `${p.id}: no se inventa un perfil`);
  }
  // Los ids que la empresa pidió sacar siguen afuera.
  for (const id of ['reduccion', 'cupertina', 'alfeizar', 'perfil_z']) assert.equal(buscarPlantilla(catalogo, id), null);
  // Las plantillas que ya estaban no cambiaron de medidas (se revisa una de cada tipo).
  assert.deepEqual(buscarPlantilla(catalogo, 'canaleta_nota_real').perfil.tramos.map((t) => t.medidaCm), [1, 20, 32, 7]);
});

test('código cargado en el catálogo: en la plantilla o en el modelo elegido (sin programar)', () => {
  const copia = JSON.parse(JSON.stringify(catalogo));
  const plantilla = buscarPlantilla(copia, 'h_extractores_eolicos');
  plantilla.parametros[0].opciones[1].codigo = 'EXT150';
  const renglon = crearRenglonDesdePlantilla(plantilla, config);
  renglon.parametros.variante = plantilla.parametros[0].opciones[1].valor;
  let r = calcularRenglon(renglon, { ...datos, catalogo: copia });
  assert.equal(r.codigo.codigo, 'EXT150');
  assert.ok(!r.avisos.some((a) => a.startsWith('Código pendiente')));
  renglon.parametros.variante = plantilla.parametros[0].opciones[0].valor;
  r = calcularRenglon(renglon, { ...datos, catalogo: copia });
  assert.equal(r.codigo.codigo, null, 'el otro modelo sigue pendiente');
  assert.deepEqual(r.errores, []);
});

// ---------- tipos de renglón ----------

test('tipos de renglón: se derivan del renglón (plegada, especial, artículo, metalmecánica, servicio)', () => {
  assert.equal(tipoDeRenglon(nuevo('canaleta_nota_real')), 'plegada');
  assert.equal(tipoDeRenglon(nuevo('boqueta_suelta')), 'especial');
  assert.equal(tipoDeRenglon(nuevo('compriband')), 'articulo');
  assert.equal(tipoDeRenglon(nuevo('h_montante')), 'articulo');
  assert.equal(tipoDeRenglon(nuevo('gt_pieza_a_medida')), 'metalmecanica');
  assert.equal(tipoDeRenglon(nuevo('gt_corte_laser')), 'servicio');
});

test('artículo relevado: se elige el modelo, sale por unidad, sin material y con código pendiente', () => {
  const renglon = nuevo('h_perfiles_pgc');
  renglon.cantidad = 40;
  const r = calcularRenglon(renglon, datos);
  assert.deepEqual(r.errores, []);
  assert.equal(r.porUnidad, true);
  assert.equal(r.descripcion, renglon.parametros.variante, 'la descripción es el modelo tal como lo publica HIPER');
  assert.ok(r.avisos.includes('Código pendiente: lo completa administración'));
  assert.equal(cantidadDeLaNota(renglon, r, config).texto, '40');
  // Reventa de otra marca: la presentación es opcional y no deja signos de pregunta.
  const placa = nuevo('ab_placa_estandar');
  assert.equal(calcularRenglon(placa, datos).descripcion, 'Placa Estandar');
  placa.parametros.presentacion = '12,5 mm 2,40 x 1,20';
  assert.equal(calcularRenglon(placa, datos).descripcion, 'Placa Estandar 12,5 mm 2,40 x 1,20');
});

test('pieza metalmecánica a medida: descripción, medidas, material, espesor en mm, procesos y plano opcional', () => {
  const renglon = nuevo('gt_pieza_a_medida');
  let r = calcularRenglon(renglon, datos);
  // Recién creada le faltan datos: no se puede emitir y dice qué falta y dónde.
  assert.ok(r.errores.includes('Falta "Qué es"') && r.errores.includes('Falta "Medidas (mm)"') && r.errores.includes('Falta "Espesor"'));
  assert.deepEqual(r.problemas.filter((p) => p.nivel === 'error').map((p) => p.campo).sort(), ['descripcion', 'dimensiones', 'espesorMm']);
  Object.assign(renglon.parametros, { descripcion: 'soporte', dimensiones: '300 x 120 x 40', espesorMm: 3.2, procesos: ['corte láser', 'plegado CNC'] });
  renglon.cantidad = 12;
  r = calcularRenglon(renglon, datos);
  assert.deepEqual(r.errores, []);
  assert.equal(r.descripcion, 'soporte 300 x 120 x 40 SAE 1010 (acero al carbono) esp 3,2 mm (corte láser, plegado CNC)');
  renglon.parametros.plano = '0012-B.dxf';
  assert.match(calcularRenglon(renglon, datos).descripcion, / plano 0012-B\.dxf$/);
  // Sin procesos no se puede fabricar.
  renglon.parametros.procesos = [];
  assert.ok(calcularRenglon(renglon, datos).errores.some((e) => e.includes('al menos una opción')));
  // Límites publicados por G-TEC: el láser llega a 20 mm; el plegado avisa después de 6,3 y frena en 12,7.
  renglon.parametros.procesos = ['corte láser'];
  renglon.parametros.espesorMm = 25;
  assert.ok(calcularRenglon(renglon, datos).errores.some((e) => e.includes('corte láser: hasta 20 mm')));
  renglon.parametros.procesos = ['chorro de agua', 'plegado CNC'];
  renglon.parametros.espesorMm = 8;
  r = calcularRenglon(renglon, datos);
  assert.deepEqual(r.errores, []);
  assert.ok(r.avisos.some((a) => a.includes('plegado CNC: más de 6,3 mm')));
  renglon.parametros.espesorMm = 16;
  assert.ok(calcularRenglon(renglon, datos).errores.some((e) => e.includes('plegado CNC: hasta 12,7 mm')));
  // Los calibres de chapa de siempre no se tocaron.
  assert.deepEqual(datos.materiales.calibres.map((c) => c.id).slice(0, 3), ['C30', 'C28', 'C27']);
});

test('servicio: alcance, unidad y lugar; la cantidad puede tener decimales (2,5 horas)', () => {
  const renglon = nuevo('gt_corte_laser');
  assert.ok(calcularRenglon(renglon, datos).errores.includes('Falta "Alcance (qué hay que hacer)"'));
  renglon.parametros.alcance = '20 piezas según DXF';
  renglon.cantidad = 2.5;
  let r = calcularRenglon(renglon, datos);
  assert.deepEqual(r.errores, []);
  assert.equal(r.descripcion, 'Corte láser de chapa: 20 piezas según DXF (en planta G-TEC)');
  const cantidad = cantidadDeLaNota(renglon, r, config);
  assert.equal(`${cantidad.texto} ${cantidad.abreviatura}`, '2,5 h');
  // Material y espesor son opcionales; si se cargan, aparecen y se controlan contra el límite publicado.
  Object.assign(renglon.parametros, { material: 'aluminio', espesorMm: 3 });
  assert.equal(calcularRenglon(renglon, datos).descripcion, 'Corte láser de chapa: 20 piezas según DXF en aluminio esp 3 mm (en planta G-TEC)');
  renglon.parametros.espesorMm = 25;
  r = calcularRenglon(renglon, datos);
  assert.ok(r.errores.includes('"Espesor" no puede pasar de 20 mm'));
  assert.equal(r.problemas.find((p) => p.nivel === 'error').campo, 'espesorMm');
  // Una cantidad de 0 o negativa no pasa; en un artículo la cantidad sigue siendo entera.
  renglon.parametros.espesorMm = 3;
  renglon.cantidad = 0;
  assert.ok(calcularRenglon(renglon, datos).errores.includes('La cantidad tiene que ser mayor a 0'));
  const articulo = nuevo('compriband');
  articulo.cantidad = 2.5;
  assert.ok(calcularRenglon(articulo, datos).errores.includes('La cantidad tiene que ser un número entero mayor a 0'));
});

test('texto de la descripción: partes opcionales entre corchetes y textos que no son números', () => {
  assert.equal(completarTexto('caño[ Ø{diametroCm}][ {nota}]', { diametroCm: 10 }), 'caño Ø10');
  assert.equal(completarTexto('caño[ Ø{diametroCm}][ {nota}]', { diametroCm: 10, nota: 'reforzado' }), 'caño Ø10 reforzado');
  assert.equal(completarTexto('pieza ({procesos})', { procesos: ['corte láser', 'soldadura'] }), 'pieza (corte láser, soldadura)');
  assert.equal(completarTexto('plano {plano}', { plano: '0012' }), 'plano 0012', 'un número de plano no pierde los ceros');
  // Lo de siempre no cambió.
  assert.equal(completarTexto('codo {anguloGrados}° Ø{diametroCm}', { anguloGrados: 90, diametroCm: '7.5' }), 'codo 90° Ø7,5');
  assert.equal(completarTexto('boqueta Ø{diametroCm}', {}), 'boqueta Ø?');
});

// ---------- dónde se hace cada renglón ----------

test('planta de cada renglón: lo que se fabrica va a su planta; lo de stock, al depósito de quien vende', () => {
  const canaleta = renglonCanaletaNotaReal();
  const servicio = nuevo('gt_corte_laser');
  const perfilHiper = nuevo('h_perfiles_pgc');
  const placa = nuevo('ab_placa_estandar');
  const libre = nuevo('pieza_libre');
  const notaAbasto = notaDe('colon', [canaleta, perfilHiper, servicio, placa]);
  assert.deepEqual(plantaDeRenglon(canaleta, notaAbasto, datos), { plantaId: 'taller_abasto', motivo: 'fabrica' });
  assert.deepEqual(plantaDeRenglon(perfilHiper, notaAbasto, datos), { plantaId: 'taller_abasto', motivo: 'deposito' }, 'Abasto lo entrega de su depósito');
  assert.deepEqual(plantaDeRenglon(servicio, notaAbasto, datos), { plantaId: 'planta_gtec', motivo: 'fabrica' }, 'el servicio lo hace G-TEC aunque venda Abasto');
  assert.deepEqual(plantaDeRenglon(placa, notaAbasto, datos), { plantaId: 'taller_abasto', motivo: 'deposito' }, 'reventa de otra marca');
  // La misma nota se reparte sola.
  assert.deepEqual(repartoPorPlanta(notaAbasto, datos).map((g) => [g.plantaId, g.renglones]), [['taller_abasto', [0, 1, 3]], ['planta_gtec', [2]]]);
  // En una nota de HIPER el mismo perfil sale del depósito de HIPER, y una canaleta a medida va al taller de Abasto.
  const notaHiper = notaDe('hiper_japon', [perfilHiper, canaleta, libre]);
  assert.equal(plantaDeRenglon(perfilHiper, notaHiper, datos).plantaId, 'planta_hiper');
  assert.equal(plantaDeRenglon(canaleta, notaHiper, datos).plantaId, 'taller_abasto');
  assert.equal(plantaDeRenglon(libre, notaHiper, datos).plantaId, 'planta_hiper', 'una pieza sin planta fija la hace quien vende');
  // Renglón viejo (sin los campos nuevos): se resuelve con el catálogo.
  const viejo = { ...canaleta };
  delete viejo.fabricaEn; delete viejo.abastecimiento;
  assert.equal(plantaDeRenglon(viejo, notaDe('colon'), datos).plantaId, 'taller_abasto');
});

test('máquina equivalente en cada planta', () => {
  assert.equal(maquinaEnPlanta('plegadora', 'taller_abasto', prod), 'plegadora');
  assert.equal(maquinaEnPlanta('plegadora', 'planta_gtec', prod), 'gtec_plegado', 'la del mismo tipo');
  assert.equal(maquinaEnPlanta('guillotina', 'planta_gtec', prod), 'gtec_laser', 'la que la reemplaza');
  assert.equal(maquinaEnPlanta('plegadora', 'planta_hiper', prod), 'hiper_zingueria');
  assert.equal(maquinaEnPlanta('deposito', 'planta_hiper', prod), 'hiper_deposito');
  assert.equal(maquinaEnPlanta('banco', 'planta_hiper', prod, 'deposito'), 'hiper_deposito', 'lo de stock siempre al depósito');
  assert.equal(maquinaEnPlanta('gtec_laser', 'planta_gtec', prod), 'gtec_laser');
  // Cada máquina y cada operario pertenecen a una planta que existe, y cada planta tiene quien la atienda.
  const plantas = listaPlantas(datos).map((p) => p.id);
  for (const m of prod.maquinas) assert.ok(plantas.includes(m.planta), `${m.id}: planta`);
  for (const o of prod.operarios) {
    assert.ok(plantas.includes(o.planta), `${o.id}: planta`);
    for (const id of o.maquinas) assert.equal(prod.maquinas.find((m) => m.id === id)?.planta, o.planta, `${o.id} usa una máquina de otra planta`);
  }
  for (const m of prod.maquinas) assert.ok(prod.operarios.some((o) => o.maquinas.includes(m.id)), `${m.id}: sin operario`);
});

test('producción: los trabajos llevan planta y máquina de esa planta; no se arman lotes entre plantas', () => {
  const canaleta = { ...renglonCanaletaNotaReal(), id: 'r1' };
  const servicio = { ...nuevo('gt_corte_laser'), id: 'r2', cantidad: 2.5 };
  servicio.parametros.alcance = 'corte de 20 piezas';
  const pieza = { ...nuevo('gt_pieza_a_medida'), id: 'r3', cantidad: 10 };
  Object.assign(pieza.parametros, { descripcion: 'tapa', dimensiones: '200 x 100', espesorMm: 2, procesos: ['plegado CNC', 'soldadura'] });
  const articulo = { ...nuevo('h_montante'), id: 'r4', cantidad: 50 };
  const nota = notaDe('colon', [canaleta, servicio, pieza, articulo]);
  const trabajos = armarTrabajos([nota], {}, { datos, modelo, prod });
  assert.deepEqual(trabajos.map((t) => [t.planta, t.maquina]), [
    ['taller_abasto', 'plegadora'], ['planta_gtec', 'gtec_laser'], ['planta_gtec', 'gtec_plegado'], ['taller_abasto', 'deposito'],
  ]);
  assert.ok(trabajos.every((t) => t.empresaId === 'abasto' && t.tiempoValido));
  // Servicio por hora: el tiempo es el vendido (2,5 h = 150 min), sin suplementos ni preparación.
  const tiempo = tiempoDeRenglon(servicio, datos, modelo);
  assert.equal(tiempo.totalEstandarS, 2.5 * 3600);
  assert.equal(tiempo.setupEstandarS, 0);
  // Servicio por pieza y pieza metalmecánica: tiempo de la tabla (marcado SUPUESTO), nunca cero.
  servicio.parametros.unidad = 'pieza';
  assert.ok(tiempoDeRenglon(servicio, datos, modelo).mensajes[0].includes('[SUPUESTO]'));
  assert.ok(tiempoDeRenglon(pieza, datos, modelo).totalEstandarS > 0);
  // El tiempo de la canaleta de siempre no cambió por sumar plantas (EJ de la nota real).
  assert.equal(trabajos[0].maquina, 'plegadora');
  // Lotes: dos trabajos de plantas distintas no entran juntos aunque se permita mezclar máquinas.
  const opciones = { ...prod.agrupamiento, respetarMaquina: false };
  assert.equal(motivoParaNoEntrar(trabajos[1], { trabajos: [trabajos[0]] }, opciones), 'otra planta');
  assert.notEqual(motivoParaNoEntrar(trabajos[2], { trabajos: [trabajos[1]] }, opciones), 'otra planta');
  // En una nota de HIPER el artículo sale del depósito de HIPER.
  const deHiper = armarTrabajos([notaDe('hiper_japon', [articulo])], {}, { datos, modelo, prod });
  assert.deepEqual([deHiper[0].planta, deHiper[0].maquina, deHiper[0].empresaId], ['planta_hiper', 'hiper_deposito', 'hiper']);
});

// ---------- migración ----------

test('migración (versión 3): notas viejas reciben empresa y planta sin tocar número, descripción, código ni foto', async () => {
  almacenVacio();
  const base = await almacenamiento.cargarDatosBase();
  const vieja = await almacenamiento.crearNotaVacia({ sucursalId: 'ohiggins', vendedorId: 'v10' });
  delete vieja.empresaId;
  const renglon = renglonCanaletaNotaReal();
  const calculo = calcularRenglon(renglon, datos);
  renglon.calculado = fotoDelCalculo(renglon, calculo, config);
  vieja.renglones = [renglon, { ...nuevo('compriband'), id: 'r2', fabricaEn: undefined, abastecimiento: undefined }];
  delete vieja.renglones[1].fabricaEn; delete vieja.renglones[1].abastecimiento;
  const emitida = await almacenamiento.emitirNota({ ...vieja, cliente: 'Cliente viejo', factura: 'B-1' }, base.sucursales);
  const antes = JSON.parse(JSON.stringify(emitida));
  assert.equal(almacenamiento.VERSION_DATOS, 3);
  await almacenamiento.migrarDatos(base);
  const migrada = await almacenamiento.leerNota(emitida.id);
  assert.equal(migrada.empresaId, 'abasto');
  assert.deepEqual(migrada.renglones.map((r) => [r.fabricaEn, r.abastecimiento]), [['taller_abasto', 'a_pedido'], ['planta_hiper', 'stock']]);
  // Lo emitido no cambió.
  assert.equal(migrada.numero, antes.numero);
  assert.equal(migrada.cliente, 'Cliente viejo');
  assert.deepEqual(migrada.renglones[0].calculado, antes.renglones[0].calculado, 'la foto queda igual');
  assert.equal(migrada.renglones[0].calculado.descripcion, '2,44 mts canaleta pp negro D60 CH 25');
  assert.equal(migrada.renglones[0].calculado.codigo, 'CG05P60');
  // Una sola vez: la segunda corrida no vuelve a escribir.
  migrada.empresaId = 'gtec';
  assert.deepEqual(await almacenamiento.migrarDatos(base), { migradas: 0 });
  assert.equal((await almacenamiento.leerNota(emitida.id)).empresaId, 'abasto');
  // Y la planta sale bien aun sin migrar (por la sucursal y el catálogo).
  assert.equal(empresaDeNota({ sucursalId: 'ohiggins' }, base).id, 'abasto');
});

// ---------- demo ----------

test('demo: 50 notas por local de las tres empresas, sin errores y con cada planta trabajando lo suyo', () => {
  const demo = generarDemo(datos, { modelo, prod, operarios: prod.operarios }, { hoy: '2026-11-13' });
  assert.equal(demo.notas.length, datos.sucursales.length * 50);
  assert.equal(demo.resumen.renglonesConError, 0);
  for (const empresa of listaEmpresas(datos)) {
    const notas = demo.notas.filter((n) => n.empresaId === empresa.id);
    assert.equal(notas.length, sucursalesDeEmpresa(datos, empresa.id).length * 50, empresa.id);
  }
  const trabajos = armarTrabajos(demo.notas, demo.registros, { datos, modelo, prod });
  const plantas = new Set(trabajos.map((t) => t.planta));
  assert.deepEqual([...plantas].sort(), ['planta_gtec', 'planta_hiper', 'taller_abasto']);
  // Cada trabajo asignado lo tiene un operario de su planta.
  for (const t of trabajos.filter((x) => x.operarioId)) {
    assert.equal(prod.operarios.find((o) => o.id === t.operarioId).planta, t.planta, `${t.clave}: operario de otra planta`);
  }
  // Tipos de renglón de cada empresa.
  const tipos = (id) => new Set(demo.notas.filter((n) => n.empresaId === id).flatMap((n) => n.renglones.map(tipoDeRenglon)));
  assert.ok(tipos('abasto').has('plegada'));
  assert.deepEqual([...tipos('hiper')], ['articulo']);
  assert.deepEqual([...tipos('gtec')].sort(), ['metalmecanica', 'servicio']);
  // Semilla fija: dos corridas dan lo mismo.
  const otra = generarDemo(datos, { modelo, prod, operarios: prod.operarios }, { hoy: '2026-11-13' });
  assert.deepEqual(otra.notas.map((n) => n.renglones.map((r) => r.calculado.descripcion)), demo.notas.map((n) => n.renglones.map((r) => r.calculado.descripcion)));
});
