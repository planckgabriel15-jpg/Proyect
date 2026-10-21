// =============================================================
// panelesPieza.js
// Paneles del paso 2 (y del editor 3D) para lo que va SOBRE la pieza:
//   - tapas de la canaleta (tipo, pestaña de apoyo, tapa a medida);
//   - boquetas (tipo, forma, medidas, en el fondo o en una tapa);
//   - cortes en las caras (con pared opcional);
//   - empalme (tramos de chapa cuando la pieza es más larga que la chapa).
//
// Cada panel recibe un "contexto":
//   { datos, renglon: () => borrador, alCambiar: (redibujar: boolean) => void }
// alCambiar(false) = cambió un valor (se recalcula todo, el panel queda igual);
// alCambiar(true)  = cambió algo que pide otros campos (el panel se vuelve a armar).
// =============================================================

import { h, selector, enterPasaAlSiguiente } from './util.js';
import { etiquetaAtajo } from './atajos.js';
import { crearEditorTramos } from './editorTramos.js';
import { leerNumero, formatearNumero, formatearCorto } from '../logica/numeros.js';
import { calcularGeometria } from '../logica/geometria.js';
import { copiarPerfil } from '../logica/perfil.js';
import {
  FORMAS_BOQUETA, TIPOS_BOQUETA, UBICACIONES_BOQUETA, normalizarBoqueta, medidasDeTapa, cambiarMedidasTapa,
  perfilDeLaPunta, tipoDeTapa, tapaEntra,
} from '../logica/accesoriosCanaleta.js';
import { FORMAS_CORTE, LADOS_PARED, crearCorte } from '../logica/cortes.js';
import { tramosDeChapa, ajustarTramoDeChapa, necesitaEmpalme, cantidadMinimaDeTramos } from '../logica/empalme.js';
import { svgTapa } from '../vistas2d/carasSvg.js';

const texto = (v) => (v === null || v === undefined ? '' : String(v).replace('.', ','));
const numeroOTexto = (valor) => {
  const n = leerNumero(valor);
  return Number.isFinite(n) ? n : valor;
};

/** Campo numérico que se aplica mientras se escribe. */
export function campoNumero(etiqueta, valor, alEscribir, atributos = {}) {
  return h('label', { class: 'campo-parametro' }, h('span', {}, etiqueta),
    h('input', {
      type: 'text', inputmode: 'decimal', class: 'campo-medida', value: texto(valor), ...atributos,
      oninput: (e) => alEscribir(numeroOTexto(e.target.value)),
    }));
}

/** Lista desplegable con un texto arriba. */
function campoOpciones(etiqueta, opciones, valor, alElegir) {
  return h('label', { class: 'campo-parametro' }, h('span', {}, etiqueta),
    selector(opciones, valor, { onchange: (e) => alElegir(e.target.value) }));
}

// -------------------------------------------------------------
// Boquetas
// -------------------------------------------------------------

/**
 * Campos de una boqueta (sirven en el paso 2 y en el editor 3D).
 * @returns {HTMLElement[]}
 */
