// =============================================================
// medir-flujo-despues.mjs
// Los MISMOS tres casos de docs/DIAGNOSTICO.md, con los mismos datos, recorridos en el
// programa rediseñado (ficha única de la pieza). Lo usa medir-flujo.mjs:
//   node herramientas/medir-flujo.mjs despues [carpeta-de-three-local]
//
// Los tres primeros arrancan de cero (vendedor que nunca usó el programa: nada recordado),
// igual que la medición "antes", para comparar en las mismas condiciones.
// Los dos últimos miden lo que el programa ahora recuerda: la segunda nota del día y
// "Repetir". No tienen equivalente "antes" (había que cargar todo de nuevo).
// =============================================================

async function ingresar(m) {
  m.pantalla('ingreso');
  await m.opcion('select[aria-label="Vendedor"]', 'v01');
  await m.clic('.rol-ingreso >> nth=0 >> button');
  m.pantalla('inicio');
}

async function notaNueva(m, cliente = 'Constructora Sur') {
  await m.clic('text=Nueva nota de pedido', { espera: 500 });
  m.pantalla('nota');
  await m.campo('input[placeholder="Nombre del cliente"]', cliente);
  await m.campo('input[placeholder="Pegá el número de factura"]', 'A-0001-00012345');
}

/** Emitir: el botón, la confirmación en la misma pantalla y la impresión, que se abre sola. */
async function emitirEImprimir(m) {
  m.pantalla('nota');
  await m.clic('button:has-text("Emitir nota")', { espera: 400 });
  await m.clic('button:has-text("Emitir e imprimir")', { decision: true, espera: 1500 });
  m.pantalla('impresión');
}

async function canaletaConTapasYBoqueta(m, { recordado = false } = {}) {
  await m.clic('button:has-text("Agregar pieza")', { espera: 500 });
  m.pantalla('asistente 1: ¿qué pieza?');
  await m.clic(`${recordado ? '.tarjetas-rapidas ' : ''}.tarjeta-plantilla:has-text("Canaleta (ejemplo de nota real)")`, { decision: true, espera: 900 });
  m.pantalla('asistente 2: la pieza');
  await m.clic('details[data-plegable="accesorios"] > summary');
  await m.clic('.botonera[aria-label="Tapa izquierda"] button:has-text("soldada")', { decision: true });
  await m.clic('.botonera[aria-label="Tapa derecha"] button:has-text("engrampada")', { decision: true });
  await m.clic('button:has-text("Agregar boqueta")');
  if (!recordado) {
    // La primera vez hay que decir cómo es la boqueta; después arranca como la última que se cargó.
    await m.opcion('.panel-accesorios .fila-boqueta label:has-text("Forma") select', 'rectangular');
    await m.campo('.panel-accesorios .fila-boqueta label:has-text("Lado a") input', '10');
    await m.campo('.panel-accesorios .fila-boqueta label:has-text("Lado b") input', '5');
  }
  await m.campo('.panel-accesorios .fila-boqueta label:has-text("Posición") input', '60');
  if (!recordado) {
    // La primera vez hay que elegir prepintada y negro; después arranca con el último material.
    await m.clic('.botonera[aria-label="Terminación"] button:has-text("Prepintada")', { decision: true });
    await m.clic('.muestra-color:has-text("negro")', { decision: true });
  }
  await m.clic('button:has-text("Agregar a la nota")', { espera: 900 });
}

