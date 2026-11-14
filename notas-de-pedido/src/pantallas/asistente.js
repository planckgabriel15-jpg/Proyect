// =============================================================
// asistente.js
// Asistente "Agregar pieza" en 2 pasos:
//   1) ¿Qué pieza?   galería con buscador; arriba, lo último y lo que más usa el vendedor
//   2) La pieza      UNA sola ficha: largo, cantidad, medidas y material a la vista, con el
//                    material de la pieza anterior ya puesto. Lo que se usa poco (tapas y
//                    boquetas, cortes, pendiente, observaciones, 3D) está plegado y se abre
//                    con un toque. El 2D acotado se actualiza en vivo.
// Al pie, una línea con la descripción y el código ("ver cálculo" muestra el resto).
// Lo que falta se marca al lado del campo (no en un cartel al final).
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
import { crearBoqueta } from '../logica/accesoriosCanaleta.js';
import { seccionAccesorios, seccionCortes, seccionEmpalme, agregarCorteA } from './panelesPieza.js';
import { svgCaras, svgTapasConDetalle } from '../vistas2d/carasSvg.js';
import { ajustarTramoDeChapa, tramosDeChapa } from '../logica/empalme.js';
import { svgPlantaCanaleta } from '../vistas2d/plantaCanaletaSvg.js';
import { registrarAtajos, etiquetaAtajo } from './atajos.js';
import { abrirEditor3d } from './editor3d.js';
import { leerValorDeCota } from '../logica/cotas.js';
import { cambiarTramo, agregarTramoEnExtremo } from '../logica/perfil.js';
import { tienePendiente, perfilFinal, activarPendiente } from '../logica/pendiente.js';
import { svgPendienteLateral } from '../vistas2d/pendienteSvg.js';
import { estado } from './estado.js';
import * as almacenamiento from '../datos/almacenamiento.js';
import { empresaDeNota, plantillasVisibles, plantillaEsDeEmpresa, listaEmpresas, tipoDeRenglon } from '../logica/empresas.js';
import { preferenciasVacias, materialPorDefecto, aplicarMaterial, recientesYFrecuentes } from '../logica/preferencias.js';
import { UNIDADES_DE_SERVICIO } from '../logica/chapas.js';
import { describirAccesorios } from '../logica/accesoriosCanaleta.js';
import { describirCortes } from '../logica/cortes.js';

const NOMBRES_PASOS = ['¿Qué pieza?', 'Medidas, material y cantidad'];

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
 *   preferencias?: object,        // lo que se recuerda del vendedor (logica/preferencias.js)
 *   alCambiarPreferencias?: (cambios) => void,    // tabla completa o simple, 3D abierto o cerrado
 * }} opciones
 */
