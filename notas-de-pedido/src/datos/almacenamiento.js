// =============================================================
// almacenamiento.js
// ÚNICA PUERTA para guardar y leer datos (notas, contadores, configuración).
//
// Hoy guarda en el navegador (localStorage = un "cajón" de texto que el
// navegador conserva aunque se cierre la página).
// Mañana se reemplaza por llamadas a Google Apps Script (google.script.run)
// SIN tocar las pantallas: por eso TODAS las funciones son async
// (devuelven una "promesa": un resultado que llega un poco después).
//
// Regla: ningún otro archivo usa localStorage directamente.
// =============================================================

import { asignarNumeroNP, contadoresDesdeSucursales } from '../logica/numeracion.js';
import { crearId } from '../logica/renglones.js';
import { completarFotoVieja } from '../logica/fotoCalculo.js';

const PREFIJO = 'notasPedido.';

// "Motor" = dónde se guarda. Por defecto, el localStorage del navegador.
// En las pruebas se reemplaza por uno en memoria (ver configurarAlmacenamiento).
let motor = globalThis.localStorage ?? null;

// Cómo se leen los archivos de /datos. En el navegador, con fetch.
let leerArchivoDatos = async (nombreArchivo) => {
  const respuesta = await fetch(`./datos/${nombreArchivo}`, { cache: 'no-cache' });
  if (!respuesta.ok) {
    throw new Error(`No se pudo leer datos/${nombreArchivo}`);
  }
  return respuesta.json();
};

/**
 * Permite cambiar el motor y el lector de archivos (se usa en las pruebas).
 * @param {{motor?: {getItem, setItem, removeItem}, leerArchivo?: (nombre) => Promise<object>}} opciones
 */
export function configurarAlmacenamiento(opciones = {}) {
  if (opciones.motor) motor = opciones.motor;
  if (opciones.leerArchivo) leerArchivoDatos = opciones.leerArchivo;
}

// ---------- utilidades internas ----------

async function leer(clave, valorPorDefecto) {
  if (!motor) throw new Error('No hay dónde guardar datos (localStorage no disponible)');
  const texto = motor.getItem(PREFIJO + clave);
  if (texto === null || texto === undefined) {
    return valorPorDefecto;
  }
  try {
    return JSON.parse(texto);
  } catch {
    return valorPorDefecto;
  }
}

async function guardar(clave, valor) {
  if (!motor) throw new Error('No hay dónde guardar datos (localStorage no disponible)');
  try {
    motor.setItem(PREFIJO + clave, JSON.stringify(valor));
  } catch (error) {
    // El navegador da unos 5 MB por página: con muchos datos de demostración se puede llenar.
    if (error?.name === 'QuotaExceededError' || /quota/i.test(String(error?.message))) {
      throw new Error('No queda lugar en el navegador para guardar. Borrá los datos de demostración (Producción > Demo) o bajá una copia y borrá notas viejas.');
    }
    throw error;
  }
}

// =============================================================
// DATOS BASE (archivos de /datos, con los cambios hechos en Configuración)
// =============================================================

/**
 * Carga todos los datos que necesita el programa.
 * @returns {Promise<{config, sucursales, vendedores, materiales, catalogo, codigos, glosario}>}
 */
