// =============================================================
// medir-flujo.mjs
// Herramienta de DESARROLLO (no la usa el programa): recorre en un navegador
// automático los 3 casos del diagnóstico (docs/DIAGNOSTICO.md) y cuenta lo que
// tiene que hacer el vendedor: clics, opciones elegidas, campos escritos,
// teclas, decisiones y pantallas. Con eso estima el tiempo con el modelo KLM
// (Card, Moran y Newell, 1980): ver la tabla TIEMPOS de abajo.
//
// Necesita Playwright (no es dependencia del programa) y el programa servido:
//   python -m http.server 8765        (en la carpeta notas-de-pedido)
//   node herramientas/medir-flujo.mjs antes|despues [carpeta-de-three-local]
//
// "antes" = el flujo del asistente de 3 pasos tal como estaba al hacer el
// diagnóstico; "despues" = el flujo rediseñado (nota rápida).
// =============================================================
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const MODO = process.argv[2] || 'despues';
const THREE_LOCAL = process.argv[3] || null;
const BASE = process.env.BASE || 'http://127.0.0.1:8765/';

// Operadores del modelo KLM, en segundos (Card, Moran y Newell, 1980; Kieras, 2001).
export const TIEMPOS = {
  M: 1.35, // preparación mental antes de cada acción
  P: 1.1,  // apuntar con el mouse
  B: 0.2,  // apretar y soltar el botón
  H: 0.4,  // pasar la mano del mouse al teclado o al revés
  K: 0.28, // una tecla (persona que no es mecanógrafa)
  R: 1.5,  // SUPUESTO: orientarse al cambiar de pantalla
};

class Medidor {
  constructor(pagina) {
    this.p = pagina;
    this.acciones = [];
    this.pantallas = [];
  }

  pantalla(nombre) { if (this.pantallas[this.pantallas.length - 1] !== nombre) this.pantallas.push(nombre); }

  async clic(selector, { decision = false, espera = 250 } = {}) {
    await this.p.locator(selector).first().click();
    this.acciones.push({ tipo: 'clic', decision });
    await this.p.waitForTimeout(espera);
  }

  /** Elegir de una lista desplegable: abrir (apuntar + clic) y elegir (apuntar + clic). */
  async opcion(selector, valor) {
    await this.p.locator(selector).first().selectOption(valor);
    this.acciones.push({ tipo: 'opcion', decision: true });
    await this.p.waitForTimeout(200);
  }

  async campo(selector, texto) {
    const campo = this.p.locator(selector).first();
    await campo.fill(texto);
    this.acciones.push({ tipo: 'campo', teclas: texto.length, decision: false });
    await this.p.waitForTimeout(150);
  }

  /** Atajo de teclado o Enter (no hace falta apuntar). */
  async tecla(tecla) {
    await this.p.keyboard.press(tecla);
    this.acciones.push({ tipo: 'tecla', decision: false });
    await this.p.waitForTimeout(250);
  }

  resumen() {
    const cuenta = (tipo) => this.acciones.filter((a) => a.tipo === tipo).length;
    const teclas = this.acciones.reduce((s, a) => s + (a.teclas || 0), 0);
    const T = TIEMPOS;
    let segundos = (this.pantallas.length) * T.R;
    for (const a of this.acciones) {
      if (a.tipo === 'clic') segundos += T.M + T.P + T.B;
      if (a.tipo === 'opcion') segundos += T.M + 2 * (T.P + T.B);
      if (a.tipo === 'campo') segundos += T.M + T.P + T.B + 2 * T.H + a.teclas * T.K;
      if (a.tipo === 'tecla') segundos += T.M + T.K;
    }
    return {
      clics: cuenta('clic'),
      opciones: cuenta('opcion'),
      campos: cuenta('campo'),
      teclas,
      atajos: cuenta('tecla'),
      decisiones: this.acciones.filter((a) => a.decision).length,
      pantallas: this.pantallas.length,
      listaPantallas: this.pantallas.join(' → '),
      segundos: Math.round(segundos),
    };
  }
}

// ---------- pasos comunes ----------

async function ingresarAntes(m) {
  m.pantalla('ingreso');
  await m.opcion('select[aria-label="Vendedor"]', 'v01');
  await m.clic('.rol-ingreso >> nth=0 >> button');
  m.pantalla('inicio');
  await m.clic('text=Nueva nota de pedido', { espera: 500 });
  m.pantalla('nota');
  await m.campo('input[placeholder="Nombre del cliente"]', 'Constructora Sur');
  await m.campo('input[placeholder="Pegá el número de factura"]', 'A-0001-00012345');
}

async function emitirEImprimir(m) {
  m.pantalla('nota');
  await m.clic('button:has-text("Emitir nota")', { espera: 1500 }); // + el cartel "¿Emitir?" (se acepta solo)
  m.acciones.push({ tipo: 'clic', decision: true }); // Aceptar del cartel de confirmación
  m.pantalla('confirmación');
  m.pantalla('impresión');
  await m.clic('button:has-text("Imprimir / Guardar PDF")');
}

// ---------- flujo "antes": asistente de 3 pasos ----------

