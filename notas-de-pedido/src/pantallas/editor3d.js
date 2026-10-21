// =============================================================
// editor3d.js
// Editor 3D a pantalla completa (estilo programa de CAD, simplificado):
// - el 3D grande con TODAS las cotas; tocar una cota la deja escribir;
// - tocar una cara elige ese tramo (o la tapa / la boqueta) y a la derecha
//   (abajo en el celular) aparecen sus datos para cambiarlos;
// - botones "+" en las puntas libres para agregar un tramo;
// - barra de herramientas: vistas, cotas, agregar y quitar partes,
//   deshacer y rehacer;
// - abajo, siempre a la vista: desarrollo, banda y código.
//
// No guarda nada por su cuenta: todos los cambios pasan por el asistente
// (y por la tabla de tramos, así "Deshacer" funciona igual que en la tabla).
// =============================================================

import { h, selector, mostrarAviso, confirmar, enterPasaAlSiguiente } from './util.js';
import { registrarAtajos, etiquetaAtajo } from './atajos.js';
import { leerNumero, formatearNumero, formatearCorto } from '../logica/numeros.js';
import { giroEnTramo } from '../logica/geometria.js';
import { leerValorDeCota } from '../logica/cotas.js';
import { cambiarTramo, insertarTramoAntes, insertarTramoDespues, borrarTramo } from '../logica/perfil.js';
import { crearCorteLaser } from '../logica/corteLaser.js';
import { camposDeBoqueta, camposDeTapa, camposDeCorte, seccionEmpalme } from './panelesPieza.js';
import { medidaFinal, anguloFinal } from '../logica/pendiente.js';

const TIPOS_DE_TRAMO = [
  { valor: 'normal', texto: 'normal' },
  { valor: 'dobladillo', texto: 'dobladillo' },
  { valor: 'dobladillo_aplastado', texto: 'dobladillo aplastado' },
  { valor: 'pestana_engrafe', texto: 'pestaña de engrafe' },
];

/**
 * @param {{
 *   titulo: string,
 *   contenedor3d: HTMLElement,           // el mismo visor del asistente: se muda al editor y vuelve al cerrar
 *   visor: object,                       // crearVisor3d()
 *   datos: object,
 *   obtenerBorrador: () => object,
 *   obtenerResultado: () => object,      // calcularRenglon() del borrador
 *   tieneHistorial: boolean,             // hay tabla de tramos (deshacer / rehacer)
 *   contexto: object,                    // el de panelesPieza.js (tapas, boquetas, cortes, empalme)
 *   acciones: {
 *     modificarPerfil: (cambio, nuevoSeleccionado) => void,
 *     cambiarBorrador: (cambio: (borrador) => void) => void,
 *     accionPerfil: (nombre) => void,    // agregarTramo, aletaInicio… (las de la tabla de tramos)
 *     agregarBoqueta: () => number|null,
 *     agregarCorte: () => number|null,
 *     alternarPendiente: () => void,     // plegado con pendiente sí / no
 *     formularioParametros: () => HTMLElement|null,
 *     resaltarParte: (seleccion|null) => void,
 *   },
 *   alCerrar: () => void,
 * }} opciones
 */
