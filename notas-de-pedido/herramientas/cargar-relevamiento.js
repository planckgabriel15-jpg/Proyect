// =============================================================
// cargar-relevamiento.js
// Herramienta de DESARROLLO: pasa el relevamiento web del grupo
// (docs/relevamiento/*.tsv y g-tec.json) a datos/catalogo.json y arma la
// tabla de docs/CATALOGO_GRUPO.md. Se puede correr todas las veces que haga
// falta: no duplica (lo generado lleva "origen": "relevamiento").
//
//   node herramientas/cargar-relevamiento.js
//
// Reglas:
// - NO inventa nada: nombre, variantes y medidas son los publicados por cada
//   empresa. Lo que no tiene código de facturación sale con "código pendiente".
// - Las 51 plantillas de antes no se tocan (mismo id y mismas medidas): solo se
//   les agrega a qué empresas pertenecen y dónde se fabrican.
// - Después de correrla se puede seguir editando catalogo.json a mano; pero lo
//   generado se vuelve a escribir en la próxima corrida (para cambiarlo de
//   forma permanente, quitarle "origen" o cambiar este archivo).
// =============================================================
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), '..');
const leer = (ruta) => readFileSync(join(RAIZ, ruta), 'utf8');
const FECHA = '13/11/2026';

// ---------- 1) Empresas y planta de las plantillas que ya existían ----------
// empresas: quién lo vende (vacío = todas). fabricaEn: planta, "tercero" o null (= la planta de quien vende).
// abastecimiento: "stock" = se entrega de depósito; "a_pedido" = se fabrica para la nota.
const HIPER_STOCK = { empresas: ['abasto', 'hiper'], fabricaEn: 'planta_hiper', abastecimiento: 'stock' };
const ABASTO_TALLER = { empresas: ['abasto'], fabricaEn: 'taller_abasto', abastecimiento: 'a_pedido' };
const BASE = {
  _porGrupo: {
    estandar: { ...ABASTO_TALLER, notaOrigen: '[A CONFIRMAR] Son programas de la plegadora: se supone el taller de Abasto.' },
    canaletas: ABASTO_TALLER, babetas: ABASTO_TALLER, cumbreras: ABASTO_TALLER, cenefas: ABASTO_TALLER, cortes: ABASTO_TALLER,
    boquetas: ABASTO_TALLER, tapas: ABASTO_TALLER, canos: ABASTO_TALLER, sombreros: ABASTO_TALLER, articulos: HIPER_STOCK,
    especial: { empresas: [], fabricaEn: null, abastecimiento: 'a_pedido' },
  },
  // Estos cuatro ya estaban como piezas que arma el taller (con su tiempo de banco). En las webs figuran con marca
  // Hiper Argentina: no se cambia cómo se fabrican hasta confirmarlo.
  ...Object.fromEntries(['curva_articulada', 'codo_rectangular', 'ramal', 'sombrero_h'].map((id) => [id, { ...ABASTO_TALLER,
    notaOrigen: '[A CONFIRMAR] En la web figura con marca Hiper Argentina: confirmar si lo arma el taller de Abasto o llega hecho de HIPER.' }])),
  sombrero_chino: { ...ABASTO_TALLER, notaOrigen: '[A CONFIRMAR] No figura con ese nombre en los sitios relevados.' },
  cano_enlozado: { empresas: ['abasto'], fabricaEn: 'tercero', abastecimiento: 'stock', notaOrigen: '[A CONFIRMAR] Marca Abasto en la web; se supone comprado a un tercero.' },
  balde: { empresas: ['abasto'], fabricaEn: 'taller_abasto', abastecimiento: 'stock' },
  palangana: { empresas: ['abasto'], fabricaEn: 'taller_abasto', abastecimiento: 'stock' },
  regadera: { empresas: ['abasto'], fabricaEn: 'taller_abasto', abastecimiento: 'stock' },
};

