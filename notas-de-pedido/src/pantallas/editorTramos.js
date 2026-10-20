// =============================================================
// editorTramos.js
// Tabla de tramos del paso 2 del asistente:
// - una fila por tramo: medida, ángulo, sentido, tipo, corte láser, observación;
// - Enter pasa al campo siguiente; teclado numérico en el celular;
// - botones: agregar, insertar antes, borrar, deshacer, rehacer;
// - atajos: dobladillo o aleta al principio / al final, espejar, dibujar a mano.
// =============================================================

import { h, selector, ayuda, enterPasaAlSiguiente, confirmar } from './util.js';
import { etiquetaAtajo, textoTeclas } from './atajos.js';
import { leerNumero } from '../logica/numeros.js';
import { giroEnTramo, DIRECCIONES } from '../logica/geometria.js';
import {
  copiarPerfil, agregarTramoAlFinal, insertarTramoAntes, borrarTramo,
  agregarDobladillo, agregarAleta, espejarPerfil,
} from '../logica/perfil.js';
import { crearCorteLaser } from '../logica/corteLaser.js';
import { medidaFinal, anguloFinal } from '../logica/pendiente.js';

const NOMBRES_TIPO = [
  { valor: 'normal', texto: 'normal' },
  { valor: 'dobladillo', texto: 'dobladillo' },
  { valor: 'dobladillo_aplastado', texto: 'dobl. aplastado' },
  { valor: 'pestana_engrafe', texto: 'pestaña engrafe' },
];

/** Si el texto es un número válido lo guarda como número; si no, deja el texto (la validación lo marca). */
function valorNumerico(texto) {
  const numero = leerNumero(texto);
  return Number.isFinite(numero) ? numero : texto;
}

/**
 * @param {{
 *   perfil: object, datos: object,
 *   alCambiar: (perfil) => void,        // cada vez que cambia algo
 *   alResaltar: (indice|null) => void,  // al pasar por una fila
 *   alDibujarAMano: () => void,
 *   conPendiente?: boolean,             // muestra las columnas de la punta final
 * }} opciones
 */