export function camposDeBoqueta(ctx, indice, { conQuitar = true } = {}) {
  const renglon = ctx.renglon();
  const original = renglon.accesorios.boquetas[indice];
  // Se completan los datos que falten (boquetas guardadas antes de que hubiera tipos).
  Object.assign(original, normalizarBoqueta(original, ctx.datos.config));
  const b = original;
  const valor = (campo, redibujar = false) => (v) => { b[campo] = v; ctx.alCambiar(redibujar); };
  const campos = [
    campoOpciones('Tipo', TIPOS_BOQUETA.map((t) => ({ valor: t.valor, texto: t.texto })), b.tipo, valor('tipo', true)),
  ];
  if (b.tipo === 'boqueta') {
    campos.push(campoOpciones('Forma', FORMAS_BOQUETA.map((f) => ({ valor: f, texto: f })), b.forma, valor('forma', true)));
    if (b.forma === 'redonda') campos.push(campoNumero('Diámetro (cm)', b.diametroCm, valor('diametroCm')));
    else if (b.forma === 'cuadrada') campos.push(campoNumero('Lado (cm)', b.ladoACm, valor('ladoACm')));
    else campos.push(campoNumero('Lado a (cm)', b.ladoACm, valor('ladoACm')), campoNumero('Lado b (cm)', b.ladoBCm, valor('ladoBCm')));
    campos.push(campoNumero('Largo de la boca (cm)', b.largoBocaCm, valor('largoBocaCm')));
  } else if (b.tipo === 'tronera') {
    campos.push(
      campoNumero('Boca a (cm)', b.bocaACm, valor('bocaACm')), campoNumero('Boca b (cm)', b.bocaBCm, valor('bocaBCm')),
      campoNumero('Salida Ø (cm)', b.diametroSalidaCm, valor('diametroSalidaCm')), campoNumero('Alto (cm)', b.altoCm, valor('altoCm')));
  } else {
    campos.push(campoNumero('Corte en la chapa: a (cm)', b.ladoACm, valor('ladoACm')), campoNumero('b (cm)', b.ladoBCm, valor('ladoBCm')));
  }
  // En una tapa solo si la canaleta tiene esa tapa (o si ya estaba elegida).
  const ubicaciones = UBICACIONES_BOQUETA.filter((u) => u.valor === 'fondo' || u.valor === b.ubicacion
    || tipoDeTapa(renglon.accesorios, u.valor === 'tapaIzquierda' ? 'izquierda' : 'derecha') !== 'ninguna');
  campos.push(campoOpciones('Dónde va', ubicaciones, b.ubicacion, valor('ubicacion', true)));
  if (b.ubicacion === 'fondo') {
    campos.push(campoNumero('Posición desde la punta izq. (cm)', b.posicionCm, valor('posicionCm')));
  } else {
    campos.push(
      campoNumero('Altura del centro sobre el fondo (cm)', b.alturaCm, valor('alturaCm')),
      campoNumero('Corrimiento desde el medio (cm, + derecha)', b.desplazamientoCm, valor('desplazamientoCm')));
  }
  if (conQuitar) {
    campos.push(h('button', {
      type: 'button', class: 'boton chico peligro',
      onclick: () => { renglon.accesorios.boquetas.splice(indice, 1); ctx.alCambiar(true); },
    }, 'Quitar'));
  }
  return campos;
}

// -------------------------------------------------------------
// Tapas
// -------------------------------------------------------------

/**
 * Campos de una tapa: tipo, pestaña de apoyo y "a medida" (con su propio perfil).
 * @returns {HTMLElement}
 */
export function camposDeTapa(ctx, lado) {
  const renglon = ctx.renglon();
  const { config } = ctx.datos;
  const acc = renglon.accesorios;
  const tipo = tipoDeTapa(acc, lado);
  const medidas = medidasDeTapa(acc, lado, config);
  const campoTipo = lado === 'izquierda' ? 'tapaIzquierda' : 'tapaDerecha';
  const cambiarMedidas = (cambios, redibujar) => {
    Object.assign(renglon.accesorios, cambiarMedidasTapa(renglon.accesorios, lado, cambios));
    ctx.alCambiar(redibujar);
  };

  const zona = h('div', { class: 'campos-tapa' },
    h('div', { class: 'fila-campos' },
      campoOpciones(`Tapa ${lado}`, config.accesoriosCanaleta.tiposDeTapa.map((t) => ({ valor: t, texto: t })), tipo, (v) => { acc[campoTipo] = v; ctx.alCambiar(true); }),
      tipo === 'ninguna' ? null : campoNumero('Pestaña de apoyo (cm)', medidas.pestanaCm, (v) => cambiarMedidas({ pestanaCm: v }, false)),
      tipo === 'ninguna' ? null : h('label', { class: 'casilla' },
        h('input', {
          type: 'checkbox', checked: medidas.aMedida,
          onchange: (e) => cambiarMedidas(e.target.checked
            ? { aMedida: true, perfil: medidas.perfil?.tramos?.length ? medidas.perfil : copiarPerfil(perfilDeLaPunta(renglon, lado)) }
            : { aMedida: false }, true),
        }), ' Tapa a medida (otra forma, tiene que entrar en la canaleta)')));

  if (tipo !== 'ninguna' && medidas.aMedida) {
    const vista = h('div', { class: 'vista-tapa' });
    const aviso = h('p', { class: 'texto-chico', 'aria-live': 'polite' });
    const dibujar = () => {
      vista.innerHTML = svgTapa(ctx.renglon(), lado, config);
      const revision = tapaEntra(ctx.renglon(), lado, config);
      aviso.textContent = revision.entra ? 'La tapa entra en la canaleta.' : revision.mensaje;
      aviso.classList.toggle('error-texto', !revision.entra);
    };
    const editor = crearEditorTramos({
      perfil: medidas.perfil,
      datos: ctx.datos,
      compacto: true,
      alCambiar: (perfil) => {
        Object.assign(renglon.accesorios, cambiarMedidasTapa(renglon.accesorios, lado, { perfil }));
        ctx.alCambiar(false);
        dibujar();
      },
      alResaltar: () => {},
      alDibujarAMano: () => {},
    });
    zona.append(h('div', { class: 'tapa-a-medida' },
      h('div', {}, h('p', { class: 'texto-chico' }, `Medidas de la tapa ${lado} (se apoya en el fondo de la canaleta):`), editor.elemento,
        h('button', {
          type: 'button', class: 'boton chico',
          onclick: () => cambiarMedidas({ perfil: copiarPerfil(perfilDeLaPunta(ctx.renglon(), lado)) }, true),
        }, 'Volver a la forma de la canaleta')),
      h('div', {}, vista, aviso)));
    dibujar();
  }
  return zona;
}