const ANTES = {
  'Caso 1: canaleta con tapas y boqueta': async (m) => {
    await ingresarAntes(m);
    await m.clic('button:has-text("Agregar pieza")', { espera: 500 });
    m.pantalla('asistente 1: ¿qué pieza?');
    await m.clic('.tarjeta-plantilla:has-text("Canaleta (ejemplo de nota real)")', { decision: true, espera: 900 });
    m.pantalla('asistente 2: medidas y dibujo');
    await m.opcion('.panel-accesorios .campos-tapa >> nth=0 >> select', 'soldada');
    await m.opcion('.panel-accesorios .campos-tapa >> nth=1 >> select', 'engrampada');
    await m.clic('button:has-text("Agregar boqueta")');
    await m.opcion('.panel-accesorios .fila-boqueta label:has-text("Forma") select', 'rectangular');
    await m.campo('.panel-accesorios .fila-boqueta label:has-text("Lado a") input', '10');
    await m.campo('.panel-accesorios .fila-boqueta label:has-text("Lado b") input', '5');
    await m.campo('.panel-accesorios .fila-boqueta label:has-text("Posición") input', '60');
    await m.clic('button:has-text("Siguiente")', { espera: 500 });
    m.pantalla('asistente 3: material y cantidad');
    await m.opcion('.formulario-material label:has-text("Terminación") select', 'P');
    await m.clic('.muestra-color:has-text("negro")', { decision: true });
    await m.clic('button:has-text("Agregar a la nota")', { espera: 900 });
    await emitirEImprimir(m);
  },
  'Caso 2: babeta a medida con corte láser': async (m) => {
    await ingresarAntes(m);
    await m.clic('button:has-text("Agregar pieza")', { espera: 500 });
    m.pantalla('asistente 1: ¿qué pieza?');
    await m.campo('input[aria-label="Buscar pieza"]', 'babeta');
    await m.clic('.tarjeta-plantilla:has-text("Babeta 15×15")', { decision: true, espera: 900 });
    m.pantalla('asistente 2: medidas y dibujo');
    await m.campo('input[aria-label="Largo de la pieza en metros"]', '3');
    await m.campo('input[aria-label="Medida del tramo 1 en cm"]', '12');
    await m.campo('input[aria-label="Medida del tramo 2 en cm"]', '18');
    await m.opcion('select[aria-label="Corte láser del tramo 2"]', 'sinusoidal');
    await m.clic('button:has-text("Siguiente")', { espera: 500 });
    m.pantalla('asistente 3: material y cantidad');
    await m.opcion('.formulario-material label:has-text("Terminación") select', 'P');
    await m.clic('.muestra-color:has-text("negro")', { decision: true });
    await m.campo('.formulario-material label:has-text("Cantidad") input', '4');
    await m.clic('button:has-text("Agregar a la nota")', { espera: 900 });
    await emitirEImprimir(m);
  },
  'Caso 3: artículo de reventa sin dibujo': async (m) => {
    await ingresarAntes(m);
    await m.clic('button:has-text("Agregar pieza")', { espera: 500 });
    m.pantalla('asistente 1: ¿qué pieza?');
    await m.campo('input[aria-label="Buscar pieza"]', 'rejilla');
    await m.clic('.tarjeta-plantilla:has-text("Rejilla de ventilación")', { decision: true, espera: 900 });
    m.pantalla('asistente 2: medidas y dibujo');
    await m.opcion('.formulario-parametros select', '15x30');
    await m.clic('button:has-text("Siguiente")', { espera: 500 });
    m.pantalla('asistente 3: material y cantidad');
    await m.campo('.formulario-material label:has-text("Cantidad") input', '2');
    await m.clic('button:has-text("Agregar a la nota")', { espera: 900 });
    await emitirEImprimir(m);
  },
};

// ---------- flujo "después": se completa en la etapa D ----------
export const DESPUES = {};

async function medir(flujos) {
  const navegador = await chromium.launch({ args: ['--enable-unsafe-swiftshader', '--use-angle=swiftshader'] });
  const resultados = {};
  for (const [nombre, flujo] of Object.entries(flujos)) {
    const contexto = await navegador.newContext({ viewport: { width: 1366, height: 860 } });
    if (THREE_LOCAL) {
      await contexto.route('https://cdn.jsdelivr.net/npm/three@0.170.0/**', (r) => r.fulfill({
        path: r.request().url().replace('https://cdn.jsdelivr.net/npm/three@0.170.0/', `${THREE_LOCAL}/`), contentType: 'application/javascript',
      }));
    }
    const pagina = await contexto.newPage();
    pagina.on('dialog', (d) => d.accept());
    await pagina.emulateMedia({ media: 'screen' });
    await pagina.addInitScript(() => { window.print = () => {}; });
    await pagina.goto(BASE);
    await pagina.waitForTimeout(600);
    const m = new Medidor(pagina);
    try {
      await flujo(m);
      resultados[nombre] = m.resumen();
    } catch (error) {
      resultados[nombre] = { error: error.message.split('\n')[0], hasta: m.resumen() };
    }
    await contexto.close();
  }
  await navegador.close();
  return resultados;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const { DESPUES: flujosDespues } = MODO === 'despues' ? await import('./medir-flujo-despues.mjs').catch(() => ({ DESPUES })) : { DESPUES };
  const resultados = await medir(MODO === 'antes' ? ANTES : flujosDespues);
  console.log(JSON.stringify(resultados, null, 1));
}

export { Medidor, medir, emitirEImprimir };
