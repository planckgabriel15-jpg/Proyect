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
  motor.setItem(PREFIJO + clave, JSON.stringify(valor));
}

// =============================================================
// DATOS BASE (archivos de /datos, con los cambios hechos en Configuración)
// =============================================================

/**
 * Carga todos los datos que necesita el programa.
 * @returns {Promise<{config, sucursales, vendedores, materiales, catalogo, codigos, glosario}>}
 */
export async function cargarDatosBase() {
  const [config, sucursales, vendedores, materiales, catalogo, codigosArchivo, glosario] = await Promise.all([
    leerArchivoDatos('config.json'),
    leerArchivoDatos('sucursales.json'),
    leerArchivoDatos('vendedores.json'),
    leerArchivoDatos('materiales.json'),
    leerArchivoDatos('catalogo.json'),
    leerArchivoDatos('codigos.json'),
    leerArchivoDatos('glosario.json'),
  ]);

  // Si en Configuración se importó una tabla de códigos, manda esa.
  const codigosImportados = await leer('codigosImportados', null);
  // Si en Configuración se editaron sucursales (nombre, letra), mandan esas.
  const sucursalesEditadas = await leer('sucursalesEditadas', null);

  return {
    config,
    sucursales: sucursalesEditadas || sucursales.sucursales,
    vendedores: vendedores.vendedores,
    materiales,
    catalogo,
    codigos: codigosImportados || codigosArchivo,
    glosario: glosario.terminos,
  };
}

// =============================================================
// SESIÓN (quién está usando el programa y en qué sucursal trabaja hoy)
// =============================================================

/** @returns {Promise<{vendedorId: string|null, sucursalHoyId: string|null}>} */
export async function leerSesion() {
  return leer('sesion', { vendedorId: null, sucursalHoyId: null });
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