// Palabras del mostrador (lo que dice el cliente) para el buscador. [SUPUESTO]: validarlas con los vendedores.
const SINONIMOS = [
  [/canaleta/i, ['desagüe', 'pluvial', 'zinguería', 'agua de lluvia']],
  [/babeta/i, ['remate', 'encuentro con pared', 'tapajunta']],
  [/cumbrera/i, ['caballete', 'techo a dos aguas']],
  [/limaho|limahoya/i, ['conversa', 'encuentro de techos']],
  [/caño|hiperflex/i, ['bajada', 'desagüe', 'conducto', 'tubo']],
  [/sombrer|extractor|aireador/i, ['ventilación', 'chimenea', 'tiraje', 'remate de caño']],
  [/rejilla|reja/i, ['ventilación', 'respiradero']],
  [/curva|codo|ramal|reducci|adaptaci/i, ['conexión', 'accesorio de caño']],
  [/^tapa |esquinero|rinconero|intermedia|soporte canaleta|embudo|colector/i, ['canaleta', 'accesorio de canaleta']],
  [/montante|solera|omega|pgc|pgu|buña|cantonera|ajuste|anclaje steel|cartela|tensor|conector cabio|soporte l/i, ['durlock', 'steel frame', 'drywall', 'perfil', 'construcción en seco', 'tabique', 'cielorraso']],
  [/placa|masilla/i, ['durlock', 'yeso', 'tabique', 'construcción en seco']],
  [/membrana|imperm|sellador|sika|techos|goteras|asfált/i, ['goteras', 'filtración', 'humedad', 'impermeabilizar']],
  [/aislante|fieltro|rufi|panel/i, ['aislación', 'lana de vidrio', 'térmico', 'acústico']],
  [/fogonero|parrilla|estaca|plancheta/i, ['asador', 'fogón', 'asado']],
  [/grampa/i, ['abrazadera', 'sujeción', 'fijación']],
  [/chapa (sinusoidal|trapezoidal)|polipropileno/i, ['techo', 'cubierta', 'acanalada']],
  [/weber|pastina|ceresita|promex|iggam|yeso|mortero/i, ['pegamento', 'revoque', 'cerámicos', 'albañilería']],
  [/cenefa/i, ['terminación de techo', 'alero', 'adorno']],
  [/boqueta|tronera/i, ['salida de canaleta', 'bajada']],
];

// ---------- 2) Productos relevados que YA están en el programa (no se duplican) ----------
const YA_ESTA = [
  [/^REJILLA VENTILACI[OÓ]N APROBADAS/i, 'rejilla_ventilacion'], [/^CURVAS ARTICULADAS/i, 'curva_articulada'],
  [/^SOMBRERETES APROBADOS/i, 'sombrerete_aprobado'], [/^SOMBREROS HACHE/i, 'sombrero_h'], [/^SOMBREROS SALAMANDRA/i, 'sombrero_canadiense'],
  [/^CONDUCTOS PASAPARED/i, 'conducto_pasapared'], [/^PUERTA MARCO APROBADA/i, 'puerta_marco'], [/^CERRADURA REPUESTO/i, 'cerradura_puerta_marco'],
  [/^PUERTA MARCO C\/GABINETE/i, 'puerta_marco_gabinete'], [/^RAMALES/i, 'ramal'],
  [/^BABETA SINUSOIDAL/i, 'babeta_sobre_chapa_sinusoidal'], [/^BABETA TRAPEZOIDAL/i, 'babeta_sobre_chapa_trapezoidal'],
  [/^CODO RECTANGULAR/i, 'codo_rectangular'], [/^ESQUINERO AMERICANA/i, 'std_esquinero_americana'],
  [/^CENEFA PUNTA DE LIS/i, 'cenefa_punta_lis'], [/^CENEFA FLOR DE LIS/i, 'cenefa_flor_lis'], [/^CENEFA PI[ÑN]A/i, 'cenefa_pina'],
  [/^EMBUDO COLECTOR MOLDURA/i, 'embudo_colector_moldura'], [/^EMBUDO COLECTOR RECTO/i, 'colector_recto'],
  [/^SOPORTE CANALETA/i, 'soporte_canaleta'], [/^SOPORTE PARA CA[ÑN]O RECTANGULAR/i, 'soporte_cano_rectangular'], [/^BANDAS SELLADORAS/i, 'compriband'],
  [/^Balde$/i, 'balde'], [/^Palangana$/i, 'palangana'], [/^Regadera$/i, 'regadera'], [/^Ca[ñn]o Enlozado$/i, 'cano_enlozado'],
  [/^Babetas$/i, 'babeta_l_15'], [/^Cumbreras$/i, 'cumbrera_lisa_15'], [/^1\/2 Cumbrera$/i, 'media_cumbrera'], [/^Limaholla$/i, 'limahoya'],
  [/^Troneras$/i, 'tronera'], [/^Boquetas$/i, 'boqueta_suelta'], [/^Canadiense$/i, 'sombrero_canadiense'], [/^Tipo Spiro$/i, 'sombrero_spiro'],
];

