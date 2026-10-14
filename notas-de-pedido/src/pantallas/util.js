// =============================================================
// util.js
// Herramientas chicas que usan todas las pantallas.
// =============================================================

/**
 * Crea un elemento HTML de forma corta.
 *   h('button', { class: 'boton', onclick: () => … }, 'Guardar')
 * - Los atributos que empiezan con "on" se toman como eventos (onclick, oninput…).
 * - "class", "id", "value", "type", etc. se copian tal cual.
 * - Los hijos pueden ser texto, elementos, listas o null (se ignora).
 */
export function h(etiqueta, atributos = {}, ...hijos) {
  const elemento = document.createElement(etiqueta);
  for (const [nombre, valor] of Object.entries(atributos || {})) {
    if (valor === null || valor === undefined || valor === false) continue;
    if (nombre.startsWith('on') && typeof valor === 'function') {
      elemento.addEventListener(nombre.slice(2), valor);
    } else if (nombre === 'value') {
      elemento.value = valor;
    } else if (nombre === 'checked' || nombre === 'selected' || nombre === 'disabled') {
      elemento[nombre] = Boolean(valor);
    } else if (nombre === 'html') {
      elemento.innerHTML = valor; // solo para SVG generado por el programa
    } else {
      elemento.setAttribute(nombre, valor === true ? '' : String(valor));
    }
  }
  agregarHijos(elemento, hijos);
  return elemento;
}

function agregarHijos(elemento, hijos) {
  for (const hijo of hijos.flat(Infinity)) {
    if (hijo === null || hijo === undefined || hijo === false) continue;
    elemento.append(hijo instanceof Node ? hijo : document.createTextNode(String(hijo)));
  }
}

/** Arma un <select> con opciones [{valor, texto}]. */
export function selector(opciones, valorActual, atributos = {}) {
  return h('select', atributos, opciones.map((o) =>
    h('option', { value: o.valor, selected: String(o.valor) === String(valorActual) }, o.texto)));
}

/** Mensaje flotante que se va solo ("toast"). */
export function mostrarAviso(mensaje, tipo = 'info', segundos = 4) {
  let caja = document.getElementById('avisos-flotantes');
  if (!caja) {
    caja = h('div', { id: 'avisos-flotantes', 'aria-live': 'polite' });
    document.body.append(caja);
  }
  const aviso = h('div', { class: `aviso-flotante aviso-${tipo}`, role: 'status' }, mensaje);
  caja.append(aviso);
  setTimeout(() => aviso.remove(), segundos * 1000);
}

/** Pregunta Sí/No. (window.confirm es simple y funciona en celular.) */
export function confirmar(mensaje) {
  return window.confirm(mensaje);
}

/**
 * Botón "?" con la explicación de un término del glosario.
 * Al pasar el mouse muestra el texto; al tocarlo (celular) lo muestra como aviso.
 */
export function ayuda(glosario, idTermino) {
  const termino = (glosario || []).find((t) => t.id === idTermino);
  if (!termino) return null;
  return h('button', {
    type: 'button',
    class: 'boton-ayuda',
    title: `${termino.termino}: ${termino.explicacion}`,
    'aria-label': `Qué es ${termino.termino}`,
    onclick: (evento) => {
      evento.preventDefault();
      mostrarAviso(`${termino.termino}: ${termino.explicacion}`, 'info', 7);
    },
  }, '?');
}

/** 'aaaa-mm-ddThh:mm…' → 'dd/mm/aaaa'. */
export function fechaCorta(iso) {
  if (!iso) return '';
  const fecha = new Date(iso);
  return `${String(fecha.getDate()).padStart(2, '0')}/${String(fecha.getMonth() + 1).padStart(2, '0')}/${fecha.getFullYear()}`;
}

/** 'aaaa-mm-ddThh:mm…' → 'dd/mm/aaaa hh:mm'. */
export function fechaYHora(iso) {
  if (!iso) return '';
  const fecha = new Date(iso);
  return `${fechaCorta(iso)} ${String(fecha.getHours()).padStart(2, '0')}:${String(fecha.getMinutes()).padStart(2, '0')}`;
}

/** Fecha de hoy en formato 'aaaa-mm-dd' (para los filtros). */
export function hoyIso() {
  const hoy = new Date();
  return `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, '0')}-${String(hoy.getDate()).padStart(2, '0')}`;
}

/** Hace que Enter pase al siguiente campo dentro de un contenedor (como Tab). */
export function enterPasaAlSiguiente(contenedor) {
  contenedor.addEventListener('keydown', (evento) => {
    if (evento.key !== 'Enter' || evento.target.tagName === 'TEXTAREA' || evento.target.tagName === 'BUTTON') return;
    const campos = [...contenedor.querySelectorAll('input:not([type=hidden]):not([disabled]), select:not([disabled])')];
    const posicion = campos.indexOf(evento.target);
    if (posicion >= 0) {
      evento.preventDefault();
      const siguiente = campos[posicion + 1];
      if (siguiente) {
        siguiente.focus();
        if (siguiente.select) siguiente.select();
      } else {
        evento.target.blur();
      }
    }
  });
}

/** Espera `ms` milisegundos sin trabar la pantalla. */
export function esperar(ms) {
  return new Promise((resolver) => setTimeout(resolver, ms));
}