/** Panel completo de tapas y boquetas de la canaleta. */
export function seccionAccesorios(ctx, { agregarBoqueta }) {
  const renglon = ctx.renglon();
  const zona = h('section', { class: 'panel-accesorios', 'data-seccion': 'accesorios' }, h('h3', {}, 'Tapas y boquetas de la canaleta'));
  zona.append(camposDeTapa(ctx, 'izquierda'), camposDeTapa(ctx, 'derecha'));
  renglon.accesorios.boquetas.forEach((_, i) => {
    zona.append(h('div', { class: 'fila-campos fila-boqueta' }, h('strong', { class: 'numero-boqueta' }, `Boqueta ${i + 1}`), camposDeBoqueta(ctx, i)));
  });
  zona.append(h('button', { type: 'button', class: 'boton', onclick: () => agregarBoqueta() }, 'Agregar boqueta', etiquetaAtajo('Alt+Q')),
    h('p', { class: 'texto-chico' }, 'Boqueta, tronera o colector, en el fondo o en una tapa. Donde va la boqueta la chapa queda cortada. La posición se mide desde la punta izquierda hasta el centro.'));
  enterPasaAlSiguiente(zona);
  return zona;
}

// -------------------------------------------------------------
// Cortes
// -------------------------------------------------------------

/** Campos de un corte (sirven en el paso 2 y en el editor 3D). */
export function camposDeCorte(ctx, indice, { conQuitar = true } = {}) {
  const renglon = ctx.renglon();
  const corte = renglon.cortes[indice];
  const valor = (campo, redibujar = false) => (v) => { corte[campo] = v; ctx.alCambiar(redibujar); };
  const caras = calcularGeometria(renglon.perfil, ctx.datos.config).segmentos.map((s) => ({
    valor: s.indice, texto: `Cara ${s.indice + 1} (${formatearCorto(Math.hypot(s.fin.x - s.inicio.x, s.fin.y - s.inicio.y))} cm)`,
  }));
  const campos = [
    campoOpciones('En la cara', caras, corte.tramo, (v) => { corte.tramo = Number(v); corte.centroCm = null; ctx.alCambiar(true); }),
    campoOpciones('Forma', FORMAS_CORTE.map((f) => ({ valor: f, texto: f })), corte.forma, valor('forma', true)),
  ];
  if (corte.forma === 'redonda') campos.push(campoNumero('Diámetro (cm)', corte.diametroCm, valor('diametroCm')));
  else if (corte.forma === 'cuadrada') campos.push(campoNumero('Lado (cm)', corte.ladoACm, valor('ladoACm')));
  else campos.push(campoNumero('Lado a, a lo ancho de la cara (cm)', corte.ladoACm, valor('ladoACm')), campoNumero('Lado b, a lo largo (cm)', corte.ladoBCm, valor('ladoBCm')));
  campos.push(
    campoNumero('Posición desde la punta izq. (cm)', corte.posicionCm, valor('posicionCm')),
    campoNumero('Centro desde el comienzo de la cara (cm, vacío = al medio)', corte.centroCm, (v) => { corte.centroCm = v === '' ? null : v; ctx.alCambiar(false); }),
    campoNumero('Pared alrededor: alto (cm, 0 = sin pared)', corte.paredAlturaCm, valor('paredAlturaCm')),
    campoOpciones('La pared va', LADOS_PARED, corte.paredLado, valor('paredLado')));
  if (conQuitar) {
    campos.push(h('button', {
      type: 'button', class: 'boton chico peligro',
      onclick: () => { renglon.cortes.splice(indice, 1); ctx.alCambiar(true); },
    }, 'Quitar'));
  }
  return campos;
}

