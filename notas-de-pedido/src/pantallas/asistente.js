// =============================================================
// asistente.js
// Asistente "Agregar pieza" en 3 pasos:
//   1) ¿Qué pieza?        galería de plantillas con buscador
//   2) Medidas y dibujo   tabla de tramos (o parámetros) + 2D acotado + 3D, en vivo
//   3) Material y cantidad
// El panel de resultados (desarrollo, banda y código) está siempre visible.
// =============================================================

import { h, selector, ayuda, mostrarAviso, confirmar, enterPasaAlSiguiente } from './util.js';
import { crearEditorTramos } from './editorTramos.js';
import { svgDelPerfil } from '../vistas2d/perfilSvg.js';
import { svgCorteLaser } from '../vistas2d/corteLaserSvg.js';
import { svgDeEspecial, svgMiniaturaEspecial } from '../vistas2d/especialSvg.js';
import { crearDibujoAMano } from '../vistas2d/dibujoAMano.js';
import { cargar3d } from '../vistas3d/cargar3d.js';
import { calcularRenglon } from '../logica/calculoRenglon.js';
import { leerNumero, formatearNumero, formatearCorto } from '../logica/numeros.js';
import { crearRenglonDesdePlantilla, buscarPlantilla, filtrarPlantillas, agruparPlantillas } from '../logica/renglones.js';
import { copiarPerfil } from '../logica/perfil.js';
import { parametrosVisibles } from '../logica/piezasEspeciales.js';
import { crearBoqueta, FORMAS_BOQUETA } from '../logica/accesoriosCanaleta.js';
import { svgPlantaCanaleta } from '../vistas2d/plantaCanaletaSvg.js';
import { registrarAtajos, etiquetaAtajo } from './atajos.js';
import { abrirEditor3d } from './editor3d.js';
import { leerValorDeCota } from '../logica/cotas.js';
import { cambiarTramo, agregarTramoEnExtremo } from '../logica/perfil.js';
import { tienePendiente, perfilFinal, activarPendiente } from '../logica/pendiente.js';
import { svgPendienteLateral } from '../vistas2d/pendienteSvg.js';

const NOMBRES_PASOS = ['¿Qué pieza?', 'Medidas y dibujo', 'Material y cantidad'];

/**
 * Abre el asistente encima de la pantalla de la nota.
 * @param {{
 *   nota: object,                 // la nota (para copiar el perfil de una canaleta a una tapa suelta)
 *   renglon?: object,             // si viene, se edita ese renglón (arranca en el paso 2)
 *   paso?: number,                // paso donde arrancar (para recuperar una pieza sin terminar)
 *   datos: object,
 *   alGuardar: (renglon) => void,
 *   alCerrar: () => void,
 *   alCambiarBorrador?: (renglon, paso) => void,  // para no perder lo cargado si se corta
 * }} opciones
 */