export function crearEditorTramos(opciones) {
  const { datos } = opciones;
  const config = datos.config;
  let perfil = copiarPerfil(opciones.perfil);
  let conPendiente = Boolean(opciones.conPendiente);
  let seleccionado = perfil.tramos.length ? 0 : null;
  let problemas = [];

  // Historial para deshacer / rehacer (cada entrada es una copia del perfil).
  const historial = [copiarPerfil(perfil)];
  let posicionHistorial = 0;

  const raiz = h('div', { class: 'editor-tramos' });
  const cuerpoTabla = h('tbody');
  const botonDeshacer = h('button', { type: 'button', class: 'boton chico', onclick: () => deshacer(), title: 'Deshacer (Ctrl+Z)' }, 'Deshacer');
  const botonRehacer = h('button', { type: 'button', class: 'boton chico', onclick: () => rehacer(), title: 'Rehacer (Ctrl+Y)' }, 'Rehacer');

  // ---------- cambios ----------

  /** Cambio que modifica la cantidad o el tipo de tramos: se redibuja la tabla. */
  function cambioEstructural(nuevoPerfil, nuevoSeleccionado = seleccionado) {
    perfil = nuevoPerfil;
    seleccionado = nuevoSeleccionado;
    guardarEnHistorial();
    dibujarTabla();
    opciones.alCambiar(copiarPerfil(perfil));
  }

  /** Cambio de un valor (medida, ángulo, texto): NO se redibuja la tabla para no perder el foco. */
  let temporizadorHistorial = null;
  function cambioDeValor() {
    opciones.alCambiar(copiarPerfil(perfil));
    // Se guarda en el historial cuando se deja de escribir un momento (así "Deshacer" se habilita enseguida).
    clearTimeout(temporizadorHistorial);
    temporizadorHistorial = setTimeout(guardarEnHistorial, 500);
    botonDeshacer.disabled = false;
  }

  function guardarEnHistorial() {
    clearTimeout(temporizadorHistorial);
    // Si no cambió nada desde la última vez, no se guarda otra copia igual.
    if (JSON.stringify(perfil) === JSON.stringify(historial[posicionHistorial])) return;
    historial.splice(posicionHistorial + 1);
    historial.push(copiarPerfil(perfil));
    if (historial.length > 100) historial.shift();
    posicionHistorial = historial.length - 1;
    actualizarBotonesHistorial();
  }

  function deshacer() {
    guardarEnHistorial(); // por si quedó algo escrito sin guardar en el historial
    if (posicionHistorial === 0) return;
    posicionHistorial--;
    perfil = copiarPerfil(historial[posicionHistorial]);
    seleccionado = Math.min(seleccionado ?? 0, perfil.tramos.length - 1);
    dibujarTabla();
    actualizarBotonesHistorial();
    opciones.alCambiar(copiarPerfil(perfil));
  }

  function rehacer() {
    if (posicionHistorial >= historial.length - 1) return;
    posicionHistorial++;
    perfil = copiarPerfil(historial[posicionHistorial]);
    dibujarTabla();
    actualizarBotonesHistorial();
    opciones.alCambiar(copiarPerfil(perfil));
  }

  function actualizarBotonesHistorial() {
    botonDeshacer.disabled = posicionHistorial === 0;
    botonRehacer.disabled = posicionHistorial >= historial.length - 1;
  }

  // ---------- tabla ----------

  function dibujarTabla() {
    cuerpoTabla.replaceChildren();
    perfil.tramos.forEach((tramo, indice) => {
      cuerpoTabla.append(filaDeTramo(tramo, indice));
      if (tramo.corteLaser) cuerpoTabla.append(filaDeCorteLaser(tramo, indice));
    });
    if (perfil.tramos.length === 0) {
      cuerpoTabla.append(h('tr', {}, h('td', { colspan: 9, class: 'vacio' }, 'Sin tramos: tocá "Agregar tramo" o "Dibujar a mano".')));
    }
    tabla.classList.toggle('con-pendiente', conPendiente);
    selectorDireccion.value = typeof perfil.direccionInicial === 'string' && perfil.direccionInicial in DIRECCIONES
      ? perfil.direccionInicial : 'grados';
    campoGrados.hidden = selectorDireccion.value !== 'grados';
    if (selectorDireccion.value === 'grados') campoGrados.value = String(perfil.direccionInicial).replace('.', ',');
    marcarProblemas();
  }

  function filaDeTramo(tramo, indice) {
    const giro = giroEnTramo(perfil.tramos, indice, config);
    const anguloFijo = indice === 0 || giro.esVuelta;

    const campoMedida = h('input', {
      type: 'text', inputmode: 'decimal', class: 'campo-medida', 'aria-label': `Medida del tramo ${indice + 1} en cm`,
      value: String(tramo.medidaCm ?? '').replace('.', ','),
      oninput: (e) => { tramo.medidaCm = valorNumerico(e.target.value); cambioDeValor(); },
      onchange: () => guardarEnHistorial(),
    });
    const campoAngulo = h('input', {
      type: 'text', inputmode: 'decimal', class: 'campo-angulo', 'aria-label': `Ángulo del tramo ${indice + 1}`,
      value: anguloFijo ? (indice === 0 ? '—' : '180') : String(tramo.anguloPliegue ?? '').replace('.', ','),
      disabled: anguloFijo,
      title: indice === 0 ? 'El primer tramo no tiene ángulo: usá "Arranca hacia"' : (giro.esVuelta ? 'Dobladillo: siempre 180°' : 'Ángulo interior (90 = escuadra)'),
      oninput: (e) => { tramo.anguloPliegue = valorNumerico(e.target.value); cambioDeValor(); },
      onchange: () => guardarEnHistorial(),
    });
    // Punta final (solo con pendiente): si el tramo no tiene valor final, se ve el del inicio.
    const campoMedidaFinal = h('input', {
      type: 'text', inputmode: 'decimal', class: 'campo-medida', 'aria-label': `Medida del tramo ${indice + 1} en la punta final, en cm`,
      value: String(medidaFinal(tramo) ?? '').replace('.', ','),
      oninput: (e) => { tramo.medidaFinalCm = valorNumerico(e.target.value); cambioDeValor(); },
      onchange: () => guardarEnHistorial(),
    });
    const campoAnguloFinal = h('input', {
      type: 'text', inputmode: 'decimal', class: 'campo-angulo', 'aria-label': `Ángulo del tramo ${indice + 1} en la punta final`,
      value: anguloFijo ? (indice === 0 ? '—' : '180') : String(anguloFinal(tramo) ?? '').replace('.', ','),
      disabled: anguloFijo,
      oninput: (e) => { tramo.anguloPliegueFinal = valorNumerico(e.target.value); cambioDeValor(); },
      onchange: () => guardarEnHistorial(),
    });
    const campoSentido = selector(
      [{ valor: 'izquierda', texto: 'izquierda' }, { valor: 'derecha', texto: 'derecha' }],
      tramo.sentido,
      {
        'aria-label': `Sentido del tramo ${indice + 1}`, disabled: indice === 0,
        onchange: (e) => { tramo.sentido = e.target.value; guardarEnHistorial(); cambioDeValor(); },
      },
    );
    const campoTipo = selector(NOMBRES_TIPO, tramo.tipo, {
      'aria-label': `Tipo del tramo ${indice + 1}`,
      onchange: (e) => { tramo.tipo = e.target.value; cambioEstructural(perfil, indice); },
    });
    const campoLaser = selector(
      [{ valor: '', texto: 'no' }, { valor: 'sinusoidal', texto: 'sinusoidal' }, { valor: 'trapezoidal', texto: 'trapezoidal' }],
      tramo.corteLaser?.tipo || '',
      {
        'aria-label': `Corte láser del tramo ${indice + 1}`,
        onchange: (e) => {
          tramo.corteLaser = e.target.value ? crearCorteLaser(e.target.value, config) : null;
          cambioEstructural(perfil, indice);
        },
      },
    );
    const campoObservacion = h('input', {
      type: 'text', class: 'campo-observacion', maxlength: 60, 'aria-label': `Observación del tramo ${indice + 1}`,
      value: tramo.observacion || '',
      oninput: (e) => { tramo.observacion = e.target.value; cambioDeValor(); },
      onchange: () => guardarEnHistorial(),
    });

    const fila = h('tr', {
      class: `fila-tramo${indice === seleccionado ? ' seleccionado' : ''}`,
      'data-tramo': indice,
      onmouseenter: () => opciones.alResaltar(indice),
      onmouseleave: () => opciones.alResaltar(seleccionado),
      onfocusin: () => seleccionar(indice),
      onclick: () => seleccionar(indice),
    },
    h('td', { class: 'numero-tramo' }, String(indice + 1)),
    h('td', {}, campoMedida),
    h('td', {}, campoAngulo),
    h('td', { class: 'col-final' }, campoMedidaFinal),
    h('td', { class: 'col-final' }, campoAnguloFinal),
    h('td', {}, campoSentido),
    h('td', {}, campoTipo),
    h('td', {}, campoLaser),
    h('td', {}, campoObservacion));
    return fila;
  }

  function filaDeCorteLaser(tramo, indice) {
    const corte = tramo.corteLaser;
    return h('tr', { class: 'fila-laser', 'data-tramo': indice },
      h('td', {}, ''),
      h('td', { colspan: 8 },
        h('div', { class: 'detalle-laser' },
          h('span', {}, `Corte láser (tercerizado) del tramo ${indice + 1}:`),
          h('label', {}, 'Altura de onda (cm) ',
            h('input', {
              type: 'text', inputmode: 'decimal', class: 'campo-angulo', value: String(corte.alturaOndaCm).replace('.', ','),
              oninput: (e) => { corte.alturaOndaCm = valorNumerico(e.target.value); cambioDeValor(); },
              onchange: () => guardarEnHistorial(),
            }), ayuda(datos.glosario, 'altura_onda')),
          h('label', {}, 'Separación entre valles (cm) ',
            h('input', {
              type: 'text', inputmode: 'decimal', class: 'campo-angulo', value: String(corte.separacionVallesCm).replace('.', ','),
              oninput: (e) => { corte.separacionVallesCm = valorNumerico(e.target.value); cambioDeValor(); },
              onchange: () => guardarEnHistorial(),
            }), ayuda(datos.glosario, 'separacion_valles')),
          h('span', { class: 'texto-chico' }, `Mínimos: cara ${String(config.corteLaser.anchoMinimoCaraCm).replace('.', ',')} cm, onda ${String(config.corteLaser.alturaMinimaOndaCm).replace('.', ',')} cm`))));
  }

  function seleccionar(indice) {
    if (seleccionado === indice) return;
    seleccionado = indice;
    cuerpoTabla.querySelectorAll('.fila-tramo').forEach((fila) => {
      fila.classList.toggle('seleccionado', Number(fila.dataset.tramo) === indice);
    });
    opciones.alResaltar(indice);
  }

  /** Pinta las filas con error (rojo) o aviso (amarillo) y pone el mensaje al pasar el mouse. */
  function marcarProblemas() {
    cuerpoTabla.querySelectorAll('.fila-tramo').forEach((fila) => {
      const indice = Number(fila.dataset.tramo);
      const propios = problemas.filter((p) => p.indice === indice);
      fila.classList.toggle('con-error', propios.some((p) => p.nivel === 'error'));
      fila.classList.toggle('con-aviso', !propios.some((p) => p.nivel === 'error') && propios.some((p) => p.nivel === 'aviso'));
      fila.title = propios.map((p) => p.mensaje).join('\n');
    });
  }

  // ---------- dirección inicial ----------

  const campoGrados = h('input', {
    type: 'text', inputmode: 'decimal', class: 'campo-angulo', 'aria-label': 'Dirección inicial en grados', hidden: true,
    oninput: (e) => { const g = leerNumero(e.target.value); if (Number.isFinite(g)) { perfil.direccionInicial = g; cambioDeValor(); } },
    onchange: () => guardarEnHistorial(),
  });
  const selectorDireccion = selector(
    [
      { valor: 'arriba', texto: 'arriba' }, { valor: 'abajo', texto: 'abajo' },
      { valor: 'izquierda', texto: 'izquierda' }, { valor: 'derecha', texto: 'derecha' },
      { valor: 'grados', texto: 'ángulo en grados…' },
    ],
    'arriba',
    {
      'aria-label': 'Hacia dónde arranca el tramo 1',
      onchange: (e) => {
        if (e.target.value === 'grados') {
          campoGrados.hidden = false;
          perfil.direccionInicial = leerNumero(campoGrados.value) || 45;
          campoGrados.value = String(perfil.direccionInicial);
        } else {
          campoGrados.hidden = true;
          perfil.direccionInicial = e.target.value;
        }
        guardarEnHistorial();
        cambioDeValor();
      },
    },
  );

  // ---------- acciones (las usan los botones y los atajos de teclado) ----------

  const acciones = {
    agregarTramo: () => cambioEstructural(agregarTramoAlFinal(perfil, { anguloPliegue: config.anguloPorDefecto }), perfil.tramos.length),
    insertarAntes: () => {
      const indice = seleccionado ?? 0;
      cambioEstructural(insertarTramoAntes(perfil, indice, { anguloPliegue: config.anguloPorDefecto }), indice);
    },
    borrarTramo: () => {
      if (seleccionado === null || !perfil.tramos.length) return;
      if (!confirmar(`¿Borrar el tramo ${seleccionado + 1}?`)) return;
      cambioEstructural(borrarTramo(perfil, seleccionado, config), Math.max(0, seleccionado - 1));
    },
    deshacer: () => deshacer(),
    rehacer: () => rehacer(),
    aletaInicio: () => cambioEstructural(agregarAleta(perfil, 'inicio', 3, 90, 'izquierda'), 0),
    aletaFinal: () => cambioEstructural(agregarAleta(perfil, 'fin', 3, 90, 'izquierda'), perfil.tramos.length),
    dobladilloInicio: () => cambioEstructural(agregarDobladillo(perfil, 'inicio', true, 1, 'izquierda'), 0),
    dobladilloFinal: () => cambioEstructural(agregarDobladillo(perfil, 'fin', true, 1, 'izquierda'), perfil.tramos.length),
    espejar: () => cambioEstructural(espejarPerfil(perfil)),
    dibujarAMano: () => opciones.alDibujarAMano(),
  };

  /** Lista de atajos del editor (el asistente los registra mientras está en el paso 2). */
  const listaAtajos = [
    { teclas: 'Alt+T', descripcion: 'Agregar tramo', accion: acciones.agregarTramo },
    { teclas: 'Alt+I', descripcion: 'Insertar tramo antes del elegido', accion: acciones.insertarAntes },
    { teclas: 'Alt+B', descripcion: 'Borrar el tramo elegido', accion: acciones.borrarTramo },
    { teclas: 'Ctrl+Z', descripcion: 'Deshacer', accion: acciones.deshacer },
    { teclas: 'Ctrl+Y', descripcion: 'Rehacer', accion: acciones.rehacer },
    { teclas: 'Alt+1', descripcion: 'Agregar aleta al inicio', accion: acciones.aletaInicio },
    { teclas: 'Alt+2', descripcion: 'Agregar aleta al final', accion: acciones.aletaFinal },
    { teclas: 'Alt+3', descripcion: 'Agregar dobladillo al inicio', accion: acciones.dobladilloInicio },
    { teclas: 'Alt+4', descripcion: 'Agregar dobladillo al final', accion: acciones.dobladilloFinal },
    { teclas: 'Alt+J', descripcion: 'Espejar la pieza', accion: acciones.espejar },
    { teclas: 'Alt+M', descripcion: 'Dibujar a mano', accion: acciones.dibujarAMano },
  ];
  const teclasDe = (descripcion) => listaAtajos.find((a) => a.descripcion === descripcion).teclas;
  const boton = (texto, descripcion, accion, clase = 'boton') => h('button', {
    type: 'button', class: clase, onclick: accion, title: `${descripcion} (${textoTeclas(teclasDe(descripcion))})`,
  }, texto, etiquetaAtajo(teclasDe(descripcion)));

  // ---------- armado ----------

  botonDeshacer.replaceChildren('Deshacer', etiquetaAtajo('Ctrl+Z'));
  botonRehacer.replaceChildren('Rehacer', etiquetaAtajo('Ctrl+Y'));
  const barra = h('div', { class: 'barra-botones' },
    boton('Agregar tramo', 'Agregar tramo', acciones.agregarTramo),
    boton('Insertar antes', 'Insertar tramo antes del elegido', acciones.insertarAntes),
    boton('Borrar tramo', 'Borrar el tramo elegido', acciones.borrarTramo, 'boton peligro'),
    botonDeshacer,
    botonRehacer);

  const atajos = h('div', { class: 'barra-botones atajos' },
    h('span', { class: 'texto-chico' }, 'Agregar rápido:'),
    boton('Aleta al inicio', 'Agregar aleta al inicio', acciones.aletaInicio, 'boton chico'),
    boton('Aleta al final', 'Agregar aleta al final', acciones.aletaFinal, 'boton chico'),
    boton('Dobladillo al inicio', 'Agregar dobladillo al inicio', acciones.dobladilloInicio, 'boton chico'),
    boton('Dobladillo al final', 'Agregar dobladillo al final', acciones.dobladilloFinal, 'boton chico'),
    boton('Espejar', 'Espejar la pieza', acciones.espejar, 'boton chico'),
    boton('Dibujar a mano', 'Dibujar a mano', acciones.dibujarAMano, 'boton chico'));

  const tabla = h('table', { class: 'tabla-tramos' },
    h('thead', {}, h('tr', {},
      h('th', {}, 'N°'),
      h('th', {}, h('span', { class: 'titulo-con-pendiente' }, 'Inicio: '), 'Medida (cm) ', ayuda(datos.glosario, 'medida_exterior')),
      h('th', {}, 'Ángulo ', ayuda(datos.glosario, 'angulo_interior')),
      h('th', { class: 'col-final' }, 'Final: medida (cm)'),
      h('th', { class: 'col-final' }, 'Final: ángulo'),
      h('th', {}, 'Sentido ', ayuda(datos.glosario, 'sentido')),
      h('th', {}, 'Tipo ', ayuda(datos.glosario, 'dobladillo')),
      h('th', {}, 'Láser ', ayuda(datos.glosario, 'corte_laser')),
      h('th', {}, 'Observación'))),
    cuerpoTabla);

  raiz.append(
    h('div', { class: 'fila-direccion' }, h('label', {}, 'El tramo 1 arranca hacia ', selectorDireccion, campoGrados)),
    h('div', { class: 'tabla-desplazable' }, tabla),
    barra,
    atajos);
  enterPasaAlSiguiente(raiz);

  dibujarTabla();
  actualizarBotonesHistorial();

  return {
    elemento: raiz,
    listaAtajos,
    /** Problemas por tramo (de validarTramos) para pintar las filas. */
    mostrarProblemas(nuevos) {
      problemas = nuevos || [];
      marcarProblemas();
    },
    /** Resalta una fila (cuando se toca el tramo en el 2D o el 3D). */
    resaltarFila(indice) {
      seleccionar(indice);
      const fila = cuerpoTabla.querySelector(`.fila-tramo[data-tramo="${indice}"]`);
      fila?.scrollIntoView({ block: 'nearest' });
    },
    /** Reemplaza todo el perfil (por ejemplo, después de dibujar a mano). */
    reemplazarPerfil(nuevo) {
      cambioEstructural(copiarPerfil(nuevo), 0);
    },
    /**
     * Cambia el perfil desde afuera (lo usa el editor 3D) y lo guarda en el historial,
     * así Deshacer también deshace lo que se hizo en el 3D.
     * @param {(perfil) => object} cambio  recibe una copia y devuelve el perfil nuevo
     */
    modificarPerfil(cambio, nuevoSeleccionado = seleccionado) {
      const nuevo = cambio(copiarPerfil(perfil));
      const elegido = nuevo.tramos.length ? Math.min(Math.max(nuevoSeleccionado ?? 0, 0), nuevo.tramos.length - 1) : null;
      cambioEstructural(nuevo, elegido);
      opciones.alResaltar(elegido);
    },
    perfilActual: () => copiarPerfil(perfil),
    /** Muestra u oculta las columnas de la punta final (plegado con pendiente). */
    establecerPendiente(activada) {
      conPendiente = activada;
      dibujarTabla();
    },
    acciones,
    obtenerSeleccionado: () => seleccionado,
  };
}