/** Panel de cortes en la chapa (cualquier plegado). */
export function seccionCortes(ctx, { agregarCorte }) {
  const renglon = ctx.renglon();
  renglon.cortes = renglon.cortes || [];
  const zona = h('section', { class: 'panel-cortes', 'data-seccion': 'cortes' }, h('h3', {}, 'Cortes en la chapa'));
  renglon.cortes.forEach((_, i) => {
    zona.append(h('div', { class: 'fila-campos fila-boqueta' }, h('strong', { class: 'numero-boqueta' }, `Corte ${i + 1}`), camposDeCorte(ctx, i)));
  });
  zona.append(h('button', { type: 'button', class: 'boton', onclick: () => agregarCorte() }, 'Agregar corte', etiquetaAtajo('Alt+R')),
    h('p', { class: 'texto-chico' }, 'Agujero redondo, cuadrado o rectangular en cualquier cara (por ejemplo, para una boqueta que el cliente ya tiene). Puede llevar una pared o aletas alrededor.'));
  enterPasaAlSiguiente(zona);
  return zona;
}

/** Corte nuevo (lo usan el botón y el atajo). */
export function agregarCorteA(renglon, config) {
  renglon.cortes = renglon.cortes || [];
  renglon.cortes.push(crearCorte(renglon, config));
  return renglon.cortes.length - 1;
}

// -------------------------------------------------------------
// Empalme
// -------------------------------------------------------------

/**
 * Panel del empalme: solo aparece si la pieza es más larga que la chapa (o si ya se pidió dividirla).
 * @returns {HTMLElement|null}
 */
export function seccionEmpalme(ctx) {
  const renglon = ctx.renglon();
  const { config } = ctx.datos;
  const modo = renglon.empalme?.modo;
  if (renglon.usaLargo === false || renglon.tipoPieza !== 'plegada') return null;
  if (!necesitaEmpalme(renglon, config) && modo !== 'manual' && modo !== 'iguales') return null;
  const largo = leerNumero(renglon.largoCm);
  const maximo = config.largoMaximoChapaCm;
  const tramos = tramosDeChapa(renglon, config);
  const minimo = cantidadMinimaDeTramos(largo, maximo, config.empalme?.solapeCm ?? 0);
  const poner = (empalme) => { renglon.empalme = empalme; ctx.alCambiar(true); };

  const zona = h('section', { class: 'panel-empalme', 'data-seccion': 'empalme' },
    h('h3', {}, 'Empalme: tramos de chapa'),
    h('p', { class: 'texto-chico' }, `La pieza mide ${formatearNumero(largo / 100, 2)} m y la chapa ${formatearNumero(maximo / 100, 2)} m. Se arma con ${tramos.length} tramos (cambiá cualquiera: el último se ajusta solo).`));
  const fila = h('div', { class: 'fila-campos' });
  tramos.forEach((t, i) => {
    fila.append(h('label', { class: 'campo-parametro' }, h('span', {}, `Tramo ${i + 1} (m)`),
      h('input', {
        type: 'text', inputmode: 'decimal', class: 'campo-medida', value: formatearNumero(t / 100, 2),
        onchange: (e) => {
          const metros = leerNumero(e.target.value);
          if (!(metros > 0)) return;
          poner({ modo: 'manual', tramosCm: ajustarTramoDeChapa(tramos, i, Math.round(metros * 10000) / 100, largo, config.empalme?.solapeCm ?? 0) });
        },
      })));
  });
  zona.append(fila, h('div', { class: 'barra-botones' },
    h('button', { type: 'button', class: `boton chico${!modo || modo === 'automatico' ? ' elegido' : ''}`, onclick: () => poner({ modo: 'automatico' }) }, `Automático (${formatearNumero(maximo / 100, 2)} + resto)`),
    h('button', { type: 'button', class: `boton chico${modo === 'iguales' ? ' elegido' : ''}`, onclick: () => poner({ modo: 'iguales', cantidad: tramos.length }) }, 'Partes iguales'),
    h('button', { type: 'button', class: 'boton chico', onclick: () => poner({ modo: 'iguales', cantidad: tramos.length + 1 }) }, 'Un tramo más'),
    h('button', { type: 'button', class: 'boton chico', disabled: tramos.length <= Math.max(minimo, 1), onclick: () => poner({ modo: 'iguales', cantidad: tramos.length - 1 }) }, 'Un tramo menos')));
  enterPasaAlSiguiente(zona);
  return zona;
}