// ---------- 3) Grupos nuevos ----------
const GRUPOS_NUEVOS = [
  { id: 'accesorios_techo', nombre: 'Accesorios de canaleta y techo (estándar HIPER)' },
  { id: 'gas_ventilacion', nombre: 'Gas y ventilación (aprobados)' },
  { id: 'construccion_seco', nombre: 'Perfiles y accesorios para construcción en seco' },
  { id: 'sanitarios', nombre: 'Accesorios sanitarios y fijaciones' },
  { id: 'fogoneros', nombre: 'Fogoneros y parrillas' },
  { id: 'chapas', nombre: 'Chapas para techo' },
  { id: 'placas_aislantes', nombre: 'Placas y aislantes' },
  { id: 'quimicos_obra', nombre: 'Membranas, selladores, masillas y morteros' },
  { id: 'metalmecanica', nombre: 'Piezas metalmecánicas a medida (G-TEC)' },
  { id: 'servicios', nombre: 'Servicios industriales (G-TEC)' },
];
const GRUPO_POR_CATEGORIA = {
  'Zinguería aprobada para gas y ventilación': 'gas_ventilacion', 'Zinguería para techos y plegados especiales': 'accesorios_techo',
  'Accesorios sanitarios': 'sanitarios', 'Calefacción y fogoneros': 'fogoneros',
  'Perfiles Drywall': 'construccion_seco', 'Perfiles Steel Frame': 'construccion_seco', 'Accesorios para Steel Frame': 'construccion_seco',
  'Zinguería para techos': 'accesorios_techo', 'Accesorios': 'accesorios_techo', 'Caños, codos y curvas': 'canos', 'Artesanías': 'articulos',
  'Chapa sinusoidal': 'chapas', 'Chapa trapezoidal': 'chapas', 'Chapas polipropileno': 'chapas',
  Placas: 'placas_aislantes', Aislantes: 'placas_aislantes',
  Impermeabilizantes: 'quimicos_obra', Selladores: 'quimicos_obra', Adhesivos: 'quimicos_obra', Masillas: 'quimicos_obra', Membranas: 'quimicos_obra', 'Aditivos y morteros': 'quimicos_obra',
};

