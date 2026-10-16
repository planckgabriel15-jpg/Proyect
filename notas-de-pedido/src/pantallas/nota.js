// =============================================================
// nota.js
// Pantalla de la nota de pedido:
// - encabezado: origen, NP (se asigna al EMITIR), fecha, factura y cliente;
// - renglones (tarjetas con miniatura, descripción, código y cantidad);
// - agregar / editar / duplicar / eliminar piezas;
// - guardado automático del borrador cada pocos segundos;
// - emitir: valida todo, asigna el número y abre la impresión.
// =============================================================

import { h, selector, ayuda, mostrarAviso, confirmar, fechaCorta } from './util.js';
import { estado, ir, sucursalActual } from './estado.js';
import { abrirAsistente } from './asistente.js';
import * as almacenamiento from '../datos/almacenamiento.js';
import { calcularRenglon } from '../logica/calculoRenglon.js';
import { validarNota } from '../logica/validaciones.js';
import { duplicarRenglon } from '../logica/renglones.js';
import { registrarAtajos, etiquetaAtajo } from './atajos.js';
import { svgDelPerfil } from '../vistas2d/perfilSvg.js';
import { svgDeEspecial } from '../vistas2d/especialSvg.js';
import { cargar3d } from '../vistas3d/cargar3d.js';

/**
 * @param {HTMLElement} contenedor
 * @param {string} notaId  id de la nota o "nueva"
 * @returns {Promise<() => void>} función para limpiar al salir de la pantalla
 */