export async function cargarDatosBase() {
  const [config, sucursales, vendedores, materiales, catalogo, codigosArchivo, glosario, tiemposMtm, produccion] = await Promise.all([
    leerArchivoDatos('config.json'),
    leerArchivoDatos('sucursales.json'),
    leerArchivoDatos('vendedores.json'),
    leerArchivoDatos('materiales.json'),
    leerArchivoDatos('catalogo.json'),
    leerArchivoDatos('codigos.json'),
    leerArchivoDatos('glosario.json'),
    leerArchivoDatos('tiempos-mtm.json'),
    leerArchivoDatos('produccion.json'),
  ]);

  // Si en Configuración se importó una tabla de códigos, manda esa.
  const codigosImportados = await leer('codigosImportados', null);
  // Si en Configuración se editaron sucursales (nombre, letra), mandan esas.
  const sucursalesEditadas = await leer('sucursalesEditadas', null);
  // Operarios editados en Producción (nombre, turno, máquinas, activo).
  const operariosEditados = await leer('operariosEditados', null);
  const criteriosAgrupamiento = await leer('criteriosAgrupamiento', null);

  return {
    config,
    sucursales: sucursalesEditadas || sucursales.sucursales,
    vendedores: vendedores.vendedores,
    materiales,
    catalogo,
    codigos: codigosImportados || codigosArchivo,
    glosario: glosario.terminos,
    tiemposMtm,
    produccion: {
      ...produccion,
      operarios: operariosEditados || produccion.operarios,
      agrupamiento: criteriosAgrupamiento || produccion.agrupamiento,
    },
  };
}

// =============================================================
// SESIÓN (quién está usando el programa y en qué sucursal trabaja hoy)
// =============================================================

/**
 * rol: 'comercial' (vendedor, carga notas) | 'jefe' (jefe de producción) | 'operario'.
 * Las sesiones guardadas antes de que existieran los roles son de comercial.
 * @returns {Promise<{rol: string, vendedorId: string|null, sucursalHoyId: string|null, operarioId: string|null}>}
 */
export async function leerSesion() {
  const sesion = await leer('sesion', { vendedorId: null, sucursalHoyId: null });
  return { rol: sesion.vendedorId ? 'comercial' : null, operarioId: null, ...sesion };
}

export async function guardarSesion(sesion) {
  await guardar('sesion', sesion);
}

// =============================================================
// CONFIGURACIÓN EDITABLE
// =============================================================

export async function guardarSucursales(listaSucursales) {
  await guardar('sucursalesEditadas', listaSucursales);
}

export async function guardarTablaCodigos(filas) {
  await guardar('codigosImportados', filas);
}

/** Vuelve a usar datos/codigos.json (borra la tabla importada). */
export async function descartarTablaCodigosImportada() {
  motor.removeItem(PREFIJO + 'codigosImportados');
}

// =============================================================
// NUMERACIÓN (contadores por sucursal)
// =============================================================

/**
 * Últimos números usados, por sucursal. Arranca de sucursales.json y después
 * se guarda cada emisión.
 * @returns {Promise<object>} { idSucursal: últimoNúmero }
 */
export async function leerContadores(sucursales) {
  const guardados = await leer('contadores', null);
  const iniciales = contadoresDesdeSucursales(sucursales);
  return { ...iniciales, ...(guardados || {}) };
}

/** Configuración: fija el último número usado (para seguir desde el talonario de papel). */
export async function fijarUltimoNumero(sucursales, sucursalId, ultimoNumero) {
  const contadores = await leerContadores(sucursales);
  contadores[sucursalId] = Number(ultimoNumero) || 0;
  await guardar('contadores', contadores);
  return contadores;
}

// =============================================================
// NOTAS DE PEDIDO
// =============================================================

/** Crea una nota vacía en estado borrador (todavía SIN número). */
export async function crearNotaVacia({ sucursalId, vendedorId }) {
  return {
    id: crearId('nota'),
    estado: 'borrador',
    numero: null,              // se asigna al emitir
    sucursalId,
    vendedorId,
    fechaCreacion: new Date().toISOString(),
    fechaEmision: null,
    cliente: '',
    factura: '',
    fechaEntrega: null,        // 'aaaa-mm-dd' comprometida con el cliente (la usa producción)
    prioridad: 'normal',       // 'normal' | 'urgente'
    mostrar3d: 'auto',         // 'auto' | 'si' | 'no' (cada renglón puede elegir otra cosa)
    renglones: [],
  };
}

/**
 * Lista notas, con filtros opcionales.
 * @param {{sucursalId?, estado?, texto?, desde?, hasta?}} filtros
 *   texto busca en cliente, número y factura. desde/hasta: 'aaaa-mm-dd'.
 */
