// =============================================================
// app.js
// Arranque del programa y "router": según lo que va después de # en la
// dirección se muestra una pantalla u otra.
//   #inicio · #ingreso · #nota/<id> · #nota/nueva · #imprimir/<id>
//   #produccion · #configuracion
// =============================================================

import { h } from './pantallas/util.js';
import { estado, vendedorActual, sucursalActual } from './pantallas/estado.js';
import * as almacenamiento from './datos/almacenamiento.js';
import { pantallaInicio, pantallaIngreso } from './pantallas/inicio.js';
import { pantallaNota } from './pantallas/nota.js';
import { pantallaImpresion } from './pantallas/impresion.js';
import { pantallaProduccion } from './pantallas/produccion.js';
import { pantallaConfiguracion } from './pantallas/configuracion.js';

const principal = document.getElementById('principal');
const menu = document.getElementById('menu');
let limpiarPantallaAnterior = () => {};

function dibujarMenu(rutaActual) {
  const vendedor = vendedorActual();
  const sucursal = sucursalActual();
  const enlace = (ruta, texto) => h('a', { href: ruta, class: rutaActual === ruta ? 'activo' : '' }, texto);
  menu.replaceChildren(
    h('a', { href: '#inicio', class: 'marca' }, 'Notas de pedido'),
    h('nav', { 'aria-label': 'Menú' },
      enlace('#inicio', 'Inicio'),
      enlace('#produccion', 'Producción'),
      enlace('#configuracion', 'Configuración')),
    h('span', { class: 'quien' }, vendedor ? `${vendedor.nombre} · ${sucursal?.nombre || ''}` : ''));
}

async function mostrarPantalla() {
  limpiarPantallaAnterior();
  limpiarPantallaAnterior = () => {};
  const [ruta, parametro] = (window.location.hash || '#inicio').split('/');

  // Sin vendedor elegido, primero el ingreso (salvo producción e impresión, que usa el taller).
  const necesitaVendedor = !['#produccion', '#imprimir', '#configuracion'].includes(ruta);
  if (necesitaVendedor && !estado.sesion?.vendedorId && ruta !== '#ingreso') {
    window.location.hash = '#ingreso';
    return;
  }
  dibujarMenu(ruta);
  document.body.dataset.pantalla = ruta.slice(1) || 'inicio';
  principal.replaceChildren(h('p', { class: 'texto-chico' }, 'Cargando…'));
  window.scrollTo(0, 0);

  try {
    if (ruta === '#ingreso') limpiarPantallaAnterior = await pantallaIngreso(principal);
    else if (ruta === '#nota') limpiarPantallaAnterior = await pantallaNota(principal, parametro || 'nueva');
    else if (ruta === '#imprimir') limpiarPantallaAnterior = await pantallaImpresion(principal, parametro);
    else if (ruta === '#produccion') limpiarPantallaAnterior = await pantallaProduccion(principal);
    else if (ruta === '#configuracion') limpiarPantallaAnterior = await pantallaConfiguracion(principal);
    else limpiarPantallaAnterior = await pantallaInicio(principal);
  } catch (error) {
    console.error(error);
    principal.replaceChildren(h('div', { class: 'aviso-caja error-caja' }, `Ocurrió un error: ${error.message}`), h('a', { href: '#inicio', class: 'boton' }, 'Volver al inicio'));
  }
}

async function arrancar() {
  try {
    estado.datos = await almacenamiento.cargarDatosBase();
    estado.sesion = await almacenamiento.leerSesion();
  } catch (error) {
    principal.replaceChildren(h('div', { class: 'aviso-caja error-caja' },
      `No se pudieron cargar los datos: ${error.message}. ¿Abriste la página con un servidor? (ver README.md)`));
    return;
  }
  window.addEventListener('hashchange', mostrarPantalla);
  await mostrarPantalla();
}

arrancar();