// ---------- utilidades ----------
const sinTildes = (t) => t.normalize('NFD').replace(/[̀-ͯ]/g, '');
const slug = (t) => sinTildes(t).toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 40);
const SIGLAS = ['PGC', 'PGU', 'HIPER', 'L', 'KG'];
// Solo ortografía (los sitios publican los nombres en mayúsculas y sin tilde).
const TILDES = { conicas: 'cónicas', cilindricas: 'cilíndricas', camara: 'cámara', hermeticos: 'herméticos', adaptacion: 'adaptación', angulo: 'ángulo', andres: 'Andrés', san: 'San' };
function nombreLegible(nombre) {
  if (nombre !== nombre.toUpperCase()) return nombre; // ya viene en minúsculas (sitio de Abasto)
  const bajo = nombre.toLowerCase().replace(/\s+/g, ' ').trim();
  return (bajo.charAt(0).toUpperCase() + bajo.slice(1))
    .replace(/\b([a-z]+)\b/g, (p) => (SIGLAS.includes(p.toUpperCase()) ? (p.toUpperCase() === 'HIPER' ? 'Hiper' : p.toUpperCase()) : p))
    .replace(/\( /g, '(').replace(/mt\.\)/, 'm)')
    .replace(/[A-Za-zñ]+/g, (p) => TILDES[p.toLowerCase()] ? (p[0] === p[0].toUpperCase() ? TILDES[p.toLowerCase()].replace(/^./, (c) => c.toUpperCase()) : TILDES[p.toLowerCase()]) : p);
}
function leerTsv(ruta) {
  return leer(ruta).split('\n').slice(1).filter(Boolean).map((linea) => {
    const [categoria, marca, producto, datos, url] = linea.split('\t').map((c) => c.replace(/\\(.)/g, '$1'));
    return { categoria, marca, producto, datos: datos || '', url };
  });
}
function palabrasDe(nombre, extra = []) {
  const lista = new Set(extra);
  for (const [patron, palabras] of SINONIMOS) if (patron.test(nombre)) palabras.forEach((p) => lista.add(p));
  return [...lista];
}

// ---------- armado ----------
const catalogo = JSON.parse(leer('datos/catalogo.json'));
const base = catalogo.plantillas.filter((p) => p.origen !== 'relevamiento');
const idsBase = new Set(base.map((p) => p.id));

for (const p of base) {
  const regla = BASE[p.id] || BASE._porGrupo[p.grupo];
  p.empresas = regla.empresas;
  p.fabricaEn = regla.fabricaEn;
  p.abastecimiento = regla.abastecimiento;
  if (regla.notaOrigen) p.notaOrigen = regla.notaOrigen; else delete p.notaOrigen;
  p.palabrasClave = [...new Set([...(p.palabrasClave || []), ...palabrasDe(p.nombre)])];
}

const filasTabla = [];
const generadas = [];
const idsUsados = new Set(idsBase);
function idLibre(prefijo, nombre) {
  let id = `${prefijo}_${slug(nombre)}`;
  for (let n = 2; idsUsados.has(id); n++) id = `${prefijo}_${slug(nombre)}_${n}`;
  idsUsados.add(id);
  return id;
}

/** Artículo de catálogo (se vende tal cual): sin dibujo, sin material y con código pendiente. */
function articulo({ id, nombre, grupo, variantes, presentacion, empresas, fabricaEn, marca, url, categoria }) {
  const plantilla = {
    id, nombre, grupo, tipoPieza: 'especial', elemento: id,
    textoDescripcion: variantes.length > 1 ? '{variante}' : (variantes[0] || nombre) + (presentacion !== undefined ? '[ {presentacion}]' : ''),
    usaLargo: false, calculoDesarrollo: 'unidad', generador3d: 'articulo',
    sinMaterial: true, sinDibujo: true, codigoPendiente: true,
    parametros: [],
    empresas, fabricaEn, abastecimiento: 'stock', marca,
    origen: 'relevamiento',
    referencia: `${url} (visto el ${FECHA})`,
    palabrasClave: palabrasDe(nombre, [categoria.toLowerCase()]),
    ayuda: 'Artículo de catálogo: se vende tal cual. El código lo completa administración.',
  };
  if (variantes.length > 1) {
    plantilla.parametros.push({ id: 'variante', etiqueta: 'Modelo / medida', tipo: 'opciones', valorPorDefecto: variantes[0], opciones: variantes.map((v) => ({ valor: v, etiqueta: v })) });
  }
  if (presentacion !== undefined) {
    plantilla.parametros.push({ id: 'presentacion', etiqueta: 'Presentación o medida', tipo: 'texto', valorPorDefecto: '', opcional: true, ayuda: presentacion ? `Publicado: ${presentacion}` : 'La web no publica medidas: [A CONFIRMAR].' });
  }
  return plantilla;
}