export async function listarNotas(filtros = {}) {
  const notas = await leer('notas', []);
  const texto = String(filtros.texto || '').toLowerCase().trim();
  return notas
    .filter((n) => !filtros.sucursalId || n.sucursalId === filtros.sucursalId)
    .filter((n) => !filtros.estado || n.estado === filtros.estado)
    .filter((n) => {
      if (!texto) return true;
      return [n.cliente, n.factura, n.numero].some((campo) => String(campo ?? '').toLowerCase().includes(texto));
    })
    .filter((n) => {
      const fecha = (n.fechaEmision || n.fechaCreacion || '').slice(0, 10);
      if (filtros.desde && fecha < filtros.desde) return false;
      if (filtros.hasta && fecha > filtros.hasta) return false;
      return true;
    })
    .sort((a, b) => String(b.fechaEmision || b.fechaCreacion).localeCompare(String(a.fechaEmision || a.fechaCreacion)));
}

export async function leerNota(id) {
  const notas = await leer('notas', []);
  return notas.find((n) => n.id === id) || null;
}

/** Guarda (crea o actualiza) un borrador. No deja modificar una nota ya emitida. */
export async function guardarBorrador(nota) {
  const notas = await leer('notas', []);
  const posicion = notas.findIndex((n) => n.id === nota.id);
  if (posicion >= 0 && notas[posicion].estado === 'emitida') {
    throw new Error('La nota ya fue emitida y no se puede modificar');
  }
  const copia = { ...nota, estado: 'borrador', fechaModificacion: new Date().toISOString() };
  if (posicion >= 0) {
    notas[posicion] = copia;
  } else {
    notas.push(copia);
  }
  await guardar('notas', notas);
  return copia;
}

/**
 * Emite la nota: le asigna el próximo número de SU sucursal y la marca como emitida.
 * (La validación de la nota la hace la pantalla antes, con logica/validaciones.js.)
 * En la versión Apps Script esto se hace en el servidor con LockService,
 * para que dos vendedores no saquen el mismo número a la vez.
 */
export async function emitirNota(nota, sucursales) {
  const notas = await leer('notas', []);
  const existente = notas.find((n) => n.id === nota.id);
  if (existente && existente.estado === 'emitida') {
    throw new Error('La nota ya fue emitida');
  }

  const contadores = await leerContadores(sucursales);
  const { numero, contadores: actualizados } = asignarNumeroNP(contadores, nota.sucursalId);

  const emitida = { ...nota, estado: 'emitida', numero, fechaEmision: new Date().toISOString() };
  const posicion = notas.findIndex((n) => n.id === nota.id);
  if (posicion >= 0) {
    notas[posicion] = emitida;
  } else {
    notas.push(emitida);
  }

  await guardar('contadores', actualizados);
  await guardar('notas', notas);
  return emitida;
}

/** Borra un borrador (las notas emitidas no se borran). */
export async function borrarBorrador(id) {
  const notas = await leer('notas', []);
  const nota = notas.find((n) => n.id === id);
  if (nota && nota.estado === 'emitida') {
    throw new Error('Las notas emitidas no se borran');
  }
  await guardar('notas', notas.filter((n) => n.id !== id));
}

/**
 * Cambia SOLO cómo se muestra el 3D de una nota (también si ya está emitida: es presentación,
 * no cambia lo facturado). Queda anotado en el historial de producción.
 * @param {{mostrar3d?: string, renglones?: object}} cambios  renglones = { renglonId: true|false|null }
 */
export async function cambiarVista3d(notaId, cambios, quien = null) {
  const notas = await leer('notas', []);
  const nota = notas.find((n) => n.id === notaId);
  if (!nota) throw new Error('No se encontró la nota');
  if (cambios.mostrar3d) nota.mostrar3d = cambios.mostrar3d;
  for (const [renglonId, valor] of Object.entries(cambios.renglones || {})) {
    const renglon = nota.renglones.find((r) => r.id === renglonId);
    if (renglon) renglon.mostrar3d = valor;
  }
  await guardar('notas', notas);
  if (nota.estado === 'emitida') {
    await anotarEnHistorial(notaId, quien, 'vista 3D', JSON.stringify(cambios));
  }
  return nota;
}