export function abrirAsistente(opciones) {
  const { nota, datos } = opciones;
  const editando = Boolean(opciones.renglon && nota.renglones.some((r) => r.id === opciones.renglon.id));
  let borrador = opciones.renglon ? JSON.parse(JSON.stringify(opciones.renglon)) : null;
  // Antes había un paso 3 (material y cantidad): una pieza a medio cargar guardada ahí se abre en la ficha.
  let paso = borrador ? Math.min(opciones.paso || 2, 2) : 1;
  const preferencias = { ...preferenciasVacias(), ...(opciones.preferencias || {}) };
  const recordar = (cambios) => { Object.assign(preferencias, cambios); opciones.alCambiarPreferencias?.(cambios); };
  let resultado = null;
  let resaltado = null;
  let editor = null;
  let visor = null;
  let quitarAtajosEditor = null;
  let pestanaCelular = 'medidas';
  let editor3d = null;          // editor 3D a pantalla completa (si está abierto)
  let campoLargo = null;        // campos del paso 2 que el editor 3D puede cambiar
  let materialRecordado = null; // de dónde salió el material con el que arrancó la pieza (para avisarlo)
  let formularioActual = null;
  // Contexto de los paneles de tapas, boquetas, cortes y empalme (ver panelesPieza.js).
  const contextoPieza = {
    datos,
    renglon: () => borrador,
    alCambiar: (redibujar) => {
      if (redibujar) refrescarSecciones();
      actualizar();
      if (redibujar) editor3d?.refrescar({ forzar: true });
    },
  };

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
    { teclas: 'Ctrl+Enter', descripcion: 'Agregar la pieza a la nota', accion: () => siguiente() },
    { teclas: 'Alt+ArrowRight', descripcion: 'Agregar la pieza a la nota (igual que Ctrl+Enter)', accion: () => siguiente() },
    { teclas: 'Alt+ArrowLeft', descripcion: 'Paso anterior', accion: () => { if (paso > 1) irAPaso(paso - 1); } },
    { teclas: 'Alt+Q', descripcion: 'Agregar boqueta a la canaleta', accion: () => agregarBoqueta() },
    { teclas: 'Alt+R', descripcion: 'Agregar un corte en la chapa', accion: () => agregarCorte() },
    { teclas: 'Alt+0', descripcion: 'Vista 3D inicial', accion: () => visor?.vista('inicial') },
    { teclas: 'Alt+7', descripcion: 'Vista 3D de frente', accion: () => visor?.vista('frente') },
    { teclas: 'Alt+8', descripcion: 'Vista 3D lateral', accion: () => visor?.vista('lateral') },
    { teclas: 'Alt+9', descripcion: 'Vista 3D isométrica', accion: () => visor?.vista('iso') },
    { teclas: 'Alt+C', descripcion: 'Mostrar u ocultar las cotas del 3D', accion: () => alternarCotas() },
    { teclas: 'Alt+G', descripcion: 'Editar en 3D (pantalla completa)', accion: () => abrirEdicion3d() },
    { teclas: 'Alt+L', descripcion: 'Plegado con pendiente (sí / no)', accion: () => alternarPendiente() },
  ]);

  // El 3D se carga recién cuando se abre su panel (o el editor 3D): la ficha aparece al instante
  // y un artículo de catálogo nunca lo carga.
  let carga3d = null;
  function asegurar3d() {
    carga3d ||= cargar3d().then((modulo) => {
      if (!modulo) {
        contenedor3d.replaceChildren(h('p', { class: 'aviso-caja' }, 'El 3D no está disponible (¿sin internet?). El dibujo 2D sigue siendo la referencia para fabricar.'));
        return null;
      }
      contenedor3d.replaceChildren();
      visor = modulo.crearVisor3d(contenedor3d, {
        alTocarTramo: (indice) => seleccionarParte({ tipo: 'tramo', indice }),
        alTocarAccesorio: (clave) => {
          const [tipo, dato] = clave.split(':');
          seleccionarParte(tipo === 'tapa' ? { tipo: 'tapa', lado: dato } : { tipo, indice: Number(dato) });
        },
        alTocarVacio: () => { if (editor3d) seleccionarParte(null); },
        alPasarSobreTramo: (indice) => { if (indice !== null && !editor3d) resaltar(indice); },
        alUsarCota: (editar, valor) => usarCota(editar, valor),
      });
      actualizar3d(true);
      return visor;
    });
    return carga3d;
  }

  // ---------- navegación ----------

  function irAPaso(nuevo) {
    if (nuevo < 1 || nuevo > 2) return;
    if (nuevo === 1 && borrador && !confirmar('Si volvés a elegir la pieza se pierde lo que cargaste. ¿Seguir?')) return;
    if (nuevo === 1) borrador = null;
    paso = nuevo;
    dibujarPaso();
  }

  function siguiente() {
    if (paso === 1) return; // en el paso 1 se avanza tocando una tarjeta
    // Ficha: se agrega a la nota. Si falta algo se agrega igual (queda marcado en la nota y no deja emitir):
    // lo que falta ya está señalado al lado de cada campo, sin cartel que frene.
    resultado = calcularRenglon(borrador, datos);
    const guardado = JSON.parse(JSON.stringify(borrador));
    terminar();
    opciones.alGuardar(guardado, resultado);
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
    botonSiguiente.replaceChildren(editando ? 'Guardar cambios' : 'Agregar a la nota', etiquetaAtajo('Ctrl+Enter'));
    contenido.replaceChildren();
    editor = null;
    quitarAtajosEditor?.();
    quitarAtajosEditor = null;
    campoLargo = null;
    formularioActual = null;
    botonEditor3d.hidden = paso !== 2;
    if (paso === 1) dibujarPaso1();
    if (paso === 2) dibujarPaso2();
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
    // Catálogo de la empresa que emite la nota; con el interruptor se ve el de todo el grupo.
    const empresa = empresaDeNota(nota, datos);
    let verTodo = Boolean(estado.sesion?.verTodoElGrupo);
    const interruptor = h('label', { class: 'casilla interruptor-grupo' },
      h('input', {
        type: 'checkbox', checked: verTodo,
        onchange: async (e) => {
          verTodo = e.target.checked;
          if (estado.sesion) { estado.sesion.verTodoElGrupo = verTodo; await almacenamiento.guardarSesion(estado.sesion); }
          llenar(buscador.value);
        },
      }), ' Ver todo el grupo ', h('span', { class: 'texto-chico' }, `(sin tildar: solo el catálogo de ${empresa?.nombreCorto || 'tu empresa'})`));
    function llenar(texto) {
      zonaGrupos.replaceChildren();
      const visibles = plantillasVisibles(datos.catalogo, empresa?.id, verTodo);
      if (!texto.trim()) {
        // Lo de todos los días, arriba: reconocer es más rápido que buscar.
        const { recientes, frecuentes } = recientesYFrecuentes(preferencias, visibles);
        for (const [titulo, lista] of [['Lo último que usaste', recientes], ['Lo que más usás', frecuentes]]) {
          if (lista.length) zonaGrupos.append(h('h3', { class: 'grupo-titulo grupo-rapido' }, titulo), h('div', { class: 'tarjetas tarjetas-rapidas' }, lista.map((p) => tarjetaDePlantilla(p, empresa))));
        }
      }
      const encontradas = filtrarPlantillas(datos.catalogo, texto, visibles);
      const grupos = agruparPlantillas(datos.catalogo, encontradas);
      if (!grupos.length) {
        const enElGrupo = verTodo ? 0 : filtrarPlantillas(datos.catalogo, texto).length;
        zonaGrupos.append(h('p', {}, enElGrupo
          ? `No está en el catálogo de ${empresa?.nombreCorto}, pero hay ${enElGrupo} en otras empresas del grupo: tildá "Ver todo el grupo".`
          : 'No hay piezas con ese nombre. Probá con "Pieza especial libre".'));
      }
      for (const grupo of grupos) {
        const tarjetas = h('div', { class: 'tarjetas' }, grupo.plantillas.map((p) => tarjetaDePlantilla(p, empresa)));
        // Los grupos de artículos sin dibujo son largos: sin búsqueda van plegados (se abren con un toque).
        const soloArticulos = grupo.plantillas.every((p) => p.sinDibujo || p.generador3d === 'articulo');
        if (soloArticulos && !texto.trim()) {
          zonaGrupos.append(h('details', { class: 'grupo-plegado' }, h('summary', { class: 'grupo-titulo' }, `${grupo.nombre} (${grupo.plantillas.length})`), tarjetas));
        } else {
          zonaGrupos.append(h('h3', { class: 'grupo-titulo' }, grupo.nombre), tarjetas);
        }
      }
    }
    contenido.append(h('div', { class: 'paso-1' }, buscador, listaEmpresas(datos).length > 1 ? interruptor : null, zonaGrupos));
    llenar('');
    buscador.focus();
  }

  function tarjetaDePlantilla(plantilla, empresa) {
    const elegir = () => {
      borrador = crearRenglonDesdePlantilla(plantilla, datos.config);
      // Arranca con el material de la pieza anterior de esta nota o el último que usó el vendedor (se ve y se cambia en la ficha).
      materialRecordado = materialPorDefecto(nota, preferencias, datos.materiales);
      aplicarMaterial(borrador, materialRecordado);
      paso = 2;
      dibujarPaso();
    };
    // De otra empresa del grupo: se avisa de quién es (la nota se reparte sola a su planta).
    const ajena = empresa && !plantillaEsDeEmpresa(plantilla, empresa.id)
      ? h('span', { class: 'etiqueta-empresa' }, (plantilla.empresas || []).map((id) => listaEmpresas(datos).find((e) => e.id === id)?.nombreCorto || id).join(' · '))
      : null;
    if (plantilla.sinDibujo || plantilla.generador3d === 'articulo') {
      // Artículos, servicios y piezas con plano: tarjeta de texto (no hay dibujo que mostrar).
      const cuantos = (plantilla.parametros || []).find((d) => d.id === 'variante')?.opciones.length;
      return h('button', { type: 'button', class: 'tarjeta-plantilla sin-dibujo', onclick: elegir },
        h('span', { class: 'nombre-plantilla' }, plantilla.nombre),
        h('span', { class: 'texto-chico' }, [plantilla.marca, cuantos ? `${cuantos} modelos` : null].filter(Boolean).join(' · ')),
        ajena);
    }
    const miniatura = plantilla.tipoPieza === 'plegada'
      ? svgDelPerfil(plantilla.perfil, { config: datos.config, ancho: 160, alto: 110, miniatura: true })
      : (plantilla.usaPerfil
        ? svgDelPerfil(plantilla.perfil, { config: datos.config, ancho: 160, alto: 110, miniatura: true })
        : svgMiniaturaEspecial(plantilla.generador3d));
    return h('button', { type: 'button', class: 'tarjeta-plantilla', onclick: elegir },
      h('div', { class: 'miniatura', html: miniatura }),
      h('span', { class: 'nombre-plantilla' }, plantilla.nombre),
      plantilla.supuesto ? h('span', { class: 'etiqueta-supuesto' }, 'medidas de ejemplo') : null,
      ajena);
  }

  // ===== PASO 2: la ficha de la pieza (medidas, material y cantidad en una sola pantalla) =====
  function dibujarPaso2() {
    const plantilla = buscarPlantilla(datos.catalogo, borrador.plantillaId);
    const esPlegada = borrador.tipoPieza === 'plegada';
    const usaPerfil = esPlegada || borrador.usaPerfil;
    const conDibujo = !borrador.sinDibujo;

    const panelMedidas = h('section', { class: 'panel panel-medidas', 'data-panel': 'medidas' });
    const panel2d = h('section', { class: 'panel panel-2d', 'data-panel': '2d' }, h('h3', {}, 'Dibujo 2D acotado'));
    const zonaSvg = h('div', { class: 'zona-svg' });
    const zonaLaser = h('div', { class: 'zona-laser' });
    panel2d.append(zonaSvg, zonaLaser);
    // El 3D es una ayuda visual: va plegado y se carga recién al abrirlo. Se recuerda cómo lo dejó el vendedor.
    const abierto3d = conDibujo && (preferencias.ver3d ?? window.innerWidth >= 1100);
    const panel3d = h('details', {
      class: 'panel panel-3d', 'data-panel': '3d', open: abierto3d,
      ontoggle: (e) => {
        if (e.target.open) asegurar3d().then(() => actualizar3d(true));
        if (e.isTrusted) recordar({ ver3d: e.target.open });
      },
    }, h('summary', {}, 'Vista 3D (ayuda visual)'), contenedor3d, botones3d);
    if (abierto3d) asegurar3d();

    // 2D interactivo: tocar un tramo lo marca en la tabla y en el 3D.
    zonaSvg.addEventListener('click', (e) => {
      const indice = e.target.closest('[data-tramo]')?.dataset.tramo;
      if (indice !== undefined) { resaltar(Number(indice)); editor?.resaltarFila(Number(indice)); }
    });
    zonaSvg.addEventListener('mouseover', (e) => {
      const indice = e.target.closest('[data-tramo]')?.dataset.tramo;
      if (indice !== undefined) resaltar(Number(indice));
    });

    // --- Encabezado: nombre, largo y cantidad (lo que se carga siempre) ---
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
        // Una pieza del catálogo: alcanza con medidas y ángulos. La pieza libre arranca con la tabla completa.
        vistaSimple: !preferencias.tablaCompleta && !borrador.conPendiente,
        alCambiarVista: (simple) => recordar({ tablaCompleta: !simple }),
      });
      panelMedidas.append(editor.elemento);
      quitarAtajosEditor = registrarAtajos('Tabla de tramos', editor.listaAtajos);
    }
    if (!esPlegada) {
      formularioActual = formularioParametros(plantilla);
      panelMedidas.append(formularioActual);
    }

    // --- Material (misma pantalla; arranca con el de la pieza anterior) ---
    panelMedidas.append(bloqueMaterial());
    // Código que no está en la tabla: la casilla "código pendiente" aparece sola, a la vista.
    panelMedidas.append(h('div', { class: 'zona-pendiente' }));

    // --- Lo que se usa poco va plegado; se abre solo si ya tiene algo cargado ---
    if (esPlegada) {
      // Empalme (aparece solo si la pieza es más larga que la chapa).
      panelMedidas.append(h('div', { 'data-contenedor': 'empalme' }, seccionEmpalme(contextoPieza)));
    }
    if (borrador.accesorios) {
      const tiene = borrador.accesorios.tapaIzquierda !== 'ninguna' || borrador.accesorios.tapaDerecha !== 'ninguna' || borrador.accesorios.boquetas.length > 0;
      panelMedidas.append(plegable('accesorios', tiene, panelAccesorios()));
    }
    if (esPlegada) {
      panelMedidas.append(plegable('cortes', borrador.cortes?.length > 0, seccionCortes(contextoPieza, { agregarCorte })));
    }
    panelMedidas.append(plegable('mas', Boolean(borrador.conPendiente || borrador.observaciones || borrador.desarrolloManualCm), seccionMasOpciones()));

    // --- Pestañas para celular ---
    const pestanas = h('div', { class: 'pestanas-celular', role: 'tablist' },
      ...[['medidas', 'Datos'], ['2d', '2D'], ['3d', '3D']].map(([id, texto]) =>
        h('button', {
          type: 'button', role: 'tab', class: `pestana${pestanaCelular === id ? ' activa' : ''}`,
          onclick: (e) => {
            pestanaCelular = id;
            grilla.dataset.pestana = id;
            pestanas.querySelectorAll('.pestana').forEach((b) => b.classList.toggle('activa', b === e.currentTarget));
            if (id === '3d') panel3d.open = true;
          },
        }, texto)));

    // Sin dibujo (artículo, servicio, pieza con plano): solo el formulario, sin paneles 2D ni 3D.
    const grilla = h('div', { class: `paso2-grilla${conDibujo ? '' : ' sin-dibujo'}`, 'data-pestana': conDibujo ? pestanaCelular : 'medidas' }, panelMedidas, panel2d, panel3d);
    pestanas.hidden = !conDibujo;
    contenido.append(encabezado, pestanas, grilla);
    enterPasaAlSiguiente(panelMedidas);
    dibujar2d();
    // El cursor arranca en lo primero que hay que cargar.
    (campoLargo || contenido.querySelector('.formulario-parametros input, .formulario-parametros select, .campo-cantidad'))?.focus();
  }

  /** Sección plegada con un resumen de lo que tiene adentro (se actualiza sola). */
  function plegable(id, abierta, cuerpo) {
    return h('details', { class: 'plegable', 'data-plegable': id, open: abierta }, h('summary', {}, tituloDePlegable(id)), cuerpo);
  }

  function tituloDePlegable(id) {
    if (id === 'accesorios') {
      const texto = describirAccesorios(borrador.accesorios).replace(/^c\/ /, '');
      return `Tapas y boquetas: ${texto || 'ninguna'}`;
    }
    if (id === 'cortes') {
      const texto = describirCortes(borrador.cortes).replace(/^c\/ /, '');
      return `Cortes en la chapa: ${texto || 'ninguno'}`;
    }
    const partes = [];
    if (borrador.conPendiente) partes.push('con pendiente');
    if (borrador.desarrolloManualCm) partes.push('desarrollo a mano');
    if (borrador.observaciones) partes.push('con observaciones');
    return `Más opciones${partes.length ? `: ${partes.join(', ')}` : ' (pendiente, observaciones…)'}`;
  }

  function actualizarPlegables() {
    for (const detalle of contenido.querySelectorAll('details[data-plegable]')) {
      detalle.querySelector('summary').textContent = tituloDePlegable(detalle.dataset.plegable);
    }
  }

  /** Lo que casi nunca se toca: pendiente, desarrollo a mano y observaciones. */
  function seccionMasOpciones() {
    const seccion = h('section', { class: 'panel-mas-opciones' });
    if (borrador.tipoPieza === 'plegada') {
      // Plegado con pendiente: el perfil cambia de una punta a la otra.
      seccion.append(h('button', {
        type: 'button', class: `boton boton-pendiente${borrador.conPendiente ? ' activo' : ''}`, 'aria-pressed': String(Boolean(borrador.conPendiente)),
        title: 'La pieza cambia de perfil de una punta a la otra (por ejemplo, una canaleta más honda hacia la bajada)',
        onclick: () => alternarPendiente(),
      }, borrador.conPendiente ? 'Con pendiente: sí' : 'Con pendiente', etiquetaAtajo('Alt+L')));
    }
    // Desarrollo manual (solo piezas especiales que tienen desarrollo).
    if (borrador.tipoPieza === 'especial' && borrador.calculoDesarrollo !== 'unidad') {
      seccion.append(h('label', { class: 'campo-parametro' }, h('span', {}, 'Corregir desarrollo a mano (cm, opcional)', ayuda(datos.glosario, 'desarrollo')),
        h('input', {
          type: 'text', inputmode: 'decimal', value: borrador.desarrolloManualCm ? String(borrador.desarrolloManualCm).replace('.', ',') : '',
          placeholder: 'vacío = usa la fórmula',
          oninput: (e) => { const n = leerNumero(e.target.value); borrador.desarrolloManualCm = n > 0 ? n : null; actualizar(); },
        })));
    }
    seccion.append(h('label', { class: 'campo-parametro' }, h('span', {}, 'Observaciones'), h('textarea', {
      rows: 2, maxlength: 300, placeholder: 'Ej.: entregar con la tapa puesta',
      oninput: (e) => { borrador.observaciones = e.target.value; actualizar(); },
    }, borrador.observaciones || '')));
    return seccion;
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
        onfocus: (e) => e.target.select(),
        oninput: (e) => {
          const metros = leerNumero(e.target.value);
          borrador.largoCm = Number.isFinite(metros) ? Math.round(metros * 10000) / 100 : null;
          actualizar();
          contenido.querySelector('[data-contenedor="empalme"]')?.replaceChildren(...[seccionEmpalme(contextoPieza)].filter(Boolean));
        },
      });
      campos.append(h('label', { 'data-campo': 'largoCm' }, 'Largo de la pieza (m) ', campoLargo));
    }
    // Cantidad: junto al largo (son los dos datos que se cargan siempre).
    const unidad = borrador.tipoPieza === 'servicio' ? UNIDADES_DE_SERVICIO[borrador.parametros?.unidad]?.plural : null;
    campos.append(h('label', { 'data-campo': 'cantidad' }, `Cantidad${unidad ? ` (${unidad})` : (borrador.usaLargo ? ' (piezas)' : '')} `, h('input', {
      type: 'text', inputmode: borrador.cantidadDecimal ? 'decimal' : 'numeric', class: 'campo-cantidad', 'aria-label': 'Cantidad',
      value: String(borrador.cantidad ?? 1).replace('.', ','),
      onfocus: (e) => e.target.select(),
      oninput: (e) => { borrador.cantidad = leerNumero(e.target.value); actualizar(); },
    })));
    if (borrador.usaPerfil) campos.append(selectorCopiarPerfil());
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

  /** Canaletas: tapas (tipo, pestaña, a medida) y boquetas de cualquier tipo, en el fondo o en una tapa. */
  function panelAccesorios() {
    return seccionAccesorios(contextoPieza, { agregarBoqueta });
  }

  /** Vuelve a armar los paneles de tapas, boquetas, cortes y empalme del paso 2. */
  function refrescarSecciones() {
    if (paso !== 2 || !borrador) return;
    contenido.querySelector('[data-seccion="accesorios"]')?.replaceWith(panelAccesorios());
    contenido.querySelector('[data-seccion="cortes"]')?.replaceWith(seccionCortes(contextoPieza, { agregarCorte }));
    contenido.querySelector('[data-contenedor="empalme"]')?.replaceChildren(...[seccionEmpalme(contextoPieza)].filter(Boolean));
  }

  /** @returns {number|null} el número del corte nuevo (empieza en 0) */
  function agregarCorte() {
    if (paso !== 2 || borrador?.tipoPieza !== 'plegada') return null;
    const indice = agregarCorteA(borrador, datos.config);
    contenido.querySelector('details[data-plegable="cortes"]')?.setAttribute('open', '');
    refrescarSecciones();
    actualizar();
    if (editor3d) editor3d.seleccionar({ tipo: 'corte', indice });
    return indice;
  }

  /** @returns {number|null} el número de la boqueta nueva (empieza en 0) */
  function agregarBoqueta() {
    if (paso !== 2 || !borrador?.accesorios) return null;
    borrador.accesorios.boquetas.push({ ...crearBoqueta(datos.config), ...(preferencias.boqueta || {}) });
    contenido.querySelector('details[data-plegable="accesorios"]')?.setAttribute('open', '');
    refrescarSecciones();
    actualizar();
    const indice = borrador.accesorios.boquetas.length - 1;
    if (editor3d) editor3d.seleccionar({ tipo: 'boqueta', indice });
    return indice;
  }

  function formularioParametros(plantilla) {
    const titulos = { articulo: 'Datos del artículo', servicio: 'Datos del servicio', metalmecanica: 'Datos de la pieza' };
    const formulario = h('div', { class: 'formulario-parametros' }, h('h3', {}, titulos[tipoDeRenglon(borrador)] || 'Medidas de la pieza'));
    for (const definicion of parametrosVisibles(plantilla || {}, borrador.parametros)) {
      const valorActual = borrador.parametros[definicion.id];
      let campo;
      if (definicion.tipo === 'texto') {
        // Texto libre (alcance del servicio, descripción de la pieza, nombre del plano).
        campo = h('input', {
          type: 'text', value: String(valorActual ?? ''), maxlength: 200, autocomplete: 'off',
          oninput: (e) => { borrador.parametros[definicion.id] = e.target.value; actualizar(); },
        });
      } else if (definicion.tipo === 'multiple') {
        // Varias opciones a la vez (procesos de una pieza metalmecánica).
        campo = h('span', { class: 'opciones-multiples' }, definicion.opciones.map((o) => h('label', { class: 'casilla' },
          h('input', {
            type: 'checkbox', checked: (valorActual || []).includes(o.valor),
            onchange: (e) => {
              const actuales = new Set(borrador.parametros[definicion.id] || []);
              if (e.target.checked) actuales.add(o.valor); else actuales.delete(o.valor);
              borrador.parametros[definicion.id] = definicion.opciones.map((x) => x.valor).filter((v) => actuales.has(v));
              actualizar();
            },
          }), ` ${o.etiqueta}`)));
      } else if (definicion.tipo === 'opciones') {
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
        if (definicion.sugeridos?.length) {
          // Valores habituales a un toque (espesores en mm).
          campo = h('span', { class: 'campo-con-atajos' }, entrada, definicion.sugeridos.map((valor) => h('button', {
            type: 'button', class: 'boton chico',
            onclick: () => { entrada.value = String(valor).replace('.', ','); borrador.parametros[definicion.id] = valor; actualizar(); },
          }, String(valor).replace('.', ','))));
        }
        if (definicion.tipo === 'diametro') {
          // Botones rápidos de diámetros en pulgadas.
          campo = h('span', { class: 'campo-con-atajos' }, entrada,
            datos.config.diametrosComunesCm.map((d) => h('button', {
              type: 'button', class: 'boton chico',
              onclick: () => { entrada.value = String(d.valor).replace('.', ','); borrador.parametros[definicion.id] = d.valor; actualizar(); },
            }, d.etiqueta.split(' ')[0])));
        }
      }
      formulario.append(h('label', { class: 'campo-parametro', 'data-campo': definicion.id },
        h('span', {}, `${definicion.etiqueta}${definicion.unidad ? ` (${definicion.unidad})` : ''}${definicion.opcional ? ' (opcional)' : ''}`),
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

  // ===== Material (antes era el paso 3; ahora es un bloque de la ficha) =====
  function bloqueMaterial() {
    const formulario = h('div', { class: 'formulario-material', 'data-seccion': 'material' });
    const { materiales } = datos;
    if (borrador.sinMaterial) {
      formulario.append(h('p', { class: 'texto-chico' }, {
        servicio: 'Servicio: no lleva chapa. El material y el espesor, si hacen falta, se cargan arriba.',
        metalmecanica: 'Pieza a medida: el material y el espesor (en mm) se cargan arriba.',
      }[borrador.tipoPieza] || 'Artículo de catálogo: no lleva material, calibre ni color.'));
      return formulario;
    }
    const material = materiales.materiales.find((m) => m.id === borrador.materialId) || materiales.materiales[0];
    const campo = (texto, control, idAyuda, idCampo) => h('label', { class: 'campo-parametro', 'data-campo': idCampo },
      h('span', {}, texto, idAyuda ? ayuda(datos.glosario, idAyuda) : null), control);
    const cambiar = (cambio) => { cambio(); materialRecordado = null; refrescarMaterial(); actualizar(); };
    // Pocas opciones → botones (se ven todas y se eligen con un toque); muchas → lista.
    const botonera = (opcionesBotonera, valor, alElegir, nombre) => h('div', { class: 'botonera', role: 'radiogroup', 'aria-label': nombre },
      opcionesBotonera.map((o) => h('button', {
        type: 'button', role: 'radio', 'aria-checked': String(o.valor === valor), class: `boton chico${o.valor === valor ? ' elegido' : ''}`,
        onclick: () => cambiar(() => alElegir(o.valor)),
      }, o.texto)));

    formulario.append(h('h3', {}, 'Material'));
    if (materialRecordado) {
      formulario.append(h('p', { class: 'texto-chico nota-recordado', role: 'note' },
        materialRecordado.origen === 'nota' ? 'Igual que la pieza anterior de esta nota. ' : 'El último que usaste. ', 'Si es otro, cambialo acá.'));
    }
    const fila = h('div', { class: 'fila-material' });
    fila.append(campo('Material', selector(materiales.materiales.map((m) => ({ valor: m.id, texto: m.nombre })), borrador.materialId, {
      onchange: (e) => cambiar(() => {
        borrador.materialId = e.target.value;
        const nuevo = materiales.materiales.find((m) => m.id === e.target.value);
        if (!nuevo.terminaciones.includes(borrador.terminacion)) borrador.terminacion = nuevo.terminaciones[0];
      }),
    }), 'galvanizada', 'materialId'));
    fila.append(campo('Calibre', selector(materiales.calibres.map((c) => ({
      valor: c.id, texto: `C${c.numero} (${formatearCorto(c.espesorMm)} mm)${c.supuesto ? ' *' : ''}`,
    })), borrador.calibreId, { onchange: (e) => cambiar(() => { borrador.calibreId = e.target.value; }) }), 'calibre', 'calibreId'));
    if (material.terminaciones.length > 1) {
      fila.append(campo('Terminación', botonera(material.terminaciones.map((t) => ({ valor: t, texto: materiales.terminaciones.find((x) => x.codigo === t)?.nombre || t })),
        borrador.terminacion, (valor) => {
          borrador.terminacion = valor;
          if (valor === 'P' && !borrador.colorId) borrador.colorId = materiales.colores[0].id;
        }, 'Terminación'), 'prepintada', 'terminacion'));
    }
    formulario.append(fila);

    if (borrador.terminacion === 'P') {
      formulario.append(campo('Color', h('div', { class: 'muestras-color', role: 'radiogroup' },
        materiales.colores.map((c) => h('button', {
          type: 'button', role: 'radio', 'aria-checked': String(borrador.colorId === c.id),
          class: `muestra-color${borrador.colorId === c.id ? ' elegido' : ''}`,
          onclick: () => cambiar(() => { borrador.colorId = c.id; }),
        }, h('span', { class: 'cuadradito', style: `background:${c.hex}` }), c.nombre))), null, 'colorId'));
      formulario.append(campo('Lado de la pintura', botonera(datos.config.ladosPintura.map((o) => ({ valor: o.valor, texto: o.texto })),
        borrador.ladoPintura, (valor) => { borrador.ladoPintura = valor; }, 'Lado de la pintura'), 'lado_pintura', 'ladoPintura'));
    }
    return formulario;
  }

  /** Vuelve a armar SOLO el bloque de material (la tabla de tramos y su "deshacer" no se tocan). */
  function refrescarMaterial() {
    contenido.querySelector('[data-seccion="material"]')?.replaceWith(bloqueMaterial());
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
    marcarErroresEnCampos();
    actualizarPlegables();
    clearTimeout(temporizador3d);
    temporizador3d = setTimeout(() => actualizar3d(false), 120);
    editor3d?.refrescar();
    opciones.alCambiarBorrador?.(borrador, paso);
  }

  /**
   * Resultado en UNA línea: la descripción (lo que va a decir la nota) y el código.
   * Desarrollo, banda, fórmula, códigos de tapas y boquetas y avisos están en "ver cálculo".
   * Lo que falta se lista acá, corto, y además queda marcado al lado de cada campo.
   */
  let calculoAbierto = false;
  function dibujarResultados() {
    const r = resultado;
    const errores = r.problemas.filter((p) => p.nivel === 'error');
    const avisos = r.avisos.filter((m) => !m.startsWith('Código genérico') && !m.startsWith('Código pendiente'));
    const codigo = r.codigo.encontrado ? `${r.codigo.codigo}${r.codigo.generico ? ' (genérico)' : ''}` : (borrador.codigoPendiente ? 'PENDIENTE' : 'no encontrado');
    const linea = h('div', { class: 'resultado-linea' },
      h('span', { class: 'descripcion-viva' }, r.descripcion),
      h('span', { class: 'resultado-dato' }, 'Código ', h('strong', { class: r.codigo.encontrado ? 'codigo-ok' : 'codigo-falta' }, codigo)));
    const detalle = h('details', { class: 'ver-calculo', open: calculoAbierto, ontoggle: (e) => { calculoAbierto = e.target.open; } },
      h('summary', {}, `ver cálculo${avisos.length ? ` · ${avisos.length} aviso${avisos.length > 1 ? 's' : ''}` : ''}`),
      h('div', { class: 'resultados-datos' },
        h('span', { class: 'resultado-dato' }, 'Desarrollo ',
          h('strong', {}, r.porUnidad ? 'por unidad' : (r.desarrolloCm > 0 ? `D = ${formatearCorto(r.desarrolloCm, 1)} cm${r.desarrolloEsManual ? ' (a mano)' : ''}` : '—')),
          r.porUnidad ? null : h('span', { class: 'texto-chico' }, ` (${r.formulaDesarrollo})`)),
        h('span', { class: 'resultado-dato' }, 'Banda ', h('strong', {}, r.banda.numero ? `${r.banda.nombre} (${r.banda.numero})` : r.banda.nombre)),
        ...r.codigosAdicionales.map((c) => h('span', { class: 'resultado-dato codigo-extra' }, `+ ${c.codigo} x${c.cantidad} (${c.descripcion})`))),
      avisos.length ? h('ul', { class: 'lista-mensajes' }, avisos.map((m) => h('li', { class: 'aviso' }, h('strong', {}, 'Aviso: '), m))) : null);
    const faltan = errores.length ? h('ul', { class: 'lista-faltantes' }, errores.slice(0, 4).map((p) => h('li', {},
      h('button', { type: 'button', class: 'enlace-error', onclick: () => irAlCampo(p.campo) }, p.mensaje))),
      errores.length > 4 ? h('li', {}, `… y ${errores.length - 4} más`) : null) : null;
    panelResultados.replaceChildren(linea, faltan || '', detalle);
    botonSiguiente.classList.toggle('con-faltantes', errores.length > 0);
    botonSiguiente.title = errores.length ? 'Se puede agregar igual, pero la nota no se va a poder emitir hasta corregirlo' : '';
  }

  /** Marca cada campo con su error, al lado (y lo desmarca cuando se corrige). */
  function marcarErroresEnCampos() {
    for (const marcado of contenido.querySelectorAll('.campo-con-error')) {
      marcado.classList.remove('campo-con-error');
      marcado.querySelector('.error-campo')?.remove();
    }
    for (const p of resultado.problemas.filter((x) => x.nivel === 'error' && x.campo)) {
      const campo = contenido.querySelector(`[data-campo="${p.campo}"]`);
      if (!campo || campo.classList.contains('campo-con-error')) continue;
      campo.classList.add('campo-con-error');
      campo.append(h('span', { class: 'error-campo', role: 'alert' }, p.mensaje));
    }
  }

  /** Lleva al campo donde está el problema (abre la sección plegada si hace falta). */
  function irAlCampo(idCampo) {
    const indiceTramo = /^tramo(\d+)$/.exec(idCampo || '')?.[1];
    if (indiceTramo !== undefined) { editor?.resaltarFila(Number(indiceTramo)); contenido.querySelector(`.fila-tramo[data-tramo="${indiceTramo}"] input`)?.focus(); return; }
    const campo = idCampo ? contenido.querySelector(`[data-campo="${idCampo}"]`) : null;
    if (!campo) return;
    campo.closest('details')?.setAttribute('open', '');
    campo.scrollIntoView({ block: 'center', behavior: 'smooth' });
    campo.querySelector('input, select, textarea, button')?.focus();
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
        + svgPlantaCanaleta(borrador)
        + svgCaras(borrador, datos.config)
        + svgTapasConDetalle(borrador, datos.config);
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
    refrescarSecciones();
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
    if (seleccion?.tipo === 'corte') { resaltar(seleccion.indice !== undefined ? borrador.cortes?.[seleccion.indice]?.tramo ?? null : null); visor?.resaltarAccesorio(`corte:${seleccion.indice}`); }
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
    const tipoValor = editar.tipo === 'angulo' ? 'angulo' : (['boqueta-posicion', 'corte-posicion'].includes(editar.tipo) ? 'posicion' : 'medida');
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
    if (editar.tipo === 'corte-posicion') cambiarBorrador((b) => { b.cortes[editar.indice].posicionCm = valor; });
    if (editar.tipo === 'empalme-tramo') {
      // Se cambia un tramo de chapa y el último se ajusta solo para que la suma dé el largo.
      cambiarBorrador((b) => {
        const tramos = tramosDeChapa(b, datos.config);
        b.empalme = { modo: 'manual', tramosCm: ajustarTramoDeChapa(tramos, editar.indice, Math.round(valor * 10000) / 100, leerNumero(b.largoCm), datos.config.empalme?.solapeCm ?? 0) };
      });
    }
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
    contenido.querySelector('.panel-mas-opciones')?.replaceWith(seccionMasOpciones());
    contenido.querySelector('details[data-plegable="mas"]')?.setAttribute('open', '');
    actualizar();
    actualizar3d(true);
    editor3d?.refrescar({ forzar: true });
  }

  function abrirEdicion3d() {
    if (editor3d || paso !== 2 || !borrador || borrador.sinDibujo) return;
    if (!visor) {
      // El 3D se carga a pedido: se abre el editor apenas esté listo.
      asegurar3d().then((listo) => {
        if (listo) abrirEdicion3d();
        else mostrarAviso('El 3D no está disponible (¿sin internet?).', 'info');
      });
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
      contexto: contextoPieza,
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
        agregarCorte,
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