const yaEsta = (nombre) => YA_ESTA.find(([patron]) => patron.test(nombre))?.[1] || null;
const hiper = leerTsv('docs/relevamiento/hiper-argentina.tsv');
const nombresHiper = new Set(hiper.map((f) => f.producto));
const abasto = leerTsv('docs/relevamiento/abasto-soluciones.tsv');
const partir = (datos) => (datos ? datos.split(' | ').map((v) => v.trim()).filter(Boolean) : []);
// Hay fichas que en el sitio de HIPER no listan los modelos y en el de Abasto sí (mismo producto, marca Hiper Argentina).
const variantesEnAbasto = new Map(abasto.filter((f) => f.marca === 'Hiper Argentina' && f.datos).map((f) => [f.producto, partir(f.datos)]));
const porNombre = new Map();

for (const f of hiper) {
  const existente = yaEsta(f.producto);
  const variantes = f.datos ? partir(f.datos) : (variantesEnAbasto.get(f.producto) || []);
  if (existente) {
    filasTabla.push({ empresa: 'hiper', categoria: f.categoria, producto: nombreLegible(f.producto), vende: 'HIPER y Abasto', fabrica: 'HIPER', esta: `sí (${existente})`, url: f.url, variantes: variantes.length });
    continue;
  }
  // Dos fichas con el mismo nombre (p. ej. extractores eólicos chicos y grandes) son un solo producto con más modelos.
  const repetida = porNombre.get(f.producto);
  if (repetida) {
    const opciones = repetida.parametros.find((p) => p.id === 'variante').opciones;
    variantes.forEach((v) => opciones.push({ valor: v, etiqueta: v }));
    repetida.referencia += ` y ${f.url}`;
    filasTabla.push({ empresa: 'hiper', categoria: f.categoria, producto: nombreLegible(f.producto), vende: 'HIPER y Abasto', fabrica: 'HIPER', esta: `no → agregado (${repetida.id}, misma plantilla)`, url: f.url, variantes: variantes.length });
    continue;
  }
  const id = idLibre('h', f.producto);
  generadas.push(articulo({ id, nombre: nombreLegible(f.producto), grupo: GRUPO_POR_CATEGORIA[f.categoria], variantes, presentacion: variantes.length ? undefined : '', empresas: ['hiper', 'abasto'], fabricaEn: 'planta_hiper', marca: 'Hiper Argentina', url: f.url, categoria: f.categoria }));
  if (variantes.length > 1) porNombre.set(f.producto, generadas.at(-1));
  filasTabla.push({ empresa: 'hiper', categoria: f.categoria, producto: nombreLegible(f.producto), vende: 'HIPER y Abasto', fabrica: 'HIPER', esta: `no → agregado (${id})`, url: f.url, variantes: variantes.length });
}

for (const f of abasto) {
  if (f.marca === 'Hiper Argentina' && nombresHiper.has(f.producto)) continue; // ya contado en el sitio de HIPER
  const existente = yaEsta(f.producto);
  const propio = f.marca === 'Abasto';
  const deHiper = f.marca === 'Hiper Argentina';
  const vende = deHiper ? 'Abasto (marca Hiper Argentina)' : 'Abasto';
  const fabrica = deHiper ? 'HIPER' : (propio ? 'Abasto (marca propia) [A CONFIRMAR dónde]' : 'tercero (reventa)');
  if (existente) {
    filasTabla.push({ empresa: 'abasto', categoria: f.categoria, producto: f.producto, vende, fabrica, esta: `sí (${existente})`, url: f.url, variantes: 0 });
    continue;
  }
  const esCanoHiper = deHiper && /^CA[ÑN]OS/i.test(f.producto);
  const variantes = (deHiper || propio) ? partir(f.datos) : [];
  const id = idLibre(deHiper ? 'h' : 'ab', f.producto);
  generadas.push(articulo({
    id, nombre: nombreLegible(f.producto), grupo: GRUPO_POR_CATEGORIA[f.categoria] || 'articulos', variantes,
    presentacion: variantes.length ? undefined : (deHiper || propio ? '' : f.datos),
    empresas: deHiper ? ['hiper', 'abasto'] : ['abasto'],
    fabricaEn: deHiper ? 'planta_hiper' : (propio ? 'taller_abasto' : 'tercero'),
    marca: deHiper ? 'Hiper Argentina' : (propio ? 'Abasto' : null), url: f.url, categoria: f.categoria,
  }));
  if (propio) generadas.at(-1).notaOrigen = '[A CONFIRMAR] Marca Abasto en la web; no se publica dónde se fabrica.';
  filasTabla.push({ empresa: 'abasto', categoria: f.categoria, producto: f.producto, vende, fabrica, esta: `${esCanoHiper ? 'en parte (cano, a medida) → ' : 'no → '}agregado (${id})`, url: f.url, variantes: variantes.length });
}