// =============================================================
// PRODUCCIÓN (registros por nota, lotes, incidencias, parámetros)
// La lógica está en logica/produccion.js; acá solo se guarda y se lee.
// =============================================================

/** { notaId: registro } (ver logica/produccion.js → registroVacio). */
export async function leerRegistros() {
  return leer('produccion', {});
}

/** Guarda (crea o reemplaza) varios registros de una vez. */
export async function guardarRegistros(lista) {
  const registros = await leer('produccion', {});
  for (const registro of lista) registros[registro.notaId] = registro;
  await guardar('produccion', registros);
  return registros;
}

async function anotarEnHistorial(notaId, quien, accion, detalle) {
  const registros = await leer('produccion', {});
  registros[notaId] ||= { notaId, demo: false, orden: null, renglones: {}, historial: [] };
  registros[notaId].historial.push({ hora: new Date().toISOString(), rol: quien?.rol || null, usuario: quien?.nombre || null, accion, detalle });
  await guardar('produccion', registros);
}

/** Lotes guardados por el jefe: [{id, nombre, claves: ['notaId/renglonId'], aceptado}]. Guarda la versión anterior para "deshacer". */
export async function leerLotes() {
  return leer('lotes', []);
}

export async function guardarLotes(lotes) {
  await guardar('lotesAnterior', await leer('lotes', []));
  await guardar('lotes', lotes);
}

/** Vuelve a la versión de los lotes anterior al último cambio. */
export async function deshacerLotes() {
  const anterior = await leer('lotesAnterior', null);
  if (!anterior) throw new Error('No hay un cambio para deshacer');
  await guardar('lotes', anterior);
  motor.removeItem(PREFIJO + 'lotesAnterior');
  return anterior;
}

/** Incidencias, retrabajos y demoras: [{id, hora, tipo, causa, notaId, renglonId, operarioId, minutosPerdidos, descripcion}]. */
export async function leerIncidencias() {
  return leer('incidencias', []);
}

export async function agregarIncidencia(incidencia) {
  if (!incidencia.tipo || !incidencia.causa) throw new Error('Elegí el tipo y la causa de la incidencia');
  const lista = await leer('incidencias', []);
  const nueva = { id: crearId('inc'), hora: new Date().toISOString(), demo: false, ...incidencia };
  lista.push(nueva);
  await guardar('incidencias', lista);
  if (nueva.notaId) await anotarEnHistorial(nueva.notaId, null, `incidencia: ${nueva.tipo}`, `${nueva.causa}${nueva.descripcion ? ` – ${nueva.descripcion}` : ''}`);
  return nueva;
}

/** Cambios del jefe a los parámetros de tiempos: {parametros: {clave: valor}, productosSinPerfil?, fuente, fecha}. */
export async function leerCambiosTiempos() {
  return leer('cambiosTiempos', null);
}

export async function guardarCambiosTiempos(cambios) {
  await guardar('cambiosTiempos', { ...cambios, fecha: new Date().toISOString() });
}

/** Vuelve a los valores del estudio (datos/tiempos-mtm.json). */
export async function descartarCambiosTiempos() {
  motor.removeItem(PREFIJO + 'cambiosTiempos');
}

export async function guardarOperarios(lista) {
  await guardar('operariosEditados', lista);
}

export async function guardarCriteriosAgrupamiento(criterios) {
  await guardar('criteriosAgrupamiento', criterios);
}

// =============================================================
// DATOS DE DEMOSTRACIÓN (marcados demo: true; no tocan los contadores reales)
// =============================================================

export async function hayDemo() {
  return (await leer('notas', [])).some((n) => n.demo);
}