export function abrirEditor3d(opciones) {
  const { contenedor3d, visor, datos, acciones } = opciones;
  const config = datos.config;
  let seleccion = null; // {tipo:'tramo'|'boqueta'|'corte', indice} | {tipo:'tapa', lado} | null
  let panelPlegado = false;

  const borrador = () => opciones.obtenerBorrador();
  // Los paneles de tapas, boquetas y cortes son los mismos del paso 2; si cambia algo que pide otros campos, se redibuja este panel.
  const contexto = {
    ...opciones.contexto,
    alCambiar: (redibujar) => {
      opciones.contexto.alCambiar(redibujar);
      if (redibujar) dibujarPanel();
    },
  };
  const usaPerfil = () => borrador().tipoPieza === 'plegada' || borrador().usaPerfil;

  // ---------- estructura ----------
  const lugarOriginal = { padre: contenedor3d.parentNode, siguiente: contenedor3d.nextSibling };
  const zonaLienzo = h('div', { class: 'editor-3d-lienzo' });
  const contenidoPropiedades = h('div', { class: 'editor-3d-contenido' });
  const manija = h('button', {
    type: 'button', class: 'editor-3d-manija', 'aria-expanded': 'true',
    onclick: () => plegarPanel(!panelPlegado),
  }, 'Propiedades');
  const panel = h('aside', { class: 'editor-3d-propiedades', 'aria-label': 'Propiedades de la parte elegida' }, manija, contenidoPropiedades);
  const resumen = h('div', { class: 'editor-3d-resumen', 'aria-live': 'polite' });
  const botonCotas = h('button', { type: 'button', class: 'boton chico', 'aria-pressed': String(visor.cotasVisibles()), onclick: () => alternarCotas() }, 'Cotas', etiquetaAtajo('Alt+C'));

  const herramienta = (texto, accion, teclas, clase = 'boton chico') => h('button', { type: 'button', class: clase, onclick: accion }, texto, teclas ? etiquetaAtajo(teclas) : null);
  const grupoVistas = h('div', { class: 'grupo-herramientas', role: 'group', 'aria-label': 'Vistas' },
    herramienta('Inicial', () => visor.vista('inicial'), 'Alt+0'),
    herramienta('Frente', () => visor.vista('frente'), 'Alt+7'),
    herramienta('Lateral', () => visor.vista('lateral'), 'Alt+8'),
    herramienta('Isométrica', () => visor.vista('iso'), 'Alt+9'),
    botonCotas);
  const botonPendiente = h('button', {
    type: 'button', class: 'boton chico', 'aria-pressed': String(Boolean(borrador().conPendiente)),
    title: 'La pieza cambia de perfil de una punta a la otra', onclick: () => acciones.alternarPendiente(),
  }, 'Con pendiente', etiquetaAtajo('Alt+L'));
  botonPendiente.hidden = borrador().tipoPieza !== 'plegada';
  const grupoPerfil = h('div', { class: 'grupo-herramientas', role: 'group', 'aria-label': 'Tramos' },
    botonPendiente,
    herramienta('+ Tramo al final', () => acciones.accionPerfil('agregarTramo'), 'Alt+T'),
    herramienta('Aleta al inicio', () => acciones.accionPerfil('aletaInicio'), 'Alt+1'),
    herramienta('Aleta al final', () => acciones.accionPerfil('aletaFinal'), 'Alt+2'),
    herramienta('Dobladillo al inicio', () => acciones.accionPerfil('dobladilloInicio'), 'Alt+3'),
    herramienta('Dobladillo al final', () => acciones.accionPerfil('dobladilloFinal'), 'Alt+4'),
    herramienta('Espejar', () => acciones.accionPerfil('espejar'), 'Alt+J'),
    borrador().tipoPieza === 'plegada' ? herramienta('+ Corte', () => agregarCorte(), 'Alt+R') : null,
    herramienta('Borrar lo elegido', () => borrarSeleccion(), 'Delete', 'boton chico peligro'),
    opciones.tieneHistorial ? herramienta('Deshacer', () => acciones.accionPerfil('deshacer'), 'Ctrl+Z') : null,
    opciones.tieneHistorial ? herramienta('Rehacer', () => acciones.accionPerfil('rehacer'), 'Ctrl+Y') : null);
  const grupoCanaleta = h('div', { class: 'grupo-herramientas', role: 'group', 'aria-label': 'Canaleta' },
    herramienta('+ Boqueta', () => agregarBoqueta(), 'Alt+Q'));
  grupoPerfil.hidden = !usaPerfil();
  grupoCanaleta.hidden = !borrador().accesorios;

  const botonPantallaCompleta = document.fullscreenEnabled
    ? h('button', { type: 'button', class: 'boton chico', onclick: () => alternarPantallaCompleta() }, 'Pantalla completa')
    : null;

  const raiz = h('div', { class: 'editor-3d', role: 'dialog', 'aria-modal': 'true', 'aria-label': 'Editor 3D' },
    h('header', { class: 'editor-3d-barra' },
      h('div', { class: 'editor-3d-titulo' }, h('strong', {}, 'Editor 3D'), h('span', { class: 'texto-chico' }, opciones.titulo)),
      h('div', { class: 'editor-3d-herramientas' }, grupoVistas, grupoPerfil, grupoCanaleta),
      h('div', { class: 'editor-3d-salida' }, botonPantallaCompleta,
        h('button', { type: 'button', class: 'boton principal', onclick: () => cerrar() }, 'Listo', etiquetaAtajo('Escape')))),
    h('div', { class: 'editor-3d-cuerpo' }, zonaLienzo, panel),
    resumen);

  zonaLienzo.append(contenedor3d,
    h('p', { class: 'ayuda-gestos' },
      h('span', { class: 'gestos-mouse' }, 'Arrastrá para girar · rueda: zoom · botón derecho: mover · tocá una cota para cambiarla'),
      h('span', { class: 'gestos-dedo' }, '1 dedo: girar · 2 dedos: zoom y mover · tocá una cota para cambiarla')));
  document.body.append(raiz);
  visor.modoEdicion(true);

  // Atajos propios (ganan sobre los del asistente mientras el editor está abierto).
  const quitarAtajos = registrarAtajos('Editor 3D', [
    { teclas: 'Escape', descripcion: 'Cerrar el editor 3D', accion: () => cerrar() },
    { teclas: 'Alt+G', descripcion: 'Cerrar el editor 3D', accion: () => cerrar() },
    { teclas: 'Delete', descripcion: 'Borrar el tramo o la boqueta elegida', accion: () => borrarSeleccion(), soloFueraDeCampos: true },
    { teclas: 'Alt+C', descripcion: 'Mostrar u ocultar las cotas', accion: () => alternarCotas() },
    { teclas: 'Alt+ArrowRight', descripcion: 'Elegir el tramo siguiente', accion: () => moverSeleccion(1) },
    { teclas: 'Alt+ArrowLeft', descripcion: 'Elegir el tramo anterior', accion: () => moverSeleccion(-1) },
    { teclas: 'Alt+M', descripcion: 'Dibujar a mano (cerrá el editor 3D primero)', accion: () => mostrarAviso('Para dibujar a mano cerrá el editor 3D (Esc).', 'info') },
  ]);

  // ---------- acciones ----------

  function cerrar() {
    quitarAtajos();
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
    visor.modoEdicion(false);
    acciones.resaltarParte(null);
    // El visor vuelve a su lugar en el asistente.
    if (lugarOriginal.padre?.isConnected) lugarOriginal.padre.insertBefore(contenedor3d, lugarOriginal.siguiente);
    raiz.remove();
    opciones.alCerrar();
  }

  function alternarCotas() {
    visor.mostrarCotas(!visor.cotasVisibles());
    botonCotas.setAttribute('aria-pressed', String(visor.cotasVisibles()));
  }

  function alternarPantallaCompleta() {
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
    else raiz.requestFullscreen?.().catch(() => mostrarAviso('Este navegador no deja usar pantalla completa.', 'info'));
  }

  function plegarPanel(plegar) {
    panelPlegado = plegar;
    panel.classList.toggle('plegado', plegar);
    manija.setAttribute('aria-expanded', String(!plegar));
  }

  function agregarCorte() {
    const indice = acciones.agregarCorte();
    if (indice !== null && indice !== undefined) seleccionar({ tipo: 'corte', indice });
  }

  function agregarBoqueta() {
    const indice = acciones.agregarBoqueta();
    if (indice !== null && indice !== undefined) seleccionar({ tipo: 'boqueta', indice });
  }

  function moverSeleccion(paso) {
    const tramos = borrador().perfil?.tramos || [];
    if (!usaPerfil() || !tramos.length) return;
    const actual = seleccion?.tipo === 'tramo' ? seleccion.indice : (paso > 0 ? -1 : tramos.length);
    const nuevo = Math.min(Math.max(actual + paso, 0), tramos.length - 1);
    seleccionar({ tipo: 'tramo', indice: nuevo });
  }

  function borrarSeleccion() {
    if (!seleccion) {
      mostrarAviso('Primero tocá la parte que querés borrar.', 'info');
      return;
    }
    if (seleccion.tipo === 'tramo') {
      const { indice } = seleccion;
      if (!confirmar(`¿Borrar el tramo ${indice + 1}?`)) return;
      acciones.modificarPerfil((perfil) => borrarTramo(perfil, indice, config), Math.max(0, indice - 1));
      seleccionar(borrador().perfil.tramos.length ? { tipo: 'tramo', indice: Math.max(0, indice - 1) } : null);
    } else if (seleccion.tipo === 'boqueta') {
      const { indice } = seleccion;
      if (!confirmar(`¿Quitar la boqueta ${indice + 1}?`)) return;
      acciones.cambiarBorrador((b) => { b.accesorios.boquetas.splice(indice, 1); });
      seleccionar(null);
    } else if (seleccion.tipo === 'corte') {
      const { indice } = seleccion;
      if (!confirmar(`¿Quitar el corte ${indice + 1}?`)) return;
      acciones.cambiarBorrador((b) => { b.cortes.splice(indice, 1); });
      seleccionar(null);
    } else if (seleccion.tipo === 'tapa') {
      const { lado } = seleccion;
      acciones.cambiarBorrador((b) => { b.accesorios[lado === 'izquierda' ? 'tapaIzquierda' : 'tapaDerecha'] = 'ninguna'; });
      seleccionar(null);
    }
  }

  // ---------- selección y panel de propiedades ----------

  function seleccionar(nueva) {
    seleccion = nueva;
    acciones.resaltarParte(nueva);
    if (nueva) plegarPanel(false);
    dibujarPanel();
  }

  /** Campo numérico que se aplica al confirmar (Enter o al salir del campo). */
  function campoNumero(etiqueta, valor, tipoValor, aplicar, atributos = {}) {
    const entrada = h('input', {
      type: 'text', inputmode: 'decimal', class: 'campo-medida', value: Number.isFinite(leerNumero(valor)) ? String(valor).replace('.', ',') : (valor ?? ''),
      ...atributos,
      onchange: (e) => {
        const lectura = leerValorDeCota(e.target.value, tipoValor, config);
        if (!lectura.ok) {
          mostrarAviso(lectura.mensaje, 'error');
          e.target.value = String(valor ?? '').replace('.', ',');
          return;
        }
        aplicar(lectura.valor);
      },
    });
    return h('label', { class: 'campo-parametro' }, h('span', {}, etiqueta), entrada);
  }

  function dibujarPanel() {
    const b = borrador();
    const partes = [];
    if (seleccion?.tipo === 'tramo' && usaPerfil() && b.perfil.tramos[seleccion.indice]) {
      partes.push(...panelDeTramo(b, seleccion.indice));
    } else if (seleccion?.tipo === 'boqueta' && b.accesorios?.boquetas[seleccion.indice]) {
      partes.push(...panelDeBoqueta(b, seleccion.indice));
    } else if (seleccion?.tipo === 'tapa' && b.accesorios) {
      partes.push(...panelDeTapa(b, seleccion.lado));
    } else if (seleccion?.tipo === 'corte' && b.cortes?.[seleccion.indice]) {
      partes.push(h('h3', {}, `Corte ${seleccion.indice + 1}`), ...camposDeCorte(contexto, seleccion.indice, { conQuitar: false }),
        h('div', { class: 'barra-botones' }, h('button', { type: 'button', class: 'boton chico peligro', onclick: () => borrarSeleccion() }, 'Quitar corte', etiquetaAtajo('Delete'))));
    } else {
      seleccion = null;
      partes.push(...panelGeneral(b));
    }
    contenidoPropiedades.replaceChildren(...partes);
    enterPasaAlSiguiente(contenidoPropiedades);
  }

  function panelGeneral(b) {
    const partes = [h('h3', {}, 'La pieza')];
    if (b.usaLargo) {
      partes.push(campoNumero('Largo de la pieza (m)', formatearNumero(leerNumero(b.largoCm) / 100, 2), 'medida', (metros) => {
        acciones.cambiarBorrador((x) => { x.largoCm = Math.round(metros * 10000) / 100; });
      }));
    }
    if (usaPerfil()) {
      partes.push(h('ul', { class: 'lista-ayuda texto-chico' },
        h('li', {}, 'Tocá una cara de la pieza para elegir ese tramo y cambiar sus datos.'),
        h('li', {}, 'Tocá una cota (el número) para escribir la medida o el ángulo nuevo. Enter confirma, Esc cancela.'),
        h('li', {}, 'Los botones "+" en las puntas agregan un tramo ahí.'),
        b.accesorios ? h('li', {}, 'Tocá una tapa o una boqueta (o su cartel) para cambiarla o quitarla.') : null,
        h('li', {}, '"+ Corte" agrega un agujero en una cara (puede llevar pared alrededor).')));
    }
    const empalme = seccionEmpalme(contexto);
    if (empalme) partes.push(empalme);
    const formulario = acciones.formularioParametros();
    if (formulario) partes.push(formulario);
    return partes;
  }

  function panelDeTramo(b, indice) {
    const tramos = b.perfil.tramos;
    const tramo = tramos[indice];
    const giro = giroEnTramo(tramos, indice, config);
    const anguloFijo = indice === 0 || giro.esVuelta;
    const aplicar = (cambios, estructural = false) => {
      acciones.modificarPerfil((perfil) => cambiarTramo(perfil, indice, cambios), indice);
      if (estructural) dibujarPanel();
    };
    const resultado = opciones.obtenerResultado();
    const problemas = (resultado?.problemasTramos || []).filter((p) => p.indice === indice);

    const partes = [
      h('div', { class: 'titulo-tramo' },
        h('button', { type: 'button', class: 'boton chico', disabled: indice === 0, onclick: () => moverSeleccion(-1), 'aria-label': 'Tramo anterior' }, '<'),
        h('h3', {}, `Tramo ${indice + 1} de ${tramos.length}`),
        h('button', { type: 'button', class: 'boton chico', disabled: indice === tramos.length - 1, onclick: () => moverSeleccion(1), 'aria-label': 'Tramo siguiente' }, '>')),
      campoNumero('Medida (cm)', tramo.medidaCm, 'medida', (v) => aplicar({ medidaCm: v }), { 'data-campo': 'medida' }),
      anguloFijo
        ? h('p', { class: 'texto-chico' }, indice === 0 ? 'El tramo 1 no tiene ángulo: arranca la pieza.' : 'Dobladillo: el pliegue es siempre de 180°.')
        : campoNumero(b.conPendiente ? 'Inicio: ángulo del pliegue (°)' : 'Ángulo del pliegue (°)', tramo.anguloPliegue, 'angulo', (v) => aplicar({ anguloPliegue: v })),
    ];
    if (b.conPendiente) {
      // Plegado con pendiente: el mismo tramo en la punta final (derecha).
      partes[1].querySelector('span').textContent = 'Inicio: medida (cm)';
      partes.push(campoNumero('Final: medida (cm)', medidaFinal(tramo), 'medida', (v) => aplicar({ medidaFinalCm: v })));
      if (!anguloFijo) partes.push(campoNumero('Final: ángulo del pliegue (°)', anguloFinal(tramo), 'angulo', (v) => aplicar({ anguloPliegueFinal: v })));
    }
    if (indice > 0) {
      partes.push(h('div', { class: 'campo-parametro' }, h('span', {}, 'Dobla hacia'),
        h('div', { class: 'botones-sentido', role: 'radiogroup' },
          ['izquierda', 'derecha'].map((sentido) => h('button', {
            type: 'button', role: 'radio', class: `boton chico${tramo.sentido === sentido ? ' elegido' : ''}`, 'aria-checked': String(tramo.sentido === sentido),
            onclick: () => aplicar({ sentido }, true),
          }, sentido)))));
    }
    partes.push(h('label', { class: 'campo-parametro' }, h('span', {}, 'Tipo'),
      selector(TIPOS_DE_TRAMO, tramo.tipo, { onchange: (e) => aplicar({ tipo: e.target.value }, true) })));
    partes.push(h('label', { class: 'campo-parametro' }, h('span', {}, 'Corte láser (tercerizado)'),
      selector([{ valor: '', texto: 'no' }, { valor: 'sinusoidal', texto: 'sinusoidal' }, { valor: 'trapezoidal', texto: 'trapezoidal' }], tramo.corteLaser?.tipo || '', {
        onchange: (e) => aplicar({ corteLaser: e.target.value ? crearCorteLaser(e.target.value, config) : null }, true),
      })));
    if (tramo.corteLaser) {
      partes.push(
        campoNumero('Altura de onda (cm)', tramo.corteLaser.alturaOndaCm, 'medida', (v) => aplicar({ corteLaser: { ...tramo.corteLaser, alturaOndaCm: v } })),
        campoNumero('Separación entre valles (cm)', tramo.corteLaser.separacionVallesCm, 'medida', (v) => aplicar({ corteLaser: { ...tramo.corteLaser, separacionVallesCm: v } })));
    }
    partes.push(h('label', { class: 'campo-parametro' }, h('span', {}, 'Observación'),
      h('input', { type: 'text', maxlength: 60, value: tramo.observacion || '', onchange: (e) => aplicar({ observacion: e.target.value }) })));
    if (problemas.length) {
      partes.push(h('ul', { class: 'lista-mensajes' }, problemas.map((p) => h('li', { class: p.nivel === 'error' ? 'error' : 'aviso' }, p.mensaje))));
    }
    const nuevoTramo = { anguloPliegue: config.anguloPorDefecto };
    partes.push(h('div', { class: 'barra-botones' },
      h('button', {
        type: 'button', class: 'boton chico',
        onclick: () => { acciones.modificarPerfil((p) => insertarTramoAntes(p, indice, nuevoTramo), indice); seleccionar({ tipo: 'tramo', indice }); },
      }, 'Insertar antes'),
      h('button', {
        type: 'button', class: 'boton chico',
        onclick: () => { acciones.modificarPerfil((p) => insertarTramoDespues(p, indice, nuevoTramo), indice + 1); seleccionar({ tipo: 'tramo', indice: indice + 1 }); },
      }, 'Insertar después'),
      h('button', { type: 'button', class: 'boton chico peligro', onclick: () => borrarSeleccion() }, 'Borrar tramo', etiquetaAtajo('Delete'))));
    return partes;
  }

  function panelDeBoqueta(b, indice) {
    return [
      h('h3', {}, `Boqueta ${indice + 1}`),
      ...camposDeBoqueta(contexto, indice, { conQuitar: false }),
      h('div', { class: 'barra-botones' }, h('button', { type: 'button', class: 'boton chico peligro', onclick: () => borrarSeleccion() }, 'Quitar boqueta', etiquetaAtajo('Delete'))),
    ];
  }

  function panelDeTapa(b, lado) {
    return [
      h('h3', {}, `Tapa ${lado}`),
      camposDeTapa(contexto, lado),
      h('p', { class: 'texto-chico' }, 'Soldada: la pestaña va hacia adentro. Engrampada: abraza la canaleta por afuera. A medida: otra forma, que entre en la canaleta.'),
    ];
  }

  // ---------- resumen ----------

  function dibujarResumen() {
    const r = opciones.obtenerResultado();
    if (!r) return;
    const codigo = r.codigo.encontrado ? r.codigo.codigo : (borrador().codigoPendiente ? 'PENDIENTE' : 'no encontrado');
    resumen.replaceChildren(...[
      h('span', {}, 'Desarrollo ', h('strong', {}, r.porUnidad ? 'por unidad' : (r.desarrolloCm > 0 ? `D = ${formatearCorto(r.desarrolloCm, 1)} cm` : '—'))),
      h('span', {}, 'Banda ', h('strong', {}, r.banda.numero ? `${r.banda.nombre} (${r.banda.numero})` : r.banda.nombre)),
      h('span', {}, 'Código ', h('strong', { class: r.codigo.encontrado ? 'codigo-ok' : 'codigo-falta' }, codigo),
        ...r.codigosAdicionales.map((c) => h('span', { class: 'texto-chico codigo-extra' }, ` + ${c.codigo} x${c.cantidad}`))),
      r.errores.length ? h('span', { class: 'resumen-error', title: r.errores.join('\n') }, `${r.errores.length} ${r.errores.length === 1 ? 'error' : 'errores'}: ${r.errores[0]}`) : null,
    ].filter(Boolean)); // replaceChildren escribiría "null" si quedara alguno
  }

  dibujarPanel();
  dibujarResumen();
  // En el celular el panel arranca plegado, así se ve el 3D entero.
  if (window.matchMedia('(max-width: 860px)').matches) plegarPanel(true);

  return {
    seleccionar,
    /** El asistente avisa que cambió el borrador. Si el vendedor está escribiendo en el panel, no se redibuja. */
    refrescar({ forzar = false } = {}) {
      dibujarResumen();
      grupoCanaleta.hidden = !borrador().accesorios;
      botonPendiente.setAttribute('aria-pressed', String(Boolean(borrador().conPendiente)));
      if (forzar || !contenidoPropiedades.contains(document.activeElement)) dibujarPanel();
    },
    /** Pone el foco en la medida del tramo elegido (después de agregar uno con "+"). */
    enfocarMedida() {
      const campo = contenidoPropiedades.querySelector('[data-campo="medida"]');
      campo?.focus();
      campo?.select();
    },
    cerrar,
  };
}