// ---------- G-TEC: servicios y pieza metalmecánica a medida ----------
const gtec = JSON.parse(leer('docs/relevamiento/g-tec.json'));
// Materiales y espesores en mm: una sola lista, en datos/materiales.json → industriales.
const industriales = JSON.parse(leer('datos/materiales.json')).industriales;
const deGtec = (lista) => lista.filter((x) => x.empresas.includes('gtec'));
const materialesGtec = deGtec(industriales.materiales).map((m) => m.nombre);
const espesoresGtec = deGtec(industriales.espesoresMm).map((e) => e.mm);
const opcionesMaterial = materialesGtec.concat('otro').map((m) => ({ valor: m, etiqueta: m }));
const coma = (numero) => String(numero).replace('.', ',');
const campoPlano = { id: 'plano', etiqueta: 'Plano o archivo (nombre o enlace)', tipo: 'texto', valorPorDefecto: '', opcional: true, ayuda: 'Por ejemplo el nombre del PDF o DXF, o el enlace de Drive. El archivo no se guarda en el programa.' };
for (const s of gtec.servicios) {
  idsUsados.add(s.id);
  generadas.push({
    id: s.id, nombre: s.nombre, grupo: 'servicios', tipoPieza: 'servicio', elemento: s.id,
    textoDescripcion: `${s.nombre}: {alcance}[ en {material}][ esp {espesorMm} mm] ({lugar})[ plano {plano}]`,
    usaLargo: false, calculoDesarrollo: 'unidad', generador3d: 'articulo',
    sinMaterial: true, sinDibujo: true, codigoPendiente: true, cantidadDecimal: true, aMedida: true,
    parametros: [
      { id: 'alcance', etiqueta: 'Alcance (qué hay que hacer)', tipo: 'texto', valorPorDefecto: '', ayuda: s.dato },
      { id: 'unidad', etiqueta: 'Se mide en', tipo: 'opciones', valorPorDefecto: 'hora', opciones: [{ valor: 'hora', etiqueta: 'horas' }, { valor: 'pieza', etiqueta: 'piezas' }, { valor: 'metro', etiqueta: 'metros' }, { valor: 'global', etiqueta: 'trabajo completo' }] },
      { id: 'lugar', etiqueta: 'Lugar', tipo: 'opciones', valorPorDefecto: 'en planta G-TEC', opciones: [{ valor: 'en planta G-TEC', etiqueta: 'en la planta de G-TEC' }, { valor: 'en planta del cliente', etiqueta: 'en la planta del cliente' }] },
      { id: 'material', etiqueta: 'Material', tipo: 'opciones', valorPorDefecto: '', opcional: true, opciones: [{ valor: '', etiqueta: '— no corresponde —' }].concat(opcionesMaterial) },
      {
        id: 'espesorMm', etiqueta: 'Espesor', unidad: 'mm', tipo: 'numero', valorPorDefecto: '', opcional: true, minimo: 0,
        maximo: s.limites.espesorMaxMm, avisoDesde: s.limites.espesorAvisoMm,
        avisoTexto: s.limites.espesorAvisoMm ? `${s.nombre}: más de ${coma(s.limites.espesorAvisoMm)} mm hay que confirmarlo con G-TEC` : undefined,
        sugeridos: espesoresGtec,
        ayuda: s.limites.espesorMaxMm ? `G-TEC publica hasta ${coma(s.limites.espesorMaxMm)} mm.` : '',
      },
      campoPlano,
    ],
    limites: s.limites, maquina: s.maquina,
    empresas: ['gtec'], fabricaEn: 'planta_gtec', abastecimiento: 'a_pedido', marca: 'G-TEC',
    origen: 'relevamiento', notaOrigen: s.aConfirmar ? `[A CONFIRMAR] ${s.aConfirmar}` : undefined,
    referencia: `${gtec.fuente} (visto el ${FECHA})`, palabrasClave: s.palabrasClave.concat(['servicio', 'g-tec']),
    ayuda: `Servicio de G-TEC. ${s.dato} El código lo completa administración.`,
  });
  filasTabla.push({ empresa: 'gtec', categoria: 'Servicios', producto: s.nombre, vende: 'G-TEC', fabrica: 'G-TEC', esta: `no → agregado (${s.id})`, url: gtec.fuente, variantes: 0 });
}
idsUsados.add('gt_pieza_a_medida');
generadas.push({
  id: 'gt_pieza_a_medida', nombre: 'Pieza metalmecánica a medida', grupo: 'metalmecanica', tipoPieza: 'metalmecanica', elemento: 'gt_pieza_a_medida',
  textoDescripcion: '{descripcion} {dimensiones} {material} esp {espesorMm} mm ({procesos})[ plano {plano}]',
  usaLargo: false, calculoDesarrollo: 'unidad', generador3d: 'articulo',
  sinMaterial: true, sinDibujo: true, codigoPendiente: true, aMedida: true,
  parametros: [
    { id: 'descripcion', etiqueta: 'Qué es', tipo: 'texto', valorPorDefecto: '', ayuda: 'Por ejemplo: soporte, tapa, caja, bandeja.' },
    { id: 'dimensiones', etiqueta: 'Medidas (mm)', tipo: 'texto', valorPorDefecto: '', ayuda: 'Largo × ancho × alto, o "según plano".' },
    { id: 'material', etiqueta: 'Material', tipo: 'opciones', valorPorDefecto: materialesGtec[0], opciones: opcionesMaterial },
    { id: 'espesorMm', etiqueta: 'Espesor', unidad: 'mm', tipo: 'numero', valorPorDefecto: '', minimo: 0, sugeridos: espesoresGtec, ayuda: 'En milímetros (no en calibre).' },
    { id: 'procesos', etiqueta: 'Procesos', tipo: 'multiple', valorPorDefecto: ['corte láser'], opciones: [
      { valor: 'corte láser', etiqueta: 'corte láser', espesorMaxMm: 20, maquina: 'gtec_laser' },
      { valor: 'chorro de agua', etiqueta: 'chorro de agua', espesorMaxMm: 150, maquina: 'gtec_chorro' },
      { valor: 'plegado CNC', etiqueta: 'plegado CNC', espesorMaxMm: 12.7, espesorAvisoMm: 6.3, maquina: 'gtec_plegado' },
      { valor: 'mecanizado', etiqueta: 'mecanizado CNC', maquina: 'gtec_mecanizado' },
      { valor: 'soldadura', etiqueta: 'soldadura', maquina: 'gtec_soldadura' },
    ] },
    campoPlano,
  ],
  maquina: 'gtec_laser',
  empresas: ['gtec'], fabricaEn: 'planta_gtec', abastecimiento: 'a_pedido', marca: 'G-TEC',
  origen: 'relevamiento', referencia: `${gtec.fuente} (visto el ${FECHA})`,
  palabrasClave: ['pieza', 'a medida', 'plano', 'metalúrgica', 'g-tec', 'chapa gruesa', 'soporte', 'estructura'],
  ayuda: 'No lleva dibujo por tramos: descripción, medidas, material y espesor en mm, con el plano si lo hay. El código lo completa administración.',
});
filasTabla.push({ empresa: 'gtec', categoria: 'Fabricación a medida', producto: 'Pieza metalmecánica a medida (prototipos y series)', vende: 'G-TEC', fabrica: 'G-TEC', esta: 'no → agregado (gt_pieza_a_medida)', url: gtec.fuente, variantes: 0 });