/** Agrega los datos de demostración. Si ya hay, primero hay que borrarlos. */
export async function cargarDemo({ notas, registros }) {
  const actuales = await leer('notas', []);
  if (actuales.some((n) => n.demo)) throw new Error('Ya hay datos de demostración cargados: borralos primero');
  if (notas.some((n) => !n.demo)) throw new Error('Los datos de demostración tienen que estar marcados como demo');
  await guardar('notas', actuales.concat(notas));
  await guardarRegistros(Object.values(registros));
}

/** Borra SOLO lo marcado como demo (notas, registros, incidencias y lotes que las usan). */
export async function borrarDemo() {
  const notas = await leer('notas', []);
  const idsDemo = new Set(notas.filter((n) => n.demo).map((n) => n.id));
  await guardar('notas', notas.filter((n) => !n.demo));
  const registros = await leer('produccion', {});
  for (const id of Object.keys(registros)) if (registros[id].demo || idsDemo.has(id)) delete registros[id];
  await guardar('produccion', registros);
  await guardar('incidencias', (await leer('incidencias', [])).filter((i) => !i.demo && !idsDemo.has(i.notaId)));
  const sinDemo = (lotes) => (lotes || []).map((l) => ({ ...l, claves: l.claves.filter((c) => !idsDemo.has(c.split('/')[0])) })).filter((l) => l.claves.length);
  await guardar('lotes', sinDemo(await leer('lotes', [])));
  motor.removeItem(PREFIJO + 'lotesAnterior');
  return idsDemo.size;
}

// =============================================================
// MIGRACIÓN (notas guardadas con versiones anteriores del programa)
// =============================================================

export const VERSION_DATOS = 2;

/**
 * Versión 2: las notas emitidas antes guardaban la foto sin la cantidad de chapas.
 * Se completa (sin tocar código ni descripción) y se agregan los campos nuevos de la nota
 * (fecha de entrega, prioridad, vista 3D). Se hace una sola vez.
 */
export async function migrarDatos(datos) {
  const version = await leer('versionDatos', 1);
  if (version >= VERSION_DATOS) return { migradas: 0 };
  const notas = await leer('notas', []);
  let migradas = 0;
  for (const nota of notas) {
    nota.fechaEntrega ??= null;
    nota.prioridad ??= 'normal';
    nota.mostrar3d ??= 'auto';
    for (const renglon of nota.renglones || []) {
      if (renglon.calculado && !(renglon.calculado.version >= 2)) {
        renglon.calculado = completarFotoVieja(renglon, renglon.calculado, datos.config);
        migradas += 1;
      }
    }
  }
  await guardar('notas', notas);
  await guardar('versionDatos', VERSION_DATOS);
  return { migradas };
}

// =============================================================
// COPIA DE SEGURIDAD
// =============================================================

/** Todo lo guardado (notas, producción, configuración) en un solo objeto, para bajarlo como archivo. */
export async function exportarTodo() {
  return {
    exportado: new Date().toISOString(),
    versionDatos: await leer('versionDatos', 1),
    notas: await leer('notas', []),
    contadores: await leer('contadores', {}),
    sucursalesEditadas: await leer('sucursalesEditadas', null),
    codigosImportados: await leer('codigosImportados', null),
    produccion: await leer('produccion', {}),
    lotes: await leer('lotes', []),
    incidencias: await leer('incidencias', []),
    cambiosTiempos: await leer('cambiosTiempos', null),
    operariosEditados: await leer('operariosEditados', null),
    criteriosAgrupamiento: await leer('criteriosAgrupamiento', null),
  };
}

/** Borra las notas, los contadores y lo de producción (para empezar de cero después de probar). La configuración queda. */
export async function borrarNotasYContadores() {
  for (const clave of ['notas', 'contadores', 'produccion', 'lotes', 'lotesAnterior', 'incidencias']) motor.removeItem(PREFIJO + clave);
}