export function abrirAsistente(opciones) {
  const { nota, datos } = opciones;
  const editando = Boolean(opciones.renglon && nota.renglones.some((r) => r.id === opciones.renglon.id));
  let borrador = opciones.renglon ? JSON.parse(JSON.stringify(opciones.renglon)) : null;
  let paso = borrador ? (opciones.paso || 2) : 1;
  let resultado = null;
  let resaltado = null;
  let editor = null;
  let visor = null;
  let quitarAtajosEditor = null;
  let pestanaCelular = 'medidas';
  let editor3d = null;          // editor 3D a pantalla completa (si está abierto)
  let campoLargo = null;        // campos del paso 2 que el editor 3D puede cambiar
  let formularioActual = null;

  // ---------- estructura fija ----------
  const contenido = h('div', { class: 'asistente-contenido' });
  const barraProgreso = h('ol', { class: 'progreso' });
  const panelResultados = h('div', { class: 'panel-resultados', 'aria-live': 'polite' });
  const botonAtras = h('button', { type: 'button', class: 'boton', onclick: () => irAPaso(paso - 1) }, 'Atrás', etiquetaAtajo('Alt+ArrowLeft'));
  const botonSiguiente = h('button', { type: 'button', class: 'boton principal', onclick: () => siguiente() }, 'Siguiente', etiquetaAtajo('Alt+ArrowRight'));
  const contenedor3d = h('div', { class: 'contenedor-3d' }, h('p', { class: 'texto-chico' }, 'Cargando 3D…'));
  const botonCotas = h('button', { type: 'button', class: 'boton chico', 'aria-pressed': 'true', onclick: () => alternarCotas() }, 'Cotas', etiquetaAtajo('Alt+C'));
  const botonEditor3d = h('button', { type: 'button', class: 'boton chico principal', onclick: () => abrirEdicion3d() }, 'Editar en 3D', etiquetaAtajo('Alt+G'));
  const botones3d = h('div', { class: 'barra-botones vistas-3d' },
    ...[['inicial', 'Vista inicial', 'Alt+0'], ['frente', 'Frente', 'Alt+7'], ['lateral', 'Lateral', 'Alt+8'], ['iso', 'Isométrica', 'Alt+9']].map(([vista, texto, teclas]) =>
      h('button', { type: 'button', class: 'boton chico', onclick: () => visor?.vista(vista) }, texto, etiquetaAtajo(teclas))),
    botonCotas,
    botonEditor3d);

  const raiz = h('div', { class: 'asistente', role: 'dialog', 'aria-modal': 'true', 'aria-label': 'Agregar pieza' },
    h('header', { class: 'asistente-encabezado' },
      h('h2', {}, editando ? 'Editar pieza' : 'Agregar pieza'),
      barraProgreso,
      h('button', { type: 'button', class: 'boton', onclick: () => cerrar() }, 'Cerrar', etiquetaAtajo('Escape'))),
    contenido,
    h('footer', { class: 'asistente-pie' }, panelResultados, h('div', { class: 'barra-botones' }, botonAtras, botonSiguiente)));
  document.body.append(raiz);
  document.body.classList.add('con-asistente');

  // Atajos de teclado del asistente (F1 muestra la lista).
  const quitarAtajos = registrarAtajos('Asistente "Agregar pieza"', [
    { teclas: 'Escape', descripcion: 'Cerrar el asistente', accion: () => cerrar() },
    { teclas: 'Alt+ArrowRight', descripcion: 'Siguiente paso / agregar a la nota', accion: () => siguiente() },
    { teclas: 'Alt+ArrowLeft', descripcion: 'Paso anterior', accion: () => { if (paso > 1) irAPaso(paso - 1); } },
    { teclas: 'Alt+Q', descripcion: 'Agregar boqueta a la canaleta', accion: () => agregarBoqueta() },
    { teclas: 'Alt+0', descripcion: 'Vista 3D inicial', accion: () => visor?.vista('inicial') },
    { teclas: 'Alt+7', descripcion: 'Vista 3D de frente', accion: () => visor?.vista('frente') },
    { teclas: 'Alt+8', descripcion: 'Vista 3D lateral', accion: () => visor?.vista('lateral') },
    { teclas: 'Alt+9', descripcion: 'Vista 3D isométrica', accion: () => visor?.vista('iso') },
    { teclas: 'Alt+C', descripcion: 'Mostrar u ocultar las cotas del 3D', accion: () => alternarCotas() },
    { teclas: 'Alt+G', descripcion: 'Editar en 3D (pantalla completa)', accion: () => abrirEdicion3d() },
    { teclas: 'Alt+L', descripcion: 'Plegado con pendiente (sí / no)', accion: () => alternarPendiente() },
  ]);

  // El 3D se carga una sola vez y se reutiliza en los pasos 2 y 3.
  cargar3d().then((modulo) => {
    if (!modulo) {
      contenedor3d.replaceChildren(h('p', { class: 'aviso-caja' }, 'El 3D no está disponible (¿sin internet?). El dibujo 2D sigue siendo la referencia para fabricar.'));
      return;
    }
    contenedor3d.replaceChildren();
    visor = modulo.crearVisor3d(contenedor3d, {
      alTocarTramo: (indice) => seleccionarParte({ tipo: 'tramo', indice }),
      alTocarAccesorio: (clave) => {
        const [tipo, dato] = clave.split(':');
        seleccionarParte(tipo === 'boqueta' ? { tipo, indice: Number(dato) } : { tipo: 'tapa', lado: dato });
      },
      alTocarVacio: () => { if (editor3d) seleccionarParte(null); },
      alPasarSobreTramo: (indice) => { if (indice !== null && !editor3d) resaltar(indice); },
      alUsarCota: (editar, valor) => usarCota(editar, valor),
    });
    actualizar3d(true);
  });

  // ---------- navegación ----------

  function irAPaso(nuevo) {
    if (nuevo < 1 || nuevo > 3) return;
    if (nuevo === 1 && borrador && !confirmar('Si volvés a elegir la pieza se pierde lo que cargaste. ¿Seguir?')) return;
    if (nuevo === 1) borrador = null;
    paso = nuevo;
    dibujarPaso();
  }

  function siguiente() {
    if (paso === 1) return; // en el paso 1 se avanza tocando una tarjeta
    if (paso === 2) { irAPaso(3); return; }
    // Paso 3: guardar
    resultado = calcularRenglon(borrador, datos);
    if (resultado.errores.length > 0) {
      const lista = resultado.errores.slice(0, 5).map((e) => `• ${e}`).join('\n');
      if (!confirmar(`La pieza tiene problemas:\n${lista}\n\n¿Agregarla igual? No vas a poder emitir la nota hasta corregirlos.`)) return;
    }
    const guardado = JSON.parse(JSON.stringify(borrador));
    terminar();
    opciones.alGuardar(guardado);
  }

  function cerrar() {
    if (borrador && !confirmar('¿Cerrar sin guardar esta pieza?')) return;
    terminar();
    opciones.alCerrar();
  }

  function terminar() {
    editor3d?.cerrar();
    quitarAtajos();
    quitarAtajosEditor?.();
    visor?.destruir();
    raiz.remove();
    document.body.classList.remove('con-asistente');
  }

  // ---------- dibujo de cada paso ----------

  function dibujarPaso() {
    barraProgreso.replaceChildren(...NOMBRES_PASOS.map((nombre, i) =>
      h('li', { class: i + 1 === paso ? 'actual' : (i + 1 < paso ? 'hecho' : '') }, `${i + 1}. ${nombre}`)));
    botonAtras.hidden = paso === 1;
    botonSiguiente.hidden = paso === 1;
    botonSiguiente.replaceChildren(paso === 3 ? (editando ? 'Guardar cambios' : 'Agregar a la nota') : 'Siguiente', etiquetaAtajo('Alt+ArrowRight'));
    contenido.replaceChildren();
    editor = null;
    quitarAtajosEditor?.();
    quitarAtajosEditor = null;
    campoLargo = null;
    formularioActual = null;
    botonEditor3d.hidden = paso !== 2;
    if (paso === 1) dibujarPaso1();
    if (paso === 2) dibujarPaso2();
    if (paso === 3) dibujarPaso3();
    actualizar();
    contenido.scrollTop = 0;
  }

  // ===== PASO 1: galería =====
  function dibujarPaso1() {
    const zonaGrupos = h('div', { class: 'galeria' });
    const buscador = h('input', {
      type: 'search', class: 'buscador', placeholder: 'Buscar pieza (ej. babeta, codo, sombrero…)', 'aria-label': 'Buscar pieza',
      oninput: () => llenar(buscador.value),
    });
    function llenar(texto) {
      zonaGrupos.replaceChildren();
      const grupos = agruparPlantillas(datos.catalogo, filtrarPlantillas(datos.catalogo, texto));
      if (!grupos.length) zonaGrupos.append(h('p', {}, 'No hay piezas con ese nombre. Probá con "Pieza especial libre".'));
      for (const grupo of grupos) {
        zonaGrupos.append(h('h3', { class: 'grupo-titulo' }, grupo.nombre),
          h('div', { class: 'tarjetas' }, grupo.plantillas.map(tarjetaDePlantilla)));
      }
    }
    contenido.append(h('div', { class: 'paso-1' }, buscador, zonaGrupos));
    llenar('');
    buscador.focus();
  }

  function tarjetaDePlantilla(plantilla) {
    const miniatura = plantilla.tipoPieza === 'plegada'
      ? svgDelPerfil(plantilla.perfil, { config: datos.config, ancho: 160, alto: 110, miniatura: true })
      : (plantilla.usaPerfil
        ? svgDelPerfil(plantilla.perfil, { config: datos.config, ancho: 160, alto: 110, miniatura: true })
        : svgMiniaturaEspecial(plantilla.generador3d));
    return h('button', {
      type: 'button', class: 'tarjeta-plantilla',
      onclick: () => {
        borrador = crearRenglonDesdePlantilla(plantilla, datos.config);
        paso = 2;
        dibujarPaso();
      },
    },
    h('div', { class: 'miniatura', html: miniatura }),
    h('span', { class: 'nombre-plantilla' }, plantilla.nombre),
    plantilla.supuesto ? h('span', { class: 'etiqueta-supuesto' }, 'medidas de ejemplo') : null);
  }

  // ===== PASO 2: medidas y dibujo =====
  function dibujarPaso2() {
    const plantilla = buscarPlantilla(datos.catalogo, borrador.plantillaId);
    const esPlegada = borrador.tipoPieza === 'plegada';
    const usaPerfil = esPlegada || borrador.usaPerfil;

    const panelMedidas = h('section', { class: 'panel panel-medidas', 'data-panel': 'medidas' });
    const panel2d = h('section', { class: 'panel panel-2d', 'data-panel': '2d' }, h('h3', {}, 'Dibujo 2D acotado'));
    const zonaSvg = h('div', { class: 'zona-svg' });
    const zonaLaser = h('div', { class: 'zona-laser' });
    panel2d.append(zonaSvg, zonaLaser);
    const panel3d = h('section', { class: 'panel panel-3d', 'data-panel': '3d' }, h('h3', {}, 'Vista 3D'), contenedor3d, botones3d);

    // 2D interactivo: tocar un tramo lo marca en la tabla y en el 3D.
    zonaSvg.addEventListener('click', (e) => {
      const indice = e.target.closest('[data-tramo]')?.dataset.tramo;
      if (indice !== undefined) { resaltar(Number(indice)); editor?.resaltarFila(Number(indice)); }
    });
    zonaSvg.addEventListener('mouseover', (e) => {
      const indice = e.target.closest('[data-tramo]')?.dataset.tramo;
      if (indice !== undefined) resaltar(Number(indice));
    });

    // --- Encabezado del paso: nombre, largo y "con pendiente" ---
    const encabezado = encabezadoPaso2(plantilla);

    // --- Medidas: tabla de tramos o formulario de parámetros ---
    if (usaPerfil) {
      if (borrador.usaPerfil) {
        panelMedidas.append(h('p', { class: 'texto-chico' }, 'La tapa lleva el perfil de la canaleta. Copialo de una canaleta (arriba) o corregilo en la tabla.'));
      }
      editor = crearEditorTramos({
        perfil: borrador.perfil,
        datos,
        alCambiar: (perfil) => { borrador.perfil = perfil; actualizar(); },
        alResaltar: (indice) => resaltar(indice),
        alDibujarAMano: () => abrirDibujoAMano(panelMedidas),
        conPendiente: esPlegada && borrador.conPendiente,
      });
      panelMedidas.append(editor.elemento);
      quitarAtajosEditor = registrarAtajos('Tabla de tramos', editor.listaAtajos);
    }
    if (!esPlegada) {
      formularioActual = formularioParametros(plantilla);
      panelMedidas.append(formularioActual);
    }
    if (borrador.accesorios) {
      panelMedidas.append(panelAccesorios());
    }

    // --- Pestañas para celular ---
    const pestanas = h('div', { class: 'pestanas-celular', role: 'tablist' },
      ...[['medidas', 'Medidas'], ['2d', '2D'], ['3d', '3D']].map(([id, texto]) =>
        h('button', {
          type: 'button', role: 'tab', class: `pestana${pestanaCelular === id ? ' activa' : ''}`,
          onclick: (e) => {
            pestanaCelular = id;
            grilla.dataset.pestana = id;
            pestanas.querySelectorAll('.pestana').forEach((b) => b.classList.toggle('activa', b === e.currentTarget));
          },
        }, texto)));

    const grilla = h('div', { class: 'paso2-grilla', 'data-pestana': pestanaCelular }, panelMedidas, panel2d, panel3d);
    contenido.append(encabezado, pestanas, grilla);
    dibujar2d();
  }

  /** Encabezado del paso 2. Se puede rehacer solo (al prender la pendiente) sin perder la tabla. */
  function encabezadoPaso2(plantilla) {
    const esPlegada = borrador.tipoPieza === 'plegada';
    const usaPerfil = esPlegada || borrador.usaPerfil;
    const encabezado = h('div', { class: 'paso2-encabezado' },
      h('div', {}, h('strong', {}, plantilla?.nombre || 'Pieza'),
        plantilla?.ayuda ? h('div', { class: 'texto-chico' }, plantilla.ayuda) : null),
      usaPerfil ? h('div', { class: 'recordatorio-exteriores', role: 'note' }, 'Cargá medidas EXTERIORES ', ayuda(datos.glosario, 'medida_exterior')) : null);

    const campos = h('div', { class: 'fila-campos' });
    if (borrador.usaLargo) {
      campoLargo = h('input', {
        type: 'text', inputmode: 'decimal', class: 'campo-largo',
        value: leerNumero(borrador.largoCm) > 0 ? formatearNumero(borrador.largoCm / 100, 2) : '',
        'aria-label': 'Largo de la pieza en metros',
        oninput: (e) => {
          const metros = leerNumero(e.target.value);
          borrador.largoCm = Number.isFinite(metros) ? Math.round(metros * 10000) / 100 : null;
          actualizar();
        },
      });
      campos.append(h('label', {}, 'Largo de la pieza (m) ', campoLargo));
    }
    if (borrador.usaPerfil) campos.append(selectorCopiarPerfil());
    if (esPlegada) {
      // Plegado con pendiente: el perfil cambia de una punta a la otra.
      campos.append(h('button', {
        type: 'button', class: `boton boton-pendiente${borrador.conPendiente ? ' activo' : ''}`, 'aria-pressed': String(Boolean(borrador.conPendiente)),
        title: 'La pieza cambia de perfil de una punta a la otra (por ejemplo, una canaleta más honda hacia la bajada)',
        onclick: () => alternarPendiente(),
      }, borrador.conPendiente ? 'Con pendiente: sí' : 'Con pendiente', etiquetaAtajo('Alt+L')));
    }
    encabezado.append(campos);
    if (esPlegada && borrador.conPendiente) {
      encabezado.append(h('p', { class: 'aviso-caja nota-pendiente', role: 'note' },
        'Con pendiente: en la tabla cargá cada tramo en la punta IZQUIERDA (inicio) y en la DERECHA (final). ',
        'Los dos perfiles tienen los mismos tramos, en el mismo orden. Se cotiza por el desarrollo mayor.'));
    }
    return encabezado;
  }

  /** Tapa suelta: copiar el perfil de una canaleta de esta nota o de una plantilla. */
  function selectorCopiarPerfil() {
    const deLaNota = nota.renglones.filter((r) => r.elemento === 'canaleta' && r.perfil?.tramos?.length);
    const plantillas = datos.catalogo.plantillas.filter((p) => p.elemento === 'canaleta' && p.tipoPieza === 'plegada');
    const opcionesCopia = [{ valor: '', texto: 'elegir…' }]
      .concat(deLaNota.map((r) => ({ valor: `renglon:${r.id}`, texto: `Renglón ${nota.renglones.indexOf(r) + 1}: ${calcularRenglon(r, datos).descripcion}` })))
      .concat(plantillas.map((p) => ({ valor: `plantilla:${p.id}`, texto: `Plantilla: ${p.nombre}` })));
    return h('label', {}, 'Copiar perfil de ',
      selector(opcionesCopia, '', {
        onchange: (e) => {
          const [tipo, id] = e.target.value.split(':');
          const origen = tipo === 'renglon' ? nota.renglones.find((r) => r.id === id) : buscarPlantilla(datos.catalogo, id);
          if (!origen) return;
          borrador.perfil = copiarPerfil(origen.perfil);
          if (tipo === 'renglon') {
            // También el material y el color de esa canaleta.
            Object.assign(borrador, { materialId: origen.materialId, calibreId: origen.calibreId, terminacion: origen.terminacion, colorId: origen.colorId, ladoPintura: origen.ladoPintura });
          }
          dibujarPaso();
        },
      }));
  }

  /** Canaletas: tapas (ninguna, soldada o engrampada) y boquetas puestas, con su forma, medida y posición. */
  function panelAccesorios() {
    const acc = borrador.accesorios;
    const opcionesTapa = datos.config.accesoriosCanaleta.tiposDeTapa.map((t) => ({ valor: t, texto: t }));
    const zona = h('section', { class: 'panel-accesorios' }, h('h3', {}, 'Tapas y boquetas de la canaleta'));
    zona.append(h('div', { class: 'fila-campos' },
      h('label', { class: 'campo-parametro' }, h('span', {}, 'Tapa izquierda'),
        selector(opcionesTapa, acc.tapaIzquierda, { onchange: (e) => { acc.tapaIzquierda = e.target.value; actualizar(); } })),
      h('label', { class: 'campo-parametro' }, h('span', {}, 'Tapa derecha'),
        selector(opcionesTapa, acc.tapaDerecha, { onchange: (e) => { acc.tapaDerecha = e.target.value; actualizar(); } }))));

    const numero = (objeto, campo, etiqueta) => h('label', { class: 'campo-parametro' }, h('span', {}, `${etiqueta} (cm)`),
      h('input', {
        type: 'text', inputmode: 'decimal', class: 'campo-medida', value: String(objeto[campo] ?? '').replace('.', ','),
        oninput: (e) => { const n = leerNumero(e.target.value); objeto[campo] = Number.isFinite(n) ? n : e.target.value; actualizar(); },
      }));

    acc.boquetas.forEach((b, i) => {
      const campos = [
        h('strong', { class: 'numero-boqueta' }, `Boqueta ${i + 1}`),
        h('label', { class: 'campo-parametro' }, h('span', {}, 'Forma'),
          selector(FORMAS_BOQUETA.map((f) => ({ valor: f, texto: f })), b.forma, {
            onchange: (e) => { b.forma = e.target.value; zona.replaceWith(panelAccesorios()); actualizar(); },
          })),
      ];
      if (b.forma === 'redonda') campos.push(numero(b, 'diametroCm', 'Diámetro'));
      else if (b.forma === 'cuadrada') campos.push(numero(b, 'ladoACm', 'Lado'));
      else campos.push(numero(b, 'ladoACm', 'Lado a'), numero(b, 'ladoBCm', 'Lado b'));
      campos.push(numero(b, 'largoBocaCm', 'Largo de la boca'), numero(b, 'posicionCm', 'Posición desde la punta izq.'),
        h('button', {
          type: 'button', class: 'boton chico peligro',
          onclick: () => { acc.boquetas.splice(i, 1); zona.replaceWith(panelAccesorios()); actualizar(); },
        }, 'Quitar'));
      zona.append(h('div', { class: 'fila-campos fila-boqueta' }, campos));
    });
    zona.append(h('button', { type: 'button', class: 'boton', onclick: () => agregarBoqueta() }, 'Agregar boqueta', etiquetaAtajo('Alt+Q')),
      h('p', { class: 'texto-chico' }, 'La posición se mide desde la punta izquierda de la canaleta hasta el centro de la boqueta.'));
    enterPasaAlSiguiente(zona);
    return zona;
  }

  /** @returns {number|null} el número de la boqueta nueva (empieza en 0) */
  function agregarBoqueta() {
    if (paso !== 2 || !borrador?.accesorios) return null;
    borrador.accesorios.boquetas.push(crearBoqueta(datos.config));
    contenido.querySelector('.panel-accesorios')?.replaceWith(panelAccesorios());
    actualizar();
    const indice = borrador.accesorios.boquetas.length - 1;
    if (editor3d) editor3d.seleccionar({ tipo: 'boqueta', indice });
    return indice;
  }

  function formularioParametros(plantilla) {
    const formulario = h('div', { class: 'formulario-parametros' }, h('h3', {}, 'Medidas de la pieza'));
    for (const definicion of parametrosVisibles(plantilla || {}, borrador.parametros)) {
      const valorActual = borrador.parametros[definicion.id];
      let campo;
      if (definicion.tipo === 'opciones') {
        campo = selector(definicion.opciones.map((o) => ({ valor: o.valor, texto: o.etiqueta })), valorActual, {
          onchange: (e) => {
            borrador.parametros[definicion.id] = leerNumero(e.target.value) || e.target.value;
            // Si cambió la forma, cambian las medidas que se piden.
            if (definicion.id === 'forma') refrescarCamposPaso2();
            actualizar();
          },
        });
      } else {
        const entrada = h('input', {
          type: 'text', inputmode: 'decimal', value: String(valorActual ?? '').replace('.', ','),
          oninput: (e) => {
            const n = leerNumero(e.target.value);
            borrador.parametros[definicion.id] = Number.isFinite(n) ? n : e.target.value;
            actualizar();
          },
        });
        campo = entrada;
        if (definicion.tipo === 'diametro') {
          // Botones rápidos de diámetros en pulgadas.
          campo = h('span', { class: 'campo-con-atajos' }, entrada,
            datos.config.diametrosComunesCm.map((d) => h('button', {
              type: 'button', class: 'boton chico',
              onclick: () => { entrada.value = String(d.valor).replace('.', ','); borrador.parametros[definicion.id] = d.valor; actualizar(); },
            }, d.etiqueta.split(' ')[0])));
        }
      }
      formulario.append(h('label', { class: 'campo-parametro' },
        h('span', {}, `${definicion.etiqueta}${definicion.unidad ? ` (${definicion.unidad})` : ''}`),
        campo,
        definicion.ayuda ? h('span', { class: 'texto-chico' }, definicion.ayuda) : null));
    }
    enterPasaAlSiguiente(formulario);
    return formulario;
  }

  function abrirDibujoAMano(panelMedidas) {
    const panel = crearDibujoAMano({
      config: datos.config,
      alTerminar: (perfil) => {
        panel.remove();
        editor.elemento.hidden = false;
        editor.reemplazarPerfil(perfil);
        mostrarAviso('Listo: el dibujo se pasó a la tabla. Revisá las medidas.', 'ok');
      },
      alCancelar: () => { panel.remove(); editor.elemento.hidden = false; },
    });
    editor.elemento.hidden = true;
    panelMedidas.append(panel);
  }

  // ===== PASO 3: material y cantidad =====
  function dibujarPaso3() {
    const formulario = h('div', { class: 'formulario-material' });
    const { materiales } = datos;
    const material = materiales.materiales.find((m) => m.id === borrador.materialId) || materiales.materiales[0];

    const campo = (texto, control, idAyuda) => h('label', { class: 'campo-parametro' },
      h('span', {}, texto, idAyuda ? ayuda(datos.glosario, idAyuda) : null), control);

    if (!borrador.sinMaterial) {
    formulario.append(campo('Material', selector(materiales.materiales.map((m) => ({ valor: m.id, texto: m.nombre })), borrador.materialId, {
      onchange: (e) => {
        borrador.materialId = e.target.value;
        const nuevo = materiales.materiales.find((m) => m.id === e.target.value);
        if (!nuevo.terminaciones.includes(borrador.terminacion)) borrador.terminacion = nuevo.terminaciones[0];
        dibujarPaso();
      },
    }), 'galvanizada'));

    formulario.append(campo('Calibre', selector(materiales.calibres.map((c) => ({
      valor: c.id, texto: `C${c.numero} (${formatearCorto(c.espesorMm)} mm)${c.supuesto ? ' *' : ''}`,
    })), borrador.calibreId, { onchange: (e) => { borrador.calibreId = e.target.value; actualizar(); } }), 'calibre'));

    formulario.append(campo('Terminación', selector(material.terminaciones.map((t) => ({
      valor: t, texto: materiales.terminaciones.find((x) => x.codigo === t)?.nombre || t,
    })), borrador.terminacion, {
      onchange: (e) => {
        borrador.terminacion = e.target.value;
        if (borrador.terminacion === 'P' && !borrador.colorId) borrador.colorId = materiales.colores[0].id;
        dibujarPaso();
      },
    }), 'prepintada'));

    if (borrador.terminacion === 'P') {
      formulario.append(campo('Color', h('div', { class: 'muestras-color', role: 'radiogroup' },
        materiales.colores.map((c) => h('button', {
          type: 'button', role: 'radio', 'aria-checked': String(borrador.colorId === c.id),
          class: `muestra-color${borrador.colorId === c.id ? ' elegido' : ''}`,
          onclick: () => { borrador.colorId = c.id; dibujarPaso(); },
        }, h('span', { class: 'cuadradito', style: `background:${c.hex}` }), c.nombre)))));
      formulario.append(campo('Lado de la pintura', h('div', { class: 'opciones-radio' },
        datos.config.ladosPintura.map((opcion) => h('label', { class: 'casilla' },
          h('input', { type: 'radio', name: 'lado-pintura', value: opcion.valor, checked: borrador.ladoPintura === opcion.valor, onchange: () => { borrador.ladoPintura = opcion.valor; actualizar(); } }),
          ` ${opcion.texto}`))), 'lado_pintura'));
    }
    } else {
      formulario.append(h('p', { class: 'texto-chico' }, 'Artículo de catálogo: no lleva material, calibre ni color.'));
    }

    formulario.append(campo('Cantidad', h('input', {
      type: 'text', inputmode: 'numeric', value: String(borrador.cantidad ?? 1),
      oninput: (e) => { borrador.cantidad = leerNumero(e.target.value); actualizar(); },
    })));

    // Desarrollo manual (solo piezas especiales que tienen desarrollo).
    if (borrador.tipoPieza === 'especial' && borrador.calculoDesarrollo !== 'unidad') {
      formulario.append(campo('Corregir desarrollo a mano (cm, opcional)', h('input', {
        type: 'text', inputmode: 'decimal', value: borrador.desarrolloManualCm ? String(borrador.desarrolloManualCm).replace('.', ',') : '',
        placeholder: 'vacío = usa la fórmula',
        oninput: (e) => { const n = leerNumero(e.target.value); borrador.desarrolloManualCm = n > 0 ? n : null; actualizar(); },
      }), 'desarrollo'));
    }

    formulario.append(campo('Observaciones', h('textarea', {
      rows: 3, maxlength: 300, placeholder: 'Ej.: entregar con la tapa puesta',
      oninput: (e) => { borrador.observaciones = e.target.value; },
    }, borrador.observaciones || '')));

    // Código pendiente (si el código no está en la tabla).
    const zonaPendiente = h('div', { class: 'zona-pendiente' });
    formulario.append(zonaPendiente);
    enterPasaAlSiguiente(formulario);

    const vista2d = h('section', { class: 'panel panel-2d' }, h('h3', {}, 'Dibujo 2D'), h('div', { class: 'zona-svg' }), h('div', { class: 'zona-laser' }));
    const vista3d = h('section', { class: 'panel panel-3d' }, h('h3', {}, 'Vista 3D'), contenedor3d, botones3d);
    contenido.append(h('div', { class: 'paso3-grilla' }, h('section', { class: 'panel' }, h('h3', {}, 'Material y cantidad'), formulario), vista2d, vista3d));
    dibujar2d();
  }

  // ---------- actualización en vivo ----------

  let temporizador3d = null;
  function actualizar() {
    if (!borrador) {
      panelResultados.replaceChildren(h('span', {}, 'Elegí una pieza de la galería.'));
      return;
    }
    resultado = calcularRenglon(borrador, datos);
    dibujarResultados();
    editor?.mostrarProblemas(resultado.problemasTramos);
    dibujar2d();
    dibujarZonaPendiente();
    clearTimeout(temporizador3d);
    temporizador3d = setTimeout(() => actualizar3d(false), 120);
    editor3d?.refrescar();
    opciones.alCambiarBorrador?.(borrador, paso);
  }

  function dibujarResultados() {
    const r = resultado;
    const partes = [];
    partes.push(h('span', { class: 'resultado-dato' }, 'Desarrollo ',
      h('strong', {}, r.porUnidad ? 'por unidad' : (r.desarrolloCm > 0 ? `D = ${formatearCorto(r.desarrolloCm, 1)} cm${r.desarrolloEsManual ? ' (a mano)' : ''}` : '—'))));
    partes.push(h('span', { class: 'resultado-dato' }, 'Banda ',
      h('strong', {}, r.banda.numero ? `${r.banda.nombre} (${r.banda.numero})` : r.banda.nombre)));
    partes.push(h('span', { class: 'resultado-dato' }, 'Código ',
      h('strong', { class: r.codigo.encontrado ? 'codigo-ok' : 'codigo-falta' },
        r.codigo.encontrado ? r.codigo.codigo : (borrador.codigoPendiente ? 'PENDIENTE' : 'no encontrado')),
      r.codigo.generico ? h('span', { class: 'texto-chico' }, ' (genérico)') : null,
      ...r.codigosAdicionales.map((c) => h('span', { class: 'texto-chico codigo-extra' }, ` + ${c.codigo} x${c.cantidad} (${c.descripcion})`))));
    const mensajes = [
      ...r.errores.map((m) => h('li', { class: 'error' }, h('strong', {}, 'Error: '), m)),
      ...r.avisos.filter((m) => !m.startsWith('Código genérico')).map((m) => h('li', { class: 'aviso' }, h('strong', {}, 'Aviso: '), m)),
    ];
    panelResultados.replaceChildren(
      h('div', { class: 'resultados-datos' }, ...partes),
      h('div', { class: 'descripcion-viva' }, r.descripcion),
      h('ul', { class: 'lista-mensajes', hidden: mensajes.length === 0 }, mensajes));
  }

  function dibujarZonaPendiente() {
    const zona = contenido.querySelector('.zona-pendiente');
    if (!zona) return;
    zona.replaceChildren();
    if (!resultado.codigo.encontrado || borrador.codigoPendiente) {
      zona.append(h('label', { class: 'casilla aviso-caja' },
        h('input', { type: 'checkbox', checked: borrador.codigoPendiente, onchange: (e) => { borrador.codigoPendiente = e.target.checked; actualizar(); } }),
        ' Marcar "código pendiente" (lo completa administración) ', ayuda(datos.glosario, 'codigo_pendiente')));
    }
  }

  function dibujar2d() {
    if (!borrador) return;
    const conPendiente = tienePendiente(borrador);
    for (const zonaSvg of contenido.querySelectorAll('.zona-svg')) {
      const usaPerfil = borrador.tipoPieza === 'plegada' || borrador.usaPerfil;
      const opcionesSvg = {
        config: datos.config, resaltado, interactivo: true,
        ladoPintura: borrador.terminacion === 'P' ? borrador.ladoPintura : null,
      };
      zonaSvg.classList.toggle('dos-perfiles', conPendiente);
      if (conPendiente) {
        // Los dos perfiles, uno al lado del otro: punta izquierda (inicio) y derecha (final).
        zonaSvg.innerHTML = `<figure><figcaption>Punta izquierda (inicio)</figcaption>${svgDelPerfil(borrador.perfil, opcionesSvg)}</figure>`
          + `<figure><figcaption>Punta derecha (final)</figcaption>${svgDelPerfil(perfilFinal(borrador.perfil), opcionesSvg)}</figure>`;
      } else {
        zonaSvg.innerHTML = usaPerfil ? svgDelPerfil(borrador.perfil, opcionesSvg) : svgDeEspecial(borrador);
      }
    }
    for (const zonaLaser of contenido.querySelectorAll('.zona-laser')) {
      const conLaser = (borrador.perfil?.tramos || []).map((t, i) => ({ t, i })).filter(({ t }) => t.corteLaser);
      zonaLaser.innerHTML = (conPendiente && resultado?.pendiente ? svgPendienteLateral(borrador, resultado.pendiente, { config: datos.config }) : '')
        + conLaser.map(({ t, i }) => svgCorteLaser(t, i + 1, borrador.largoCm, datos.config)).join('')
        + svgPlantaCanaleta(borrador);
    }
  }

  function actualizar3d(reencuadrar) {
    if (!visor || !borrador) return;
    try {
      visor.mostrar(borrador, datos, { reencuadrar });
      visor.resaltarTramo(resaltado);
    } catch (error) {
      console.warn('No se pudo dibujar el 3D:', error);
    }
  }

  function resaltar(indice) {
    if (resaltado === indice) return;
    resaltado = indice;
    dibujar2d();
    visor?.resaltarTramo(indice);
  }

  // ---------- cotas y editor 3D ----------

  function alternarCotas() {
    if (!visor) return;
    visor.mostrarCotas(!visor.cotasVisibles());
    botonCotas.setAttribute('aria-pressed', String(visor.cotasVisibles()));
  }

  /** Cambia el perfil pasando por la tabla de tramos (así se puede deshacer). */
  function modificarPerfil(cambio, nuevoSeleccionado) {
    if (editor) {
      editor.modificarPerfil(cambio, nuevoSeleccionado);
    } else {
      borrador.perfil = cambio(copiarPerfil(borrador.perfil));
      resaltado = nuevoSeleccionado ?? resaltado;
      actualizar();
    }
  }

  /** Cambios del editor 3D que no son del perfil: largo, parámetros, tapas y boquetas. */
  function cambiarBorrador(cambio) {
    cambio(borrador);
    refrescarCamposPaso2();
    actualizar();
  }

  /** Pone al día los campos del paso 2 que se pueden cambiar desde el 3D. */
  function refrescarCamposPaso2() {
    if (campoLargo && document.activeElement !== campoLargo) {
      campoLargo.value = leerNumero(borrador.largoCm) > 0 ? formatearNumero(borrador.largoCm / 100, 2) : '';
    }
    if (formularioActual) {
      const nuevo = formularioParametros(buscarPlantilla(datos.catalogo, borrador.plantillaId));
      formularioActual.replaceWith(nuevo);
      formularioActual = nuevo;
    }
    contenido.querySelector('.panel-accesorios')?.replaceWith(panelAccesorios());
    editor3d?.refrescar({ forzar: true });
  }

  /** Elegir un tramo, una tapa o una boqueta (tocándola en el 3D, en su cartel o en la tabla). */
  function seleccionarParte(seleccion) {
    if (seleccion?.tipo === 'tramo') {
      resaltar(seleccion.indice);
      editor?.resaltarFila(seleccion.indice);
    }
    resaltarParte(seleccion);
    editor3d?.seleccionar(seleccion);
  }

  function resaltarParte(seleccion) {
    if (!seleccion || seleccion.tipo === 'tramo') visor?.resaltarAccesorio(null);
    if (seleccion?.tipo === 'tramo') resaltar(seleccion.indice);
    if (seleccion?.tipo === 'boqueta') { resaltar(null); visor?.resaltarAccesorio(`boqueta:${seleccion.indice}`); }
    if (seleccion?.tipo === 'tapa') { resaltar(null); visor?.resaltarAccesorio(`tapa:${seleccion.lado}`); }
  }

  /**
   * El vendedor tocó una cota del 3D: agregar un tramo, elegir una parte o cambiar una medida.
   * @returns {{ok: boolean, mensaje?: string}|undefined}
   */
  function usarCota(editar, texto) {
    if (!borrador) return undefined;
    if (editar.tipo === 'agregar') {
      const extremo = editar.extremo;
      modificarPerfil((perfil) => agregarTramoEnExtremo(perfil, extremo, { medidaCm: 10, anguloPliegue: datos.config.anguloPorDefecto, sentido: 'izquierda' }),
        extremo === 'inicio' ? 0 : borrador.perfil.tramos.length);
      const indice = extremo === 'inicio' ? 0 : borrador.perfil.tramos.length - 1;
      seleccionarParte({ tipo: 'tramo', indice });
      editor3d?.enfocarMedida();
      return { ok: true };
    }
    if (editar.tipo === 'seleccionar') {
      seleccionarParte(editar.seleccion);
      if (!editor3d && editar.seleccion.tipo !== 'tramo') {
        contenido.querySelector('.panel-accesorios')?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }
      return { ok: true };
    }
    if (editar.tipo === 'parametro') {
      const plantilla = buscarPlantilla(datos.catalogo, borrador.plantillaId);
      const definicion = (plantilla?.parametros || []).find((d) => d.id === editar.id);
      if (definicion?.tipo === 'opciones') {
        borrador.parametros[editar.id] = leerNumero(texto) || texto;
        refrescarCamposPaso2();
        actualizar();
        return { ok: true };
      }
    }
    const tipoValor = editar.tipo === 'angulo' ? 'angulo' : (editar.tipo === 'boqueta-posicion' ? 'posicion' : 'medida');
    const lectura = leerValorDeCota(texto, tipoValor, datos.config);
    if (!lectura.ok) {
      mostrarAviso(lectura.mensaje, 'error');
      return lectura;
    }
    const valor = lectura.valor;
    // En un plegado con pendiente, las cotas de la punta final cambian los valores finales.
    if (editar.tipo === 'medida') modificarPerfil((perfil) => cambiarTramo(perfil, editar.indice, editar.final ? { medidaFinalCm: valor } : { medidaCm: valor }), editar.indice);
    if (editar.tipo === 'angulo') modificarPerfil((perfil) => cambiarTramo(perfil, editar.indice, editar.final ? { anguloPliegueFinal: valor } : { anguloPliegue: valor }), editar.indice);
    if (editar.tipo === 'largo') cambiarBorrador((b) => { b.largoCm = Math.round(valor * 10000) / 100; });
    if (editar.tipo === 'parametro') cambiarBorrador((b) => { b.parametros[editar.id] = valor; });
    if (editar.tipo === 'boqueta-posicion') cambiarBorrador((b) => { b.accesorios.boquetas[editar.indice].posicionCm = valor; });
    if (editar.tipo === 'medida' || editar.tipo === 'angulo') editor3d?.seleccionar({ tipo: 'tramo', indice: editar.indice });
    return { ok: true };
  }

  /** Prende o apaga "con pendiente" (solo plegados). */
  function alternarPendiente() {
    if (paso !== 2 || borrador?.tipoPieza !== 'plegada') return;
    borrador.conPendiente = !borrador.conPendiente;
    if (borrador.conPendiente) {
      // La punta final arranca igual al inicio: el vendedor cambia solo lo que difiere.
      modificarPerfil((perfil) => activarPendiente(perfil), resaltado ?? 0);
      mostrarAviso('Con pendiente: cargá en la tabla las medidas de la punta final (columnas "Final").', 'info', 6);
    }
    editor?.establecerPendiente(borrador.conPendiente);
    // Se redibuja el encabezado (botón y explicación) sin perder la tabla ni su historial.
    contenido.querySelector('.paso2-encabezado')?.replaceWith(encabezadoPaso2(buscarPlantilla(datos.catalogo, borrador.plantillaId)));
    actualizar();
    actualizar3d(true);
    editor3d?.refrescar({ forzar: true });
  }

  function abrirEdicion3d() {
    if (editor3d || paso !== 2 || !borrador) return;
    if (!visor) {
      mostrarAviso('El 3D todavía no cargó (o no está disponible sin internet).', 'info');
      return;
    }
    const plantilla = buscarPlantilla(datos.catalogo, borrador.plantillaId);
    editor3d = abrirEditor3d({
      titulo: plantilla?.nombre || 'Pieza',
      contenedor3d,
      visor,
      datos,
      obtenerBorrador: () => borrador,
      obtenerResultado: () => resultado,
      tieneHistorial: Boolean(editor),
      acciones: {
        modificarPerfil,
        cambiarBorrador,
        accionPerfil: (nombre) => {
          if (!editor) return;
          const antes = borrador.perfil.tramos.length;
          editor.acciones[nombre]();
          // Si se agregó un tramo, queda elegido para cargarle la medida.
          if (borrador.perfil.tramos.length > antes) seleccionarParte({ tipo: 'tramo', indice: editor.obtenerSeleccionado() ?? 0 });
        },
        agregarBoqueta,
        alternarPendiente,
        formularioParametros: () => (borrador.tipoPieza === 'plegada' ? null : formularioParametros(plantilla)),
        resaltarParte,
      },
      alCerrar: () => {
        editor3d = null;
        refrescarCamposPaso2();
        actualizar3d(false);
      },
    });
    // Si había un tramo marcado, arranca elegido.
    if (resaltado !== null && (borrador.tipoPieza === 'plegada' || borrador.usaPerfil)) editor3d.seleccionar({ tipo: 'tramo', indice: resaltado });
  }

  dibujarPaso();
  return { cerrar: terminar };
}