// ---------- escribir catalogo.json ----------
// Los grupos nuevos van antes de "especial" (que queda último).
const grupos = catalogo.grupos.filter((g) => g.id !== 'especial' && !GRUPOS_NUEVOS.some((n) => n.id === g.id));
catalogo.grupos = grupos.concat(GRUPOS_NUEVOS, catalogo.grupos.filter((g) => g.id === 'especial'));
catalogo._leeme = 'Plantillas de piezas y productos de las tres empresas del grupo. "empresas" = quién lo vende (vacío = todas); "fabricaEn" = planta (datos/empresas.json), "tercero" (reventa) o null (la planta de quien vende); '
  + '"abastecimiento" = "stock" (se entrega de depósito) o "a_pedido" (se fabrica para la nota). Las medidas con supuesto: true son de ejemplo. '
  + 'Lo que tiene "origen": "relevamiento" lo escribe herramientas/cargar-relevamiento.js desde docs/relevamiento (nombres y variantes publicados por cada empresa, sin inventar): '
  + 'no tiene código de facturación, por eso sale "código pendiente". Fuentes: docs/CATALOGO_GRUPO.md.';
catalogo.plantillas = base.concat(generadas.map((p) => JSON.parse(JSON.stringify(p))));
writeFileSync(join(RAIZ, 'datos/catalogo.json'), `${JSON.stringify(catalogo, null, 2)}\n`);

