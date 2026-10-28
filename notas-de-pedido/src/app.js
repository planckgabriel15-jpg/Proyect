// =============================================================
// app.js
// Arranque del programa y "router": según lo que va después de # en la
// dirección se muestra una pantalla u otra.
//   #inicio · #ingreso · #nota/<id> · #nota/nueva · #imprimir/<id>
//   #produccion[/<pestaña>] · #operario[/<id>] · #hoja-ruta/<operario|lote>/<id>/<día>
//   #configuracion
// Roles (sesión): comercial (carga notas), jefe de producción y operario.
// =============================================================

import { h } from './pantallas/util.js';
import { estado, vendedorActual, sucursalActual } from './pantallas/estado.js';
import * as almacenamiento from './datos/almacenamiento.js';
import { pantallaInicio, pantallaIngreso } from './pantallas/inicio.js';
import { pantallaNota } from './pantallas/nota.js';
import { pantallaImpresion } from './pantallas/impresion.js';
import { pantallaProduccion } from './pantallas/produccion.js';
import { pantallaConfiguracion } from './pantallas/configuracion.js';
import { pantallaOperario } from './pantallas/operario.js';
import { pantallaHojaRuta } from './pantallas/hojaRuta.js';
import { mostrarAyudaAtajos } from './pantallas/atajos.js';

const principal = document.getElementById('principal');
const menu = document.getElementById('menu');
let limpiarPantallaAnterior = () => {};

const NOMBRES_ROL = { comercial: 'Comercial', jefe: 'Jefe de producción', operario: 'Operario' };

function quienEsta() {
  const rol = estado.sesion?.rol;
  if (rol === 'jefe') return NOMBRES_ROL.jefe;
  if (rol === 'operario') return estado.datos.produccion.operarios.find((o) => o.id === estado.sesion.operarioId)?.nombre || 'Operario';
  const vendedor = vendedorActual();
  return vendedor ? `${vendedor.nombre} · ${sucursalActual()?.nombre || ''}` : '';
}

function dibujarMenu(rutaActual) {
  const rol = estado.sesion?.rol;
  const enlace = (ruta, texto) => h('a', { href: ruta, class: rutaActual === ruta ? 'activo' : '' }, texto);
  const marca = estado.datos.config.marca || {};
  let enlaces = [enlace('#inicio', 'Inicio'), enlace('#produccion', 'Producción'), enlace('#configuracion', 'Configuración')];
  if (rol === 'jefe') enlaces = [enlace('#produccion', 'Producción'), enlace('#operario', 'Vista operario'), enlace('#configuracion', 'Configuración')];
  if (rol === 'operario') enlaces = [enlace('#operario', 'Mis trabajos')];
  menu.replaceChildren(
    h('a', { href: '#inicio', class: 'marca' },
      marca.logo ? h('img', { class: 'logo-menu', src: marca.logo, alt: marca.nombre || 'Logo' }) : null,
      h('span', { class: 'marca-texto' }, 'Notas de pedido')),
    h('nav', { 'aria-label': 'Menú' }, enlaces),
    h('span', { class: 'quien' }, quienEsta(), ' ', h('a', { href: '#ingreso', class: 'enlace-chico' }, rol ? 'cambiar' : 'ingresar')),
    h('button', { type: 'button', class: 'boton-menu', onclick: () => mostrarAyudaAtajos(), title: 'Ver atajos de teclado (F1)' }, 'Atajos (F1)'));
}

/** Colores de la empresa (datos/config.json → marca) aplicados a toda la pantalla. */
function aplicarColoresDeMarca(marca) {
  if (!marca) return;
  const raiz = document.documentElement.style;
  if (marca.colorPrincipal) raiz.setProperty('--principal', marca.colorPrincipal);
  if (marca.colorPrincipalOscuro) raiz.setProperty('--principal-oscuro', marca.colorPrincipalOscuro);
  if (marca.colorAcento) raiz.setProperty('--acento', marca.colorAcento);
  if (marca.nombre) document.title = `Notas de pedido – ${marca.nombre}`;
}

async function mostrarPantalla() {
  limpiarPantallaAnterior();
  limpiarPantallaAnterior = () => {};
  const [ruta, parametro, ...resto] = (window.location.hash || '#inicio').split('/');
  const rol = estado.sesion?.rol;

  // Cada rol a su lugar. Producción, impresión y configuración se pueden abrir sin ingresar
  // (como antes: el taller mira las notas emitidas), pero producción sin ser jefe es solo para mirar.
  const rutaComercial = ['#inicio', '#nota'].includes(ruta) || ruta === '';
  if (rutaComercial && rol === 'jefe') { window.location.hash = '#produccion'; return; }
  if ((rutaComercial || ruta === '#produccion') && rol === 'operario') { window.location.hash = '#operario'; return; }
  if (rutaComercial && !estado.sesion?.vendedorId) { window.location.hash = '#ingreso'; return; }
  if ((ruta === '#operario' || ruta === '#hoja-ruta') && rol !== 'jefe' && rol !== 'operario') { window.location.hash = '#ingreso'; return; }
  dibujarMenu(ruta);
  document.body.dataset.pantalla = ruta.slice(1) || 'inicio';
  principal.replaceChildren(h('p', { class: 'texto-chico' }, 'Cargando…'));
  window.scrollTo(0, 0);

  try {
    if (ruta === '#ingreso') limpiarPantallaAnterior = await pantallaIngreso(principal);
    else if (ruta === '#nota') limpiarPantallaAnterior = await pantallaNota(principal, parametro || 'nueva');
    else if (ruta === '#imprimir') limpiarPantallaAnterior = await pantallaImpresion(principal, parametro);
    else if (ruta === '#produccion') limpiarPantallaAnterior = await pantallaProduccion(principal, parametro);
    else if (ruta === '#operario') limpiarPantallaAnterior = await pantallaOperario(principal, parametro);
    else if (ruta === '#hoja-ruta') limpiarPantallaAnterior = await pantallaHojaRuta(principal, parametro, resto[0], resto[1]);
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
    // Notas guardadas con versiones anteriores: se completan una sola vez (ver almacenamiento.migrarDatos).
    await almacenamiento.migrarDatos(estado.datos);
    aplicarColoresDeMarca(estado.datos.config.marca);
  } catch (error) {
    principal.replaceChildren(h('div', { class: 'aviso-caja error-caja' },
      `No se pudieron cargar los datos: ${error.message}. ¿Abriste la página con un servidor? (ver README.md)`));
    return;
  }
  window.addEventListener('hashchange', mostrarPantalla);
  await mostrarPantalla();
}

arrancar();
