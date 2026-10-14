// =============================================================
// dibujoAMano.js
// Dibujar el perfil tocando puntos sobre una cuadrícula.
// "Imán": los puntos se acomodan a 1 cm y a ángulos de 15°.
// Al terminar, los puntos se convierten en tramos (medida y ángulo) que
// aparecen en la tabla para corregirlos.
// =============================================================

import { h } from '../pantallas/util.js';
import { imantarPunto, puntosATramos } from '../logica/geometria.js';
import { formatearCorto } from '../logica/numeros.js';

const ANCHO_CM = 60;   // tamaño de la hoja de dibujo
const ALTO_CM = 40;
const PX_POR_CM = 12;

/**
 * @param {{config: object, alTerminar: (perfil) => void, alCancelar: () => void}} opciones
 * @returns {HTMLElement}
 */
export function crearDibujoAMano(opciones) {
  const { config } = opciones;
  const puntos = [];
  let previa = null; // punto "fantasma" donde está el mouse

  const ancho = ANCHO_CM * PX_POR_CM;
  const alto = ALTO_CM * PX_POR_CM;
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', `0 0 ${ancho} ${alto}`);
  svg.setAttribute('class', 'dibujo-a-mano');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', 'Hoja cuadriculada para dibujar el perfil');

  const info = h('div', { class: 'texto-chico', 'aria-live': 'polite' }, 'Tocá para poner el primer punto. Cada cuadradito = 1 cm.');

  // Pasar de la posición del mouse (px) a cm (con la Y hacia arriba).
  function aCm(evento) {
    const rect = svg.getBoundingClientRect();
    const x = ((evento.clientX - rect.left) / rect.width) * ANCHO_CM;
    const y = ALTO_CM - ((evento.clientY - rect.top) / rect.height) * ALTO_CM;
    return { x, y };
  }
  const aPx = (p) => ({ x: p.x * PX_POR_CM, y: (ALTO_CM - p.y) * PX_POR_CM });

  function dibujar() {
    const partes = [];
    // Cuadrícula: línea fina cada 1 cm, más marcada cada 5 cm.
    for (let x = 0; x <= ANCHO_CM; x++) {
      partes.push(`<line class="${x % 5 === 0 ? 'grilla-fuerte' : 'grilla'}" x1="${x * PX_POR_CM}" y1="0" x2="${x * PX_POR_CM}" y2="${alto}"/>`);
    }
    for (let y = 0; y <= ALTO_CM; y++) {
      partes.push(`<line class="${y % 5 === 0 ? 'grilla-fuerte' : 'grilla'}" x1="0" y1="${y * PX_POR_CM}" x2="${ancho}" y2="${y * PX_POR_CM}"/>`);
    }
    if (puntos.length) {
      const enPx = puntos.map(aPx);
      partes.push(`<polyline class="perfil-linea" fill="none" points="${enPx.map((p) => `${p.x},${p.y}`).join(' ')}"/>`);
      enPx.forEach((p, i) => partes.push(`<circle class="${i === 0 ? 'perfil-inicio' : 'punto-dibujo'}" cx="${p.x}" cy="${p.y}" r="5"/>`));
      if (previa) {
        const a = aPx(puntos[puntos.length - 1]);
        const b = aPx(previa);
        partes.push(`<line class="linea-previa" x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}"/>`);
      }
    }
    svg.innerHTML = partes.join('');
  }

  svg.addEventListener('pointermove', (evento) => {
    if (!puntos.length) return;
    const anterior = puntos[puntos.length - 1];
    previa = imantarPunto(aCm(evento), anterior, config);
    const largo = Math.hypot(previa.x - anterior.x, previa.y - anterior.y);
    const angulo = Math.round((Math.atan2(previa.y - anterior.y, previa.x - anterior.x) * 180) / Math.PI);
    info.textContent = `Próximo tramo: ${formatearCorto(largo, 1)} cm a ${angulo}°`;
    dibujar();
  });
  svg.addEventListener('pointerleave', () => { previa = null; dibujar(); });
  svg.addEventListener('click', (evento) => {
    const anterior = puntos[puntos.length - 1] || null;
    const punto = imantarPunto(aCm(evento), anterior, config);
    if (anterior && Math.hypot(punto.x - anterior.x, punto.y - anterior.y) < 0.5) return; // mismo punto
    puntos.push(punto);
    info.textContent = `${puntos.length} punto(s). Seguí tocando o tocá "Usar este dibujo".`;
    dibujar();
  });

  dibujar();

  return h('div', { class: 'panel-dibujo-a-mano' },
    h('p', {}, h('strong', {}, 'Dibujo a mano: '), 'tocá los puntos del perfil en orden. Después corregí las medidas en la tabla.'),
    svg,
    info,
    h('div', { class: 'barra-botones' },
      h('button', { type: 'button', class: 'boton', onclick: () => { puntos.pop(); dibujar(); } }, '↶ Borrar último punto'),
      h('button', { type: 'button', class: 'boton', onclick: () => { puntos.length = 0; dibujar(); } }, 'Empezar de nuevo'),
      h('button', { type: 'button', class: 'boton', onclick: () => opciones.alCancelar() }, 'Cancelar'),
      h('button', {
        type: 'button', class: 'boton principal',
        onclick: () => {
          if (puntos.length < 2) { info.textContent = 'Necesitás al menos 2 puntos.'; return; }
          opciones.alTerminar(puntosATramos(puntos));
        },
      }, '✓ Usar este dibujo')));
}