// ---------- tabla de docs/CATALOGO_GRUPO.md ----------
const NOMBRES = { hiper: 'HIPER Argentina (hiperargentina.com)', abasto: 'Abasto Soluciones (abastosoluciones.com.ar), lo que no está en el sitio de HIPER', gtec: 'G-TEC (gtecdesarrollosyservicios.com)' };
let tabla = '';
for (const empresa of ['hiper', 'abasto', 'gtec']) {
  const filas = filasTabla.filter((f) => f.empresa === empresa);
  tabla += `\n### ${NOMBRES[empresa]}: ${filas.length} productos o servicios\n\n| Producto o servicio | Categoría en la web | Variantes publicadas | Lo vende | Lo fabrica | ¿Ya estaba en el programa? | Fuente |\n|---|---|---|---|---|---|---|\n`;
  for (const f of filas) tabla += `| ${f.producto} | ${f.categoria} | ${f.variantes || '—'} | ${f.vende} | ${f.fabrica} | ${f.esta} | [ficha](${f.url}) |\n`;
}
const rutaDoc = join(RAIZ, 'docs/CATALOGO_GRUPO.md');
let doc;
try { doc = readFileSync(rutaDoc, 'utf8'); } catch { doc = '<!-- TABLA:inicio -->\n<!-- TABLA:fin -->\n'; }
doc = doc.replace(/<!-- TABLA:inicio -->[\s\S]*<!-- TABLA:fin -->/, `<!-- TABLA:inicio -->\n${tabla}\n<!-- TABLA:fin -->`);
writeFileSync(rutaDoc, doc);

const cuenta = (e) => filasTabla.filter((f) => f.empresa === e).length;
console.log(`Catálogo: ${base.length} plantillas de antes + ${generadas.length} del relevamiento = ${catalogo.plantillas.length} (${catalogo.grupos.length} grupos).`);
console.log(`Tabla: HIPER ${cuenta('hiper')}, Abasto ${cuenta('abasto')}, G-TEC ${cuenta('gtec')}; ya estaban ${filasTabla.filter((f) => f.esta.startsWith('sí')).length}.`);