export const DESPUES = {
  'Caso 1: canaleta con tapas y boqueta': async (m) => {
    await ingresar(m);
    await notaNueva(m);
    await canaletaConTapasYBoqueta(m);
    await emitirEImprimir(m);
  },
  'Caso 2: babeta a medida con corte láser': async (m) => {
    await ingresar(m);
    await notaNueva(m);
    await m.clic('button:has-text("Agregar pieza")', { espera: 500 });
    m.pantalla('asistente 1: ¿qué pieza?');
    await m.campo('input[aria-label="Buscar pieza"]', 'babeta');
    await m.clic('.tarjeta-plantilla:has-text("Babeta 15×15")', { decision: true, espera: 900 });
    m.pantalla('asistente 2: la pieza');
    await m.campo('input[aria-label="Largo de la pieza en metros"]', '3');
    await m.campo('input[aria-label="Cantidad"]', '4');
    await m.campo('input[aria-label="Medida del tramo 1 en cm"]', '12');
    await m.campo('input[aria-label="Medida del tramo 2 en cm"]', '18');
    // El corte láser se usa poco: su columna está en la tabla completa (un toque más en este caso).
    await m.clic('button:has-text("Ver todas las columnas")');
    await m.opcion('select[aria-label="Corte láser del tramo 2"]', 'sinusoidal');
    await m.clic('.botonera[aria-label="Terminación"] button:has-text("Prepintada")', { decision: true });
    await m.clic('.muestra-color:has-text("negro")', { decision: true });
    await m.clic('button:has-text("Agregar a la nota")', { espera: 900 });
    await emitirEImprimir(m);
  },
  'Caso 3: artículo de reventa sin dibujo': async (m) => {
    await ingresar(m);
    await notaNueva(m);
    await m.clic('button:has-text("Agregar pieza")', { espera: 500 });
    m.pantalla('asistente 1: ¿qué pieza?');
    await m.campo('input[aria-label="Buscar pieza"]', 'rejilla');
    await m.clic('.tarjeta-plantilla:has-text("Rejilla de ventilación")', { decision: true, espera: 900 });
    m.pantalla('asistente 2: la pieza');
    await m.opcion('.formulario-parametros select', '15x30');
    await m.campo('input[aria-label="Cantidad"]', '2');
    await m.clic('button:has-text("Agregar a la nota")', { espera: 900 });
    await emitirEImprimir(m);
  },

  // ---------- lo que el programa ahora recuerda (sin equivalente "antes") ----------
  'Caso 1, segunda nota del día (material, boqueta y pieza recordados)': async (m) => {
    // Preparación, sin contar: el vendedor ya hizo una nota igual.
    const preparacion = new m.constructor(m.p);
    await ingresar(preparacion);
    await notaNueva(preparacion);
    await canaletaConTapasYBoqueta(preparacion);
    await emitirEImprimir(preparacion);
    await m.p.goto(`${m.p.url().split('#')[0]}#inicio`);
    await m.p.waitForTimeout(600);
    // Lo que se mide: otra nota, para el mismo cliente (se elige de las sugerencias: se escriben 3 letras).
    m.pantalla('inicio');
    await m.clic('text=Nueva nota de pedido', { espera: 500 });
    m.pantalla('nota');
    await m.campo('input[placeholder="Nombre del cliente"]', 'Constructora Sur');
    m.acciones[m.acciones.length - 1].teclas = 3;
    m.acciones.push({ tipo: 'clic', decision: true }); // elegir la sugerencia
    await m.campo('input[placeholder="Pegá el número de factura"]', 'A-0001-00012346');
    await canaletaConTapasYBoqueta(m, { recordado: true });
    await emitirEImprimir(m);
  },
  'Caso 1 con "Repetir" (lo mismo que la vez pasada)': async (m) => {
    const preparacion = new m.constructor(m.p);
    await ingresar(preparacion);
    await notaNueva(preparacion);
    await canaletaConTapasYBoqueta(preparacion);
    await emitirEImprimir(preparacion);
    await m.p.goto(`${m.p.url().split('#')[0]}#inicio`);
    await m.p.waitForTimeout(600);
    m.pantalla('inicio');
    await m.clic('a:has-text("Repetir")', { decision: true, espera: 700 });
    m.pantalla('nota');
    await m.campo('input[placeholder="Pegá el número de factura"]', 'A-0001-00012346');
    await emitirEImprimir(m);
  },
};
