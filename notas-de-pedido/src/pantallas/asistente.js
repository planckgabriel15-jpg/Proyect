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
import {
  crearRenglonDesdePlantilla, buscarPlantilla, filtrarPlantillas, agruparPlantillas, vincularAccesorio,
} from '../logica/renglones.js';
import { copiarPerfil } from '../logica/perfil.js';

const NOMBRES_PASOS = ['¿Qué pieza?', 'Medidas y dibujo', 'Material y cantidad'];

/**
 * Abre el asistente encima de la pantalla de la nota.
 * @param {{
 *   nota: object,                 // la nota (para vincular accesorios y ver tapas/boquetas montadas)
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
  let verMontada = false;
  let pestanaCelular = 'medidas';

  // ---------- estructura fija ----------
  const contenido = h('div', { class: 'asistente-contenido' });
  const barraProgreso = h('ol', { class: 'progreso' });
  const panelResultados = h('div', { class: 'panel-resultados', 'aria-live': 'polite' });
  const botonAtras = h('button', { type: 'button', class: 'boton', onclick: () => irAPaso(paso - 1) }, '← Atrás');
  const botonSiguiente = h('button', { type: 'button', class: 'boton principal', onclick: () => siguiente() }, 'Siguiente →');
  const contenedor3d = h('div', { class: 'contenedor-3d' }, h('p', { class: 'texto-chico' }, 'Cargando 3D…'));
  const botones3d = h('div', { class: 'barra-botones vistas-3d' },
    ...[['inicial', 'Vista inicial'], ['frente', 'Frente'], ['lateral', 'Lateral'], ['iso', 'Isométrica']].map(([vista, texto]) =>
      h('button', { type: 'button', class: 'boton chico', onclick: () => visor?.vista(vista) }, texto)));

  const raiz = h('div', { class: 'asistente', role: 'dialog', 'aria-modal': 'true', 'aria-label': 'Agregar pieza' },
    h('header', { class: 'asistente-encabezado' },
      h('h2', {}, editando ? 'Editar pieza' : 'Agregar pieza'),
      barraProgreso,
      h('button', { type: 'button', class: 'boton', onclick: () => cerrar() }, '✕ Cerrar')),
    contenido,
    h('footer', { class: 'asistente-pie' }, panelResultados, h('div', { class: 'barra-botones' }, botonAtras, botonSiguiente)));
  document.body.append(raiz);
  document.body.classList.add('con-asistente');

  // El 3D se carga una sola vez y se reutiliza en los pasos 2 y 3.
  cargar3d().then((modulo) => {
    if (!modulo) {
      contenedor3d.replaceChildren(h('p', { class: 'aviso-caja' }, 'El 3D no está disponible (¿sin internet?). El dibujo 2D sigue siendo la referencia para fabricar.'));
      return;
    }
    contenedor3d.replaceChildren();
    visor = modulo.crearVisor3d(contenedor3d, {
      alTocarTramo: (indice) => { resaltar(indice); editor?.resaltarFila(indice); },
      alPasarSobreTramo: (indice) => { if (indice !== null) resaltar(indice); },
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
    botonSiguiente.textContent = paso === 3 ? (editando ? '✓ Guardar cambios' : '✓ Agregar a la nota') : 'Siguiente →';
    contenido.replaceChildren();
    editor = null;
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
      : (plantilla.usaPerfilVinculado
        ? svgDelPerfil(buscarPlantilla(datos.catalogo, 'canaleta_nota_real').perfil, { config: datos.config, ancho: 160, alto: 110, miniatura: true })
        : svgMiniaturaEspecial(plantilla.generador3d));
    return h('button', {
      type: 'button', class: 'tarjeta-plantilla',
      onclick: () => {
        borrador = crearRenglonDesdePlantilla(plantilla, datos.config);
        // Accesorios: si en la nota hay una sola canaleta, se vinculan solos.
        if (plantilla.vinculablePara) {
          const candidatas = renglonesVinculables(plantilla);
          if (candidatas.length === 1) borrador = vincularAccesorio(borrador, candidatas[0]);
        }
        paso = 2;
        dibujarPaso();
      },
    },
    h('div', { class: 'miniatura', html: miniatura }),
    h('span', { class: 'nombre-plantilla' }, plantilla.nombre),
    plantilla.supuesto ? h('span', { class: 'etiqueta-supuesto' }, 'medidas de ejemplo') : null);
  }

  function renglonesVinculables(plantilla) {
    return nota.renglones.filter((r) => (plantilla.vinculablePara || []).includes(r.elemento) && r.id !== borrador?.id);
  }

  // ===== PASO 2: medidas y dibujo =====
  function dibujarPaso2() {
    const plantilla = buscarPlantilla(datos.catalogo, borrador.plantillaId);
    const esPlegada = borrador.tipoPieza === 'plegada';
    const usaPerfil = esPlegada || borrador.usaPerfilVinculado;

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

    // --- Encabezado del paso: nombre, largo, vínculo ---
    const encabezado = h('div', { class: 'paso2-encabezado' },
      h('div', {}, h('strong', {}, plantilla?.nombre || 'Pieza'),
        plantilla?.ayuda ? h('div', { class: 'texto-chico' }, plantilla.ayuda) : null),
      usaPerfil ? h('div', { class: 'recordatorio-exteriores', role: 'note' }, '⚠ Cargá medidas EXTERIORES ', ayuda(datos.glosario, 'medida_exterior')) : null);

    const campos = h('div', { class: 'fila-campos' });
    if (borrador.usaLargo) {
      campos.append(h('label', {}, 'Largo de la pieza (m) ',
        h('input', {
          type: 'text', inputmode: 'decimal', class: 'campo-largo',
          value: leerNumero(borrador.largoCm) > 0 ? formatearNumero(borrador.largoCm / 100, 2) : '',
          'aria-label': 'Largo de la pieza en metros',
          oninput: (e) => {
            const metros = leerNumero(e.target.value);
            borrador.largoCm = Number.isFinite(metros) ? Math.round(metros * 10000) / 100 : null;
            actualizar();
          },
        })));
    }
    if (plantilla?.vinculablePara) campos.append(selectorVinculo(plantilla));
    encabezado.append(campos);

    // --- Medidas: tabla de tramos o formulario de parámetros ---
    if (usaPerfil) {
      if (borrador.usaPerfilVinculado) {
        panelMedidas.append(h('p', { class: 'texto-chico' },
          borrador.vinculadoA ? 'La tapa copia el perfil de la canaleta vinculada. Si hace falta, corregilo acá.' : 'Vinculá la tapa a una canaleta de la nota (arriba), o cargá el perfil a mano.'));
      }
      editor = crearEditorTramos({
        perfil: borrador.perfil,
        datos,
        alCambiar: (perfil) => { borrador.perfil = perfil; actualizar(); },
        alResaltar: (indice) => resaltar(indice),
        alDibujarAMano: () => abrirDibujoAMano(panelMedidas),
      });
      panelMedidas.append(editor.elemento);
    }
    if (!esPlegada) {
      panelMedidas.append(formularioParametros(plantilla));
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

  function selectorVinculo(plantilla) {
    const candidatas = renglonesVinculables(plantilla);
    const opcionesVinculo = [{ valor: '', texto: candidatas.length ? '— sin vincular —' : '— no hay canaletas en la nota —' }]
      .concat(candidatas.map((r) => ({ valor: r.id, texto: `Renglón ${nota.renglones.indexOf(r) + 1}: ${calcularRenglon(r, datos).descripcion}` })));
    const etiqueta = h('label', {}, 'Accesorio de: ',
      selector(opcionesVinculo, borrador.vinculadoA || '', {
        onchange: (e) => {
          const principal = nota.renglones.find((r) => r.id === e.target.value);
          if (principal) {
            borrador = vincularAccesorio(borrador, principal);
          } else {
            borrador.vinculadoA = null;
          }
          dibujarPaso();
        },
      }));
    const casilla = h('label', { class: 'casilla' },
      h('input', { type: 'checkbox', checked: verMontada, disabled: !borrador.vinculadoA, onchange: (e) => { verMontada = e.target.checked; actualizar3d(true); } }),
      ' Ver montada en la canaleta');
    // Tapa sin canaleta en la nota: permitir copiar el perfil de una plantilla.
    let copiarDePlantilla = null;
    if (borrador.usaPerfilVinculado && !borrador.vinculadoA) {
      const canaletas = datos.catalogo.plantillas.filter((p) => p.elemento === 'canaleta' && p.tipoPieza === 'plegada');
      copiarDePlantilla = h('label', {}, 'Copiar perfil de: ',
        selector([{ valor: '', texto: '— elegir —' }].concat(canaletas.map((p) => ({ valor: p.id, texto: p.nombre }))), '', {
          onchange: (e) => {
            const p = buscarPlantilla(datos.catalogo, e.target.value);
            if (p) { borrador.perfil = copiarPerfil(p.perfil); dibujarPaso(); }
          },
        }));
    }
    return h('div', { class: 'fila-campos' }, etiqueta, casilla, copiarDePlantilla);
  }

  function formularioParametros(plantilla) {
    const formulario = h('div', { class: 'formulario-parametros' }, h('h3', {}, 'Medidas de la pieza'));
    for (const definicion of plantilla?.parametros || []) {
      const valorActual = borrador.parametros[definicion.id];
      let campo;
      if (definicion.tipo === 'opciones') {
        campo = selector(definicion.opciones.map((o) => ({ valor: o.valor, texto: o.etiqueta })), valorActual, {
          onchange: (e) => { borrador.parametros[definicion.id] = leerNumero(e.target.value) || e.target.value; actualizar(); },
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
        ['afuera', 'adentro'].map((lado) => h('label', { class: 'casilla' },
          h('input', { type: 'radio', name: 'lado-pintura', value: lado, checked: borrador.ladoPintura === lado, onchange: () => { borrador.ladoPintura = lado; actualizar(); } }),
          ` Pintura ${lado}`))), 'lado_pintura'));
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
        r.codigo.encontrado ? r.codigo.codigo : (borrador.codigoPendiente ? 'PENDIENTE' : 'no encontrado'))));
    const mensajes = [
      ...r.errores.map((m) => h('li', { class: 'error' }, '✖ ', m)),
      ...r.avisos.map((m) => h('li', { class: 'aviso' }, '⚠ ', m)),
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
        ' Marcar "código pendiente" (administración lo completa) ', ayuda(datos.glosario, 'codigo_pendiente')));
    }
  }

  function dibujar2d() {
    if (!borrador) return;
    for (const zonaSvg of contenido.querySelectorAll('.zona-svg')) {
      const usaPerfil = borrador.tipoPieza === 'plegada' || borrador.usaPerfilVinculado;
      zonaSvg.innerHTML = usaPerfil
        ? svgDelPerfil(borrador.perfil, {
          config: datos.config, resaltado, interactivo: true,
          ladoPintura: borrador.terminacion === 'P' ? borrador.ladoPintura : null,
        })
        : svgDeEspecial(borrador);
    }
    for (const zonaLaser of contenido.querySelectorAll('.zona-laser')) {
      const conLaser = (borrador.perfil?.tramos || []).map((t, i) => ({ t, i })).filter(({ t }) => t.corteLaser);
      zonaLaser.innerHTML = conLaser.map(({ t, i }) => svgCorteLaser(t, i + 1, borrador.largoCm, datos.config)).join('');
    }
  }

  function actualizar3d(reencuadrar) {
    if (!visor || !borrador) return;
    let renglon3d = borrador;
    let accesorios = nota.renglones.filter((r) => r.vinculadoA === borrador.id && r.id !== borrador.id);
    if (verMontada && borrador.vinculadoA) {
      // Ver el accesorio montado: se muestra la canaleta con este accesorio (en su versión actual).
      const principal = nota.renglones.find((r) => r.id === borrador.vinculadoA);
      if (principal) {
        renglon3d = principal;
        accesorios = nota.renglones.filter((r) => r.vinculadoA === principal.id && r.id !== borrador.id).concat([borrador]);
      }
    }
    try {
      visor.mostrar(renglon3d, accesorios, datos, { reencuadrar });
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

  dibujarPaso();
  return { cerrar: terminar };
}
