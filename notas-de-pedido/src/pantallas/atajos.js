// =============================================================
// atajos.js
// Atajos de teclado. Cada pantalla registra los suyos y los quita al salir.
// Si dos pantallas usan la misma combinación (la nota y el asistente abierto
// encima), gana la última que se registró.
// F1 muestra la lista de atajos disponibles en ese momento.
//
// Las combinaciones se escriben así: "Alt+T", "Ctrl+S", "Ctrl+Enter",
// "Alt+ArrowRight", "Escape", "F1". Se leen con la tecla física (e.code),
// así funcionan igual con teclado en español o en inglés.
// =============================================================

import { h } from './util.js';

const capas = []; // cada capa = { nombre, atajos: [{teclas, descripcion, accion}] }

/** Nombre de la combinación apretada, con el mismo formato que en las listas. */
function combinacionDe(evento) {
  let tecla = evento.code || evento.key;
  if (tecla.startsWith('Key')) tecla = tecla.slice(3);          // KeyT → T
  else if (tecla.startsWith('Digit')) tecla = tecla.slice(5);   // Digit1 → 1
  else if (tecla.startsWith('Numpad') && /\d$/.test(tecla)) tecla = tecla.slice(6);
  else if (tecla === 'NumpadEnter') tecla = 'Enter';
  const partes = [];
  if (evento.ctrlKey || evento.metaKey) partes.push('Ctrl');
  if (evento.altKey) partes.push('Alt');
  if (evento.shiftKey) partes.push('Shift');
  partes.push(tecla);
  return partes.join('+');
}

document.addEventListener('keydown', (evento) => {
  const combinacion = combinacionDe(evento);
  if (combinacion === 'F1') {
    evento.preventDefault();
    mostrarAyudaAtajos();
    return;
  }
  // Se busca desde la capa más nueva (la de arriba) hacia la más vieja.
  for (let i = capas.length - 1; i >= 0; i--) {
    const atajo = capas[i].atajos.find((a) => a.teclas === combinacion);
    if (atajo) {
      evento.preventDefault();
      atajo.accion(evento);
      return;
    }
  }
});

/**
 * Registra una lista de atajos.
 * @param {string} nombre  para la ayuda (ej. "Nota de pedido")
 * @param {Array<{teclas: string, descripcion: string, accion: Function}>} atajos
 * @returns {() => void} función para quitarlos
 */
export function registrarAtajos(nombre, atajos) {
  const capa = { nombre, atajos };
  capas.push(capa);
  return () => {
    const posicion = capas.indexOf(capa);
    if (posicion >= 0) capas.splice(posicion, 1);
  };
}

/** Texto de la combinación para mostrar en pantalla (las flechas se escriben en palabras). */
export function textoTeclas(teclas) {
  return teclas
    .replace('ArrowRight', 'flecha derecha')
    .replace('ArrowLeft', 'flecha izquierda')
    .replace('Escape', 'Esc');
}

/** Etiqueta chiquita con el atajo, para poner adentro de un botón. */
export function etiquetaAtajo(teclas) {
  return h('kbd', { class: 'atajo' }, textoTeclas(teclas));
}

/** Ventana con todos los atajos disponibles en este momento. */
export function mostrarAyudaAtajos() {
  document.getElementById('ayuda-atajos')?.remove();
  const cerrar = () => { ventana.remove(); quitar(); };
  const secciones = [...capas].reverse().map((capa) => h('section', {},
    h('h3', {}, capa.nombre),
    h('table', { class: 'tabla-notas' }, h('tbody', {}, capa.atajos.map((a) =>
      h('tr', {}, h('td', {}, etiquetaAtajo(a.teclas)), h('td', {}, a.descripcion)))))));
  const ventana = h('div', { id: 'ayuda-atajos', class: 'ventana-ayuda', role: 'dialog', 'aria-label': 'Atajos de teclado' },
    h('div', { class: 'ventana-contenido panel' },
      h('div', { class: 'titulo-seccion' }, h('h2', {}, 'Atajos de teclado'),
        h('button', { type: 'button', class: 'boton chico', onclick: cerrar }, 'Cerrar')),
      h('p', { class: 'texto-chico' }, 'F1 abre esta ayuda en cualquier pantalla. Enter pasa al campo siguiente.'),
      secciones.length ? secciones : h('p', {}, 'No hay atajos en esta pantalla.')));
  const quitar = registrarAtajos('Ayuda', [{ teclas: 'Escape', descripcion: 'Cerrar la ayuda', accion: cerrar }]);
  ventana.addEventListener('click', (e) => { if (e.target === ventana) cerrar(); });
  document.body.append(ventana);
}