export async function pantallaNota(contenedor, notaId) {
  const { datos } = estado;
  let nota;
  let guardadaAlgunaVez = true;

  if (notaId === 'nueva') {
    nota = await almacenamiento.crearNotaVacia({ sucursalId: estado.sesion.sucursalHoyId, vendedorId: estado.sesion.vendedorId });
    guardadaAlgunaVez = false;
  } else {
    nota = await almacenamiento.leerNota(notaId);
    if (!nota) {
      contenedor.replaceChildren(h('p', { class: 'aviso-caja' }, 'No se encontró la nota.'), h('a', { href: '#inicio', class: 'boton' }, 'Volver al inicio'));
      return () => {};
    }
    if (nota.estado === 'emitida') {
      ir(`#imprimir/${nota.id}`);
      return () => {};
    }
  }

  let hayCambios = false;
  let asistenteAbierto = null;

  // ---------- guardado ----------

  async function guardar(silencioso = true) {
    try {
      nota = await almacenamiento.guardarBorrador(nota);
      hayCambios = false;
      if (!guardadaAlgunaVez) {
        guardadaAlgunaVez = true;
        // Cambiamos la dirección a la de esta nota sin recargar la pantalla.
        history.replaceState(null, '', `#nota/${nota.id}`);
      }
      estadoGuardado.textContent = `Guardado ${new Date().toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`;
      if (!silencioso) mostrarAviso('Borrador guardado', 'ok');
    } catch (error) {
      mostrarAviso(`No se pudo guardar: ${error.message}`, 'error', 8);
    }
  }

  function marcarCambio() {
    hayCambios = true;
    estadoGuardado.textContent = 'Cambios sin guardar…';
  }

  const intervalo = setInterval(() => { if (hayCambios) guardar(); }, (datos.config.autoguardadoSegundos || 5) * 1000);
  const guardarAlSalir = () => { if (hayCambios) guardar(); };
  window.addEventListener('beforeunload', guardarAlSalir);
  document.addEventListener('visibilitychange', guardarAlSalir);

  // ---------- encabezado ----------

  const estadoGuardado = h('span', { class: 'estado-guardado texto-chico' }, guardadaAlgunaVez ? 'Borrador' : 'Nota nueva (todavía sin guardar)');
  const campoCliente = h('input', {
    type: 'text', value: nota.cliente, placeholder: 'Nombre del cliente', autocomplete: 'off',
    oninput: (e) => { nota.cliente = e.target.value; marcarCambio(); },
  });
  const campoFactura = h('input', {
    type: 'text', value: nota.factura, placeholder: 'Pegá el número de factura', autocomplete: 'off', inputmode: 'text',
    oninput: (e) => { nota.factura = e.target.value.trim(); marcarCambio(); },
  });
  const botonPegar = navigator.clipboard?.readText
    ? h('button', {
      type: 'button', class: 'boton chico',
      onclick: async () => {
        try {
          const texto = (await navigator.clipboard.readText()).trim();
          if (texto) { campoFactura.value = texto; nota.factura = texto; marcarCambio(); }
        } catch { mostrarAviso('El navegador no dejó leer el portapapeles: pegalo con Ctrl+V', 'info'); }
      },
    }, 'Pegar')
    : null;
  const selectorOrigen = selector(datos.sucursales.map((s) => ({ valor: s.id, texto: s.nombre })), nota.sucursalId, {
    'aria-label': 'Sucursal de origen',
    onchange: (e) => { nota.sucursalId = e.target.value; marcarCambio(); },
  });

  const encabezado = h('section', { class: 'encabezado-nota panel' },
    h('div', { class: 'fila-campos' },
      h('label', { class: 'campo-parametro' }, h('span', {}, 'Origen'), selectorOrigen),
      h('div', { class: 'campo-parametro' }, h('span', {}, 'NP Nº'), h('strong', { class: 'dato-fijo' }, 'se asigna al emitir')),
      h('div', { class: 'campo-parametro' }, h('span', {}, 'Fecha'), h('strong', { class: 'dato-fijo' }, fechaCorta(new Date().toISOString())))),
    h('div', { class: 'fila-campos' },
      h('label', { class: 'campo-parametro ancho' }, h('span', {}, 'Cliente *'), campoCliente),
      h('label', { class: 'campo-parametro' }, h('span', {}, 'Factura Nº *'), h('span', { class: 'campo-con-atajos' }, campoFactura, botonPegar))),
    estadoGuardado);

  // ---------- renglones ----------

  const listaRenglones = h('div', { class: 'lista-renglones' });
  const zonaErrores = h('div', { class: 'zona-errores', 'aria-live': 'polite' });
  const zonaRecuperar = h('div');

  function numeroDeRenglon(id) {
    return nota.renglones.findIndex((r) => r.id === id) + 1;
  }

  function dibujarRenglones() {
    listaRenglones.replaceChildren();
    if (!nota.renglones.length) {
      listaRenglones.append(h('p', { class: 'vacio' }, 'Todavía no hay piezas. Tocá "Agregar pieza".'));
    }
    nota.renglones.forEach((renglon, i) => {
      const r = calcularRenglon(renglon, datos);
      const miniatura = h('div', { class: 'miniatura-renglon', 'data-renglon': renglon.id,
        html: renglon.tipoPieza === 'plegada' || renglon.usaPerfil
          ? svgDelPerfil(renglon.perfil, { config: datos.config, ancho: 200, alto: 140, miniatura: true })
          : svgDeEspecial(renglon, 640, 420) });
      listaRenglones.append(h('article', { class: `tarjeta-renglon${r.errores.length ? ' con-error' : ''}` },
        h('div', { class: 'numero-renglon' }, String(i + 1)),
        miniatura,
        h('div', { class: 'datos-renglon' },
          h('div', { class: 'descripcion-renglon' }, r.descripcion),
          h('div', {}, 'Código: ', h('strong', {}, r.codigo.encontrado ? r.codigo.codigo : (renglon.codigoPendiente ? 'PENDIENTE' : 'no encontrado')),
            r.codigo.generico ? ' (genérico)' : '',
            ' · Cantidad: ', h('strong', {}, String(renglon.cantidad))),
          r.errores.length ? h('div', { class: 'error' }, h('strong', {}, 'Error: '), `${r.errores.length} problema(s): ${r.errores[0]}`) : null,
          r.avisos.length ? h('div', { class: 'aviso' }, h('strong', {}, 'Aviso: '), r.avisos.join(' · ')) : null),
        h('div', { class: 'acciones-renglon' },
          h('button', { type: 'button', class: 'boton', onclick: () => editarRenglon(renglon) }, 'Editar'),
          h('button', { type: 'button', class: 'boton', onclick: () => duplicar(renglon) }, 'Duplicar'),
          h('button', { type: 'button', class: 'boton peligro', onclick: () => eliminar(renglon) }, 'Eliminar'))));
    });
    dibujarMiniaturas3d();
  }

  /** Cambia las miniaturas 2D por fotos 3D cuando el 3D está disponible. */
  async function dibujarMiniaturas3d() {
    const modulo = await cargar3d();
    if (!modulo) return;
    for (const renglon of nota.renglones) {
      const lugar = listaRenglones.querySelector(`.miniatura-renglon[data-renglon="${renglon.id}"]`);
      if (!lugar) continue;
      try {
        const imagen = modulo.capturarRenglon(renglon, datos, 240, 160);
        lugar.replaceChildren(h('img', { src: imagen, alt: 'Vista 3D de la pieza' }));
      } catch (error) {
        console.warn('Miniatura 3D:', error);
      }
    }
  }

  // ---------- acciones sobre renglones ----------

  function abrir(renglon, paso) {
    asistenteAbierto = abrirAsistente({
      nota, renglon, paso, datos,
      alGuardar: (guardado) => {
        const posicion = nota.renglones.findIndex((r) => r.id === guardado.id);
        if (posicion >= 0) nota.renglones[posicion] = guardado;
        else nota.renglones.push(guardado);
        delete nota.piezaEnCurso;
        asistenteAbierto = null;
        marcarCambio();
        guardar();
        dibujarRenglones();
        zonaRecuperar.replaceChildren();
        mostrarAviso(posicion >= 0 ? 'Pieza actualizada' : 'Pieza agregada a la nota', 'ok');
      },
      alCerrar: () => {
        delete nota.piezaEnCurso;
        asistenteAbierto = null;
        marcarCambio();
      },
      alCambiarBorrador: (borrador, paso) => {
        // Se guarda la pieza a medio cargar, por si se corta la luz o internet.
        nota.piezaEnCurso = { renglon: borrador, paso };
        marcarCambio();
      },
    });
  }

  function editarRenglon(renglon) { abrir(renglon); }

  function duplicar(renglon) {
    const copia = duplicarRenglon(renglon);
    nota.renglones.splice(nota.renglones.indexOf(renglon) + 1, 0, copia);
    marcarCambio();
    dibujarRenglones();
    mostrarAviso('Pieza duplicada', 'ok');
  }

  function eliminar(renglon) {
    const numero = numeroDeRenglon(renglon.id);
    if (!confirmar(`¿Eliminar el renglón ${numero}?`)) return;
    nota.renglones = nota.renglones.filter((r) => r.id !== renglon.id);
    marcarCambio();
    dibujarRenglones();
  }

  // ---------- emitir ----------

  async function emitir() {
    const resultados = nota.renglones.map((r) => calcularRenglon(r, datos));
    const validacion = validarNota(nota, resultados);
    zonaErrores.replaceChildren();
    if (!validacion.puedeEmitir) {
      zonaErrores.append(h('div', { class: 'aviso-caja error-caja' },
        h('strong', {}, 'Todavía no se puede emitir. Falta corregir:'),
        h('ul', {}, validacion.errores.map((e) => h('li', {}, e)))));
      zonaErrores.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }
    const sucursal = datos.sucursales.find((s) => s.id === nota.sucursalId);
    const avisos = validacion.avisos.length ? `\n\nAvisos:\n${validacion.avisos.map((a) => `• ${a}`).join('\n')}` : '';
    if (!confirmar(`¿Emitir la nota de ${sucursal?.nombre}?\nSe le asigna el número y ya no se puede modificar.${avisos}`)) return;

    // Se guarda una "foto" de lo calculado, para que la nota impresa no cambie si mañana cambia la tabla de códigos.
    nota.renglones = nota.renglones.map((renglon, i) => ({
      ...renglon,
      calculado: {
        descripcion: resultados[i].descripcion,
        codigo: resultados[i].codigo.encontrado ? resultados[i].codigo.codigo : null,
        desarrolloCm: resultados[i].desarrolloCm,
        desarrolloEsManual: resultados[i].desarrolloEsManual,
        banda: resultados[i].banda,
        porUnidad: resultados[i].porUnidad,
        avisos: resultados[i].avisos,
        codigoGenerico: resultados[i].codigo.generico,
      },
    }));
    delete nota.piezaEnCurso;
    try {
      await almacenamiento.guardarBorrador(nota);
      const emitida = await almacenamiento.emitirNota(nota, datos.sucursales);
      hayCambios = false;
      mostrarAviso(`Nota emitida: NP Nº ${emitida.numero}`, 'ok', 6);
      ir(`#imprimir/${emitida.id}`);
    } catch (error) {
      mostrarAviso(`No se pudo emitir: ${error.message}`, 'error', 8);
    }
  }

  // ---------- armado de la pantalla ----------

  const sucursal = sucursalActual();
  contenedor.replaceChildren(
    h('div', { class: 'titulo-pantalla' },
      h('h1', {}, 'Nota de pedido'),
      h('span', { class: 'texto-chico' }, sucursal ? `Trabajando hoy en ${sucursal.nombre}` : '')),
    zonaRecuperar,
    encabezado,
    h('section', { class: 'panel' },
      h('div', { class: 'titulo-seccion' }, h('h2', {}, 'Piezas'), ayuda(datos.glosario, 'desarrollo')),
      listaRenglones,
      h('button', { type: 'button', class: 'boton grande principal', onclick: () => abrir(null) }, 'Agregar pieza', etiquetaAtajo('Alt+P'))),
    zonaErrores,
    h('div', { class: 'barra-botones barra-final' },
      h('a', { href: '#inicio', class: 'boton' }, 'Volver al inicio'),
      h('button', { type: 'button', class: 'boton', onclick: () => guardar(false) }, 'Guardar borrador', etiquetaAtajo('Ctrl+S')),
      h('button', { type: 'button', class: 'boton grande principal', onclick: () => emitir() }, 'Emitir nota', etiquetaAtajo('Ctrl+Enter'))));

  // Atajos de teclado de la nota (F1 muestra la lista).
  const quitarAtajos = registrarAtajos('Nota de pedido', [
    { teclas: 'Alt+P', descripcion: 'Agregar pieza', accion: () => { if (!asistenteAbierto) abrir(null); } },
    { teclas: 'Ctrl+S', descripcion: 'Guardar borrador', accion: () => guardar(false) },
    { teclas: 'Ctrl+Enter', descripcion: 'Emitir nota', accion: () => { if (!asistenteAbierto) emitir(); } },
  ]);

  // ¿Quedó una pieza a medio cargar (se cortó algo)?
  if (nota.piezaEnCurso?.renglon) {
    zonaRecuperar.append(h('div', { class: 'aviso-caja' },
      h('strong', {}, 'Quedó una pieza sin terminar. '),
      h('button', { type: 'button', class: 'boton principal', onclick: () => { zonaRecuperar.replaceChildren(); abrir(nota.piezaEnCurso.renglon, nota.piezaEnCurso.paso); } }, 'Recuperarla'),
      ' ',
      h('button', { type: 'button', class: 'boton', onclick: () => { delete nota.piezaEnCurso; marcarCambio(); zonaRecuperar.replaceChildren(); } }, 'Descartarla')));
  }

  dibujarRenglones();
  if (!guardadaAlgunaVez) campoCliente.focus();

  // Limpieza al salir de la pantalla.
  return () => {
    quitarAtajos();
    clearInterval(intervalo);
    window.removeEventListener('beforeunload', guardarAlSalir);
    document.removeEventListener('visibilitychange', guardarAlSalir);
    if (hayCambios && (guardadaAlgunaVez || nota.renglones.length || nota.cliente)) guardar();
    asistenteAbierto?.cerrar();
  };
}
