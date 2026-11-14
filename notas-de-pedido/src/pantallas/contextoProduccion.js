// =============================================================
// contextoProduccion.js
// Junta todo lo que usan las pantallas de producción: notas emitidas, registros,
// lotes, incidencias, modelo de tiempos (con los cambios del jefe) y los trabajos
// ya calculados. Se arma de nuevo cada vez que algo cambia (es rápido: 500 notas
// tardan menos de medio segundo).
// =============================================================

import { estado, vendedorActual, plantaDeSesion } from './estado.js';
import * as almacenamiento from '../datos/almacenamiento.js';
import { prepararModelo } from '../logica/tiempos.js';
import { armarTrabajos, notasConEstado, minutosEnLotes, diaDe } from '../logica/produccion.js';
import { rearmarLotes } from '../logica/agrupamiento.js';

/** Quién hace el cambio (para el historial). */
export function quienSoy() {
  const s = estado.sesion || {};
  const prod = estado.datos.produccion;
  if (s.rol === 'operario') {
    const op = prod.operarios.find((o) => o.id === s.operarioId);
    return { rol: 'operario', nombre: op?.nombre || s.operarioId, operarioId: s.operarioId };
  }
  if (s.rol === 'jefe') return { rol: 'jefe', nombre: 'Jefe de producción' };
  return { rol: 'comercial', nombre: vendedorActual()?.nombre || 'Comercial' };
}

export function esJefe() {
  return estado.sesion?.rol === 'jefe';
}

/** Modelo de tiempos con los cambios guardados. */
export async function cargarModelo() {
  const cambios = await almacenamiento.leerCambiosTiempos();
  return { modelo: prepararModelo(estado.datos.tiemposMtm, estado.datos.config, cambios), cambios };
}

/**
 * prod = datos/produccion.json con los operarios y máquinas de la planta que se mira; prodCompleto = todo.
 * @returns {Promise<{hoy, datos, prod, prodCompleto, planta, modelo, cambios, notas, registros, lotesGuardados, lotes,
 *   trabajos, notasEstado, incidencias, porClave: Map}>}
 */
export async function cargarContexto(opciones = {}) {
  const datos = estado.datos;
  // El comercial ve el estado de SUS notas (no el tablero de todo el grupo), salvo que pida verlas todas.
  const soloMias = opciones.soloMias ?? (estado.sesion?.rol === 'comercial' && !estado.sesion.verTodasLasNotas);
  const { modelo, cambios } = await cargarModelo();
  const [todasLasNotas, registros, lotesGuardados, incidencias] = await Promise.all([
    almacenamiento.listarNotas({ estado: 'emitida' }),
    almacenamiento.leerRegistros(),
    almacenamiento.leerLotes(),
    almacenamiento.leerIncidencias(),
  ]);
  const notas = soloMias ? todasLasNotas.filter((n) => n.vendedorId === estado.sesion.vendedorId) : todasLasNotas;
  // Cada planta ve SUS trabajos, operarios y máquinas (el jefe puede elegir "todas las plantas").
  const planta = plantaDeSesion();
  const dePlanta = (x) => !planta || (x.planta || 'taller_abasto') === planta;
  const prodCompleto = datos.produccion;
  const prod = { ...prodCompleto, operarios: prodCompleto.operarios.filter(dePlanta), maquinas: prodCompleto.maquinas.filter(dePlanta) };
  const trabajos = armarTrabajos(notas, registros, { datos, modelo, prod: prodCompleto }).filter((t) => !planta || t.planta === planta);
  const tolerancia = prod.agrupamiento.criterios?.desarrollo?.toleranciaMm ?? 0;
  // Los lotes guardados por el jefe (aceptados o editados) se rearman con los trabajos pendientes.
  const pendientes = trabajos.filter((t) => !t.hecha);
  const lotes = rearmarLotes(lotesGuardados, pendientes, tolerancia);
  const enLote = minutosEnLotes(lotes, tolerancia);
  for (const t of trabajos) {
    const dato = enLote.get(t.clave);
    t.minutosEnLote = dato ? dato.minutosEnLote : t.minutos;
    t.ahorroLoteMin = dato ? dato.ahorroMin : 0;
    t.loteActual = dato?.loteId || null;
  }
  const hoy = diaDe(new Date());
  return {
    hoy, datos, prod, prodCompleto, planta, soloMias, modelo, cambios, notas, registros, lotesGuardados, lotes, trabajos,
    notasEstado: notasConEstado(trabajos, hoy), incidencias,
    porClave: new Map(trabajos.map((t) => [t.clave, t])),
  };
}

/** Nombre del operario. */
export function nombreOperario(id) {
  return estado.datos.produccion.operarios.find((o) => o.id === id)?.nombre || id || '—';
}

/** Nombre de la máquina. */
export function nombreMaquina(id) {
  return estado.datos.produccion.maquinas.find((m) => m.id === id)?.nombre || id || '—';
}
