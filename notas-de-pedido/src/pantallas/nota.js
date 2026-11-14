// =============================================================
// nota.js
// Pantalla de la nota de pedido:
// - encabezado: origen, NP (se asigna al EMITIR), fecha, factura y cliente;
// - fecha de entrega y prioridad (las usa producción) y la vista 3D de la nota;
// - renglones (tarjetas con miniatura, descripción, código, piezas y cantidad de chapas);
// - agregar / editar / duplicar / eliminar piezas;
// - guardado automático del borrador cada pocos segundos;
// - emitir: valida todo, asigna el número y abre la impresión.
// =============================================================

import { h, selector, ayuda, mostrarAviso, confirmar } from './util.js';
import { estado, ir, sucursalActual } from './estado.js';
import { empresaDeSucursal, empresaDeNota, sucursalesDeEmpresa, repartoPorPlanta } from '../logica/empresas.js';
import { abrirAsistente } from './asistente.js';
import * as almacenamiento from '../datos/almacenamiento.js';
import { calcularRenglon } from '../logica/calculoRenglon.js';
import { fotoDelCalculo, mostrar3d, OPCIONES_3D_NOTA } from '../logica/fotoCalculo.js';
import { cantidadDeLaNota, explicarDiferencia } from '../logica/chapas.js';
import { PRIORIDADES } from '../logica/produccion.js';
import { tiempoDeRenglon, tiempoDeNota, textoDeTiempo } from '../logica/tiemposRenglon.js';
import { cargarModelo } from './contextoProduccion.js';
import { validarNota, faltantesDeNota } from '../logica/validaciones.js';
import { registrarUso, clientesConocidos } from '../logica/preferencias.js';
import { siguienteNumeroNP } from '../logica/numeracion.js';
import { fechaEntregaDe } from '../logica/produccion.js';
import { formatearCorto, leerNumero } from '../logica/numeros.js';
import { duplicarRenglon, datosParaRepetir } from '../logica/renglones.js';
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

  if (notaId === 'nueva' || notaId.startsWith('repetir-')) {
    nota = await almacenamiento.crearNotaVacia({
      sucursalId: estado.sesion.sucursalHoyId, vendedorId: estado.sesion.vendedorId,
      empresaId: empresaDeSucursal(datos, estado.sesion.sucursalHoyId)?.id || null,
    });
    guardadaAlgunaVez = false;
    if (notaId.startsWith('repetir-')) {
      // "Lo mismo que la vez pasada": cliente y piezas de otra nota, en una nota nueva (la original no se toca).
      const original = await almacenamiento.leerNota(notaId.slice('repetir-'.length));
      if (original) {
        Object.assign(nota, datosParaRepetir(original));
        mostrarAviso(`Se copiaron ${nota.renglones.length} pieza(s) de la nota ${original.numero ?? 'en borrador'} de ${original.cliente || 'sin cliente'}. Revisá cantidades y cargá la factura nueva.`, 'ok', 8);
      }
    }
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
  // Lo que se recuerda del vendedor (último material, piezas recientes…) y los clientes de notas anteriores.
  let preferencias = await almacenamiento.leerPreferencias(estado.sesion.vendedorId);
  const clientes = clientesConocidos((await almacenamiento.listarNotas({})).filter((n) => empresaDeNota(n, datos)?.id === empresaDeSucursal(datos, estado.sesion.sucursalHoyId)?.id));
  // Modelo de tiempos (con los parámetros que haya cambiado el jefe), para mostrar el tiempo estándar.
  const { modelo } = await cargarModelo();
  const contadores = await almacenamiento.leerContadores(datos.sucursales);
  const totalTiempo = h('span', { class: 'texto-chico' });

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
  // Cliente con sugerencias de notas anteriores (se puede escribir uno nuevo igual).
  const listaClientes = h('datalist', { id: 'clientes-conocidos' }, clientes.map((nombre) => h('option', { value: nombre })));
  const campoCliente = h('input', {
    type: 'text', value: nota.cliente, placeholder: 'Nombre del cliente', autocomplete: 'off', list: 'clientes-conocidos',
    oninput: (e) => { nota.cliente = e.target.value; marcarCambio(); quitarError('cliente'); },
  });
  const campoFactura = h('input', {
    type: 'text', value: nota.factura, placeholder: 'Pegá el número de factura', autocomplete: 'off', inputmode: 'text',
    oninput: (e) => { nota.factura = e.target.value.trim(); marcarCambio(); quitarError('factura'); },
  });
  const botonPegar = navigator.clipboard?.readText
    ? h('button', {
      type: 'button', class: 'boton chico',
      onclick: async () => {
        try {
          const texto = (await navigator.clipboard.readText()).trim();
          if (texto) { campoFactura.value = texto; nota.factura = texto; marcarCambio(); quitarError('factura'); }
        } catch { mostrarAviso('El navegador no dejó leer el portapapeles: pegalo con Ctrl+V', 'info'); }
      },
    }, 'Pegar')
    : null;
  // Origen = empresa + sucursal. La empresa es la del vendedor; se elige entre SUS sucursales.
  const empresa = empresaDeNota(nota, datos);
  nota.empresaId ??= empresa?.id || null;
  const selectorOrigen = selector(sucursalesDeEmpresa(datos, empresa?.id).map((s) => ({ valor: s.id, texto: s.nombre })), nota.sucursalId, {
    'aria-label': 'Sucursal de origen',
    onchange: (e) => { nota.sucursalId = e.target.value; marcarCambio(); },
  });

  const campoEntrega = h('input', {
    type: 'date', value: nota.fechaEntrega || '', 'aria-label': 'Fecha de entrega',
    onchange: (e) => { nota.fechaEntrega = e.target.value || null; marcarCambio(); },
  });
  const selectorPrioridad = selector(PRIORIDADES, nota.prioridad || 'normal', {
    'aria-label': 'Prioridad',
    onchange: (e) => { nota.prioridad = e.target.value; marcarCambio(); },
  });
  const selector3d = selector(OPCIONES_3D_NOTA, nota.mostrar3d || 'auto', {
    'aria-label': 'Vista 3D de la nota',
    onchange: (e) => { nota.mostrar3d = e.target.value; marcarCambio(); dibujarRenglones(); },
  });

  /** Resumen de lo que hay en "Entrega, prioridad e imagen 3D" (se ve aunque esté plegado). */
  const resumenOpciones = h('summary', {});
  function actualizarResumenOpciones() {
    const [a, m, d] = String(fechaEntregaDe(nota, datos.produccion)).split('-');
    resumenOpciones.textContent = `Entrega ${d}/${m}/${a}${nota.fechaEntrega ? '' : ' (automática)'} · ${nota.prioridad === 'urgente' ? 'URGENTE' : 'prioridad normal'} · ${OPCIONES_3D_NOTA.find((o) => o.valor === (nota.mostrar3d || 'auto'))?.texto || ''}`;
  }
  for (const control of [campoEntrega, selectorPrioridad, selector3d]) control.addEventListener('change', actualizarResumenOpciones);
  actualizarResumenOpciones();

  const encabezado = h('section', { class: 'encabezado-nota panel' },
    listaClientes,
    h('div', { class: 'fila-campos' },
      h('label', { class: 'campo-parametro ancho', 'data-campo': 'cliente' }, h('span', {}, 'Cliente *'), campoCliente),
      h('label', { class: 'campo-parametro', 'data-campo': 'factura' }, h('span', {}, 'Factura Nº *'), h('span', { class: 'campo-con-atajos' }, campoFactura, botonPegar)),
      h('label', { class: 'campo-parametro', 'data-campo': 'sucursalId' }, h('span', {}, `Origen · ${empresa?.nombreCorto || ''}`), selectorOrigen)),
    // Lo que casi siempre queda como está: plegado, con su valor a la vista.
    h('details', { class: 'plegable', open: Boolean(nota.fechaEntrega) || nota.prioridad === 'urgente' },
      resumenOpciones,
      h('div', { class: 'fila-campos' },
        h('label', { class: 'campo-parametro' }, h('span', {}, 'Fecha de entrega'), campoEntrega),
        h('label', { class: 'campo-parametro' }, h('span', {}, 'Prioridad'), selectorPrioridad),
        h('label', { class: 'campo-parametro' }, h('span', {}, 'Imagen 3D'), selector3d))),
    estadoGuardado);

  /** Marca un campo del encabezado con lo que le falta (y lo desmarca al corregirlo). */
  function marcarError(campo, mensaje) {
    const lugar = encabezado.querySelector(`[data-campo="${campo}"]`);
    if (!lugar || lugar.classList.contains('campo-con-error')) return;
    lugar.classList.add('campo-con-error');
    lugar.append(h('span', { class: 'error-campo', role: 'alert' }, mensaje));
  }
  function quitarError(campo) {
    const lugar = encabezado.querySelector(`[data-campo="${campo}"]`);
    lugar?.classList.remove('campo-con-error');
    lugar?.querySelector('.error-campo')?.remove();
  }

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
    const tiempoTotal = tiempoDeNota(nota, datos, modelo);
    // Si la nota tiene renglones de más de una planta, se avisa cómo se reparte (lo hace sola).
    const reparto = repartoPorPlanta(nota, datos);
    const textoReparto = reparto.length > 1 ? ` · Se reparte sola: ${reparto.map((g) => `${g.nombre} (renglón ${g.renglones.map((n) => n + 1).join(', ')})`).join(' · ')}` : '';
    // El tiempo total es un dato de producción: queda como texto chico (el de cada pieza está en "ver cálculo").
    totalTiempo.textContent = nota.renglones.length ? `Fabricación estimada: ${textoDeTiempo(tiempoTotal.totalEstandarS)}${textoReparto}` : '';
    nota.renglones.forEach((renglon, i) => {
      const r = calcularRenglon(renglon, datos);
      const tiempo = tiempoDeRenglon(renglon, datos, modelo, r);
      const cantidad = cantidadDeLaNota(renglon, r, datos.config);
      const diferencia = explicarDiferencia(renglon, r, datos.config);
      const con3d = mostrar3d(renglon, nota, datos);
      const miniatura = renglon.sinDibujo ? null : h('div', { class: 'miniatura-renglon', 'data-renglon': renglon.id, 'data-con3d': con3d ? 'si' : 'no',
        html: renglon.tipoPieza === 'plegada' || renglon.usaPerfil
          ? svgDelPerfil(renglon.perfil, { config: datos.config, ancho: 200, alto: 140, miniatura: true })
          : svgDeEspecial(renglon, 640, 420) });
      // Cantidad editable en la tarjeta: cambiarla no obliga a abrir la pieza.
      const campoCantidad = h('input', {
        type: 'text', inputmode: renglon.cantidadDecimal ? 'decimal' : 'numeric', class: 'campo-cantidad', 'aria-label': `Cantidad del renglón ${i + 1}`,
        value: String(renglon.cantidad ?? '').replace('.', ','),
        onfocus: (e) => e.target.select(),
        onchange: (e) => { renglon.cantidad = leerNumero(e.target.value); marcarCambio(); dibujarRenglones(); },
      });
      const codigo = r.codigo.encontrado ? `${r.codigo.codigo}${r.codigo.generico ? ' (genérico)' : ''}` : (renglon.codigoPendiente ? 'PENDIENTE' : 'no encontrado');
      listaRenglones.append(h('article', { class: `tarjeta-renglon${r.errores.length ? ' con-error' : ''}`, 'data-renglon': renglon.id },
        h('div', { class: 'numero-renglon' }, String(i + 1)),
        miniatura,
        h('div', { class: 'datos-renglon' },
          h('div', { class: 'descripcion-renglon' }, r.descripcion),
          h('div', { class: 'linea-renglon' }, 'Código ', h('strong', {}, codigo),
            r.codigosAdicionales.map((c) => h('span', { class: 'codigo-extra' }, ` + ${c.codigo} x${c.cantidad}`)),
            ' · ', h('label', { class: 'campo-en-linea' }, cantidad.unidad === 'chapas' ? 'Piezas' : 'Cantidad', campoCantidad),
            cantidad.unidad === 'chapas' ? [' = ', h('strong', {}, `${cantidad.texto} chapa(s)`)] : (cantidad.abreviatura !== 'u.' ? ` ${cantidad.abreviatura}` : '')),
          // Datos de producción y del cálculo: a un toque, no encima de lo que el vendedor controla.
          h('details', { class: 'texto-chico ver-calculo' }, h('summary', {}, 'ver cálculo'),
            h('div', {}, r.porUnidad ? 'Se cotiza por unidad.' : `Desarrollo ${formatearCorto(r.desarrolloCm ?? 0, 1)} cm (${r.formulaDesarrollo}) · banda ${r.banda.nombre}`),
            cantidad.unidad === 'chapas' ? h('div', {}, `Cantidad de chapas: ${cantidad.regla} = ${cantidad.texto}`) : null,
            h('div', {}, 'Tiempo estándar de fabricación: ', tiempo.fuente === 'error' ? `sin calcular (${tiempo.estado})` : `${textoDeTiempo(tiempo.totalEstandarS)} (preparación ${textoDeTiempo(tiempo.setupEstandarS)} + ${textoDeTiempo(tiempo.piezaEstandarS)} por pieza)`),
            diferencia && Math.abs(diferencia.diferencia) >= 0.005 ? h('div', {}, 'Consumo físico estimado (no cambia la cantidad): ', diferencia.texto) : null),
          r.errores.length ? h('div', { class: 'error' }, h('strong', {}, 'Falta: '), r.errores.slice(0, 2).join(' · '), r.errores.length > 2 ? ` (y ${r.errores.length - 2} más)` : '', ' ',
            h('button', { type: 'button', class: 'boton chico', onclick: () => editarRenglon(renglon) }, 'Corregir')) : null,
          r.avisos.length ? h('div', { class: 'aviso' }, h('strong', {}, 'Aviso: '), r.avisos.join(' · ')) : null),
        h('div', { class: 'acciones-renglon' },
          h('button', { type: 'button', class: 'boton', onclick: () => editarRenglon(renglon) }, 'Editar'),
          h('button', { type: 'button', class: 'boton', onclick: () => duplicar(renglon) }, 'Duplicar'),
          renglon.sinDibujo ? null : h('button', {
            type: 'button', class: `boton chico${con3d ? ' elegido' : ''}`,
            title: renglon.mostrar3d === null || renglon.mostrar3d === undefined ? 'Imagen 3D en la hoja impresa: sigue la opción de la nota' : 'Imagen 3D en la hoja impresa: elegido en este renglón',
            onclick: () => alternar3d(renglon),
          }, `3D: ${con3d ? 'sí' : 'no'}${renglon.mostrar3d === true || renglon.mostrar3d === false ? '' : ' (auto)'}`),
          h('button', { type: 'button', class: 'boton peligro', onclick: () => eliminar(renglon) }, 'Eliminar'))));
    });
    zonaErrores.replaceChildren();
    dibujarMiniaturas3d();
  }

  /** 3D del renglón: automático → al revés de lo automático → vuelve a automático. */
  function alternar3d(renglon) {
    const automatico = mostrar3d({ ...renglon, mostrar3d: null }, nota, datos);
    if (renglon.mostrar3d === null || renglon.mostrar3d === undefined) renglon.mostrar3d = !automatico;
    else renglon.mostrar3d = null;
    marcarCambio();
    dibujarRenglones();
  }

  /** Cambia las miniaturas 2D por fotos 3D cuando el 3D está disponible (solo en los renglones con 3D). */
  async function dibujarMiniaturas3d() {
    // El 3D se baja solo si algún renglón lo muestra (una nota de artículos nunca lo carga).
    if (!listaRenglones.querySelector('.miniatura-renglon[data-con3d="si"]')) return;
    const modulo = await cargar3d();
    if (!modulo) return;
    for (const renglon of nota.renglones) {
      const lugar = listaRenglones.querySelector(`.miniatura-renglon[data-renglon="${renglon.id}"][data-con3d="si"]`);
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
      nota, renglon, paso, datos, preferencias,
      alCambiarPreferencias: (cambios) => {
        preferencias = { ...preferencias, ...cambios };
        almacenamiento.guardarPreferencias(estado.sesion.vendedorId, preferencias);
      },
      alGuardar: (guardado) => {
        const posicion = nota.renglones.findIndex((r) => r.id === guardado.id);
        if (posicion >= 0) nota.renglones[posicion] = guardado;
        else nota.renglones.push(guardado);
        // Se recuerda la pieza y su material para la próxima vez.
        preferencias = registrarUso(preferencias, guardado);
        almacenamiento.guardarPreferencias(estado.sesion.vendedorId, preferencias);
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

  /** Paso 1 de emitir: si falta algo, se marca dónde; si no, se pide la confirmación en la misma página. */
  function emitir() {
    const resultados = nota.renglones.map((r) => calcularRenglon(r, datos));
    const faltantes = faltantesDeNota(nota, resultados);
    zonaErrores.replaceChildren();
    for (const campo of ['cliente', 'factura', 'sucursalId']) quitarError(campo);
    if (faltantes.length) {
      // Cada cosa que falta se marca en su lugar y la lista lleva hasta ahí con un toque.
      for (const f of faltantes.filter((x) => x.donde === 'encabezado')) marcarError(f.campo, f.mensaje);
      const irA = (f) => {
        if (f.donde === 'encabezado') { encabezado.querySelector(`[data-campo="${f.campo}"] input, [data-campo="${f.campo}"] select`)?.focus(); return; }
        if (f.donde === 'renglon') { editarRenglon(nota.renglones.find((r) => r.id === f.renglonId)); return; }
        abrir(null);
      };
      zonaErrores.append(h('div', { class: 'aviso-caja error-caja', role: 'alert' },
        h('strong', {}, `Para emitir falta${faltantes.length > 1 ? 'n' : ''} ${faltantes.length} cosa${faltantes.length > 1 ? 's' : ''}:`),
        h('ul', { class: 'lista-faltantes' }, faltantes.slice(0, 8).map((f) => h('li', {},
          h('button', { type: 'button', class: 'enlace-error', onclick: () => irA(f) }, `${f.donde === 'renglon' ? `Renglón ${f.numero}: ` : ''}${f.mensaje}`))),
          faltantes.length > 8 ? h('li', {}, `… y ${faltantes.length - 8} más`) : null)));
      irA(faltantes[0].donde === 'encabezado' ? faltantes[0] : { donde: 'nada' });
      zonaErrores.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }
    // Emitir no se puede deshacer (le pone el número): se confirma acá mismo, sin cartel del navegador.
    const validacion = validarNota(nota, resultados);
    const sucursal = datos.sucursales.find((s) => s.id === nota.sucursalId);
    const proximo = siguienteNumeroNP(contadores, nota.sucursalId);
    const confirmarBoton = h('button', { type: 'button', class: 'boton grande principal', onclick: () => emitirDeVerdad(resultados) }, 'Emitir e imprimir', etiquetaAtajo('Ctrl+Enter'));
    zonaErrores.append(h('div', { class: 'aviso-caja caja-confirmar', role: 'alertdialog', 'aria-label': 'Confirmar emisión' },
      h('strong', {}, `Vas a emitir la nota Nº ${proximo} de ${sucursal?.nombre}. `), 'Después no se puede modificar.',
      validacion.avisos.length ? h('ul', { class: 'lista-mensajes' }, validacion.avisos.map((a) => h('li', { class: 'aviso' }, a))) : null,
      h('div', { class: 'barra-botones' }, confirmarBoton,
        h('button', { type: 'button', class: 'boton', onclick: () => zonaErrores.replaceChildren() }, 'Seguir editando'))));
    confirmando = true;
    confirmarBoton.focus();
    zonaErrores.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  let confirmando = false;
  async function emitirDeVerdad(resultados) {
    confirmando = false;
    // Se guarda una "foto" de lo calculado, para que la nota impresa no cambie si mañana cambia la tabla de códigos.
    nota.renglones = nota.renglones.map((renglon, i) => ({ ...renglon, calculado: fotoDelCalculo(renglon, resultados[i], datos.config) }));
    delete nota.piezaEnCurso;
    try {
      await almacenamiento.guardarBorrador(nota);
      const emitida = await almacenamiento.emitirNota(nota, datos.sucursales);
      hayCambios = false;
      mostrarAviso(`Nota emitida: NP Nº ${emitida.numero}`, 'ok', 3);
      // "Emitir e imprimir": la hoja se abre y la ventana de impresión aparece sola.
      ir(`#imprimir/${emitida.id}/imprimir`);
    } catch (error) {
      mostrarAviso(`No se pudo emitir: ${error.message}`, 'error', 8);
    }
  }

  // ---------- armado de la pantalla ----------

  const sucursal = sucursalActual();
  contenedor.replaceChildren(
    h('div', { class: 'titulo-pantalla' },
      h('h1', {}, 'Nota de pedido'),
      h('span', { class: 'texto-chico' }, sucursal ? `Trabajando hoy en ${sucursal.nombre} · el número se asigna al emitir` : '')),
    zonaRecuperar,
    encabezado,
    h('section', { class: 'panel' },
      h('div', { class: 'titulo-seccion' }, h('h2', {}, 'Piezas'), ayuda(datos.glosario, 'desarrollo'), totalTiempo),
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
    { teclas: 'Ctrl+Enter', descripcion: 'Emitir nota (dos veces: la segunda confirma)', accion: () => {
      if (asistenteAbierto) return;
      const boton = zonaErrores.querySelector('.caja-confirmar .principal');
      if (confirmando && boton) boton.click(); else emitir();
    } },
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
