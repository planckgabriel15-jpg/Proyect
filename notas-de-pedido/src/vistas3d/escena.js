// =============================================================
// escena.js
// Visor 3D interactivo: girar arrastrando, zoom con la rueda o pellizcando,
// botones de vista (inicial, frente, lateral, isométrica), resaltado de tramos
// y clic sobre un tramo (para sincronizar con la tabla).
//
// Cotas: arriba del dibujo hay una "capa" de etiquetas HTML que siguen a la
// pieza cuando se gira. Tocar una cota la convierte en un campo para escribir
// la medida nueva (Enter confirma, Esc cancela), como en un programa de CAD.
// Si dos etiquetas se pisan, se esconde la menos importante (vuelve a
// aparecer al acercarse con el zoom).
//
// Usa Three.js + OrbitControls (cargados desde el CDN, ver index.html).
// =============================================================

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { construirModelo } from './modelo.js';
import { construirCotas } from './cotas3d.js';
import { COLOR_RESALTADO } from './materiales3d.js';
import { encuadrar, encuadrarOrtografica, DIRECCIONES_VISTA } from './encuadre.js';

/**
 * @param {HTMLElement} contenedor
 * @param {{
 *   alPasarSobreTramo?: (i|null) => void,
 *   alTocarTramo?: (i) => void,
 *   alTocarAccesorio?: (clave) => void,     // 'tapa:izquierda', 'boqueta:0'…
 *   alTocarVacio?: () => void,
 *   alUsarCota?: (editar, valorEscrito?) => ({ok:boolean, mensaje?:string}|void),
 * }} opciones
 */
export function crearVisor3d(contenedor, opciones = {}) {
  // preserveDrawingBuffer: permite sacar una "foto" del dibujo para imprimir.
  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true, logarithmicDepthBuffer: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.domElement.classList.add('lienzo-3d');
  contenedor.append(renderer.domElement);

  // Capa de etiquetas (cotas) encima del dibujo.
  const capa = document.createElement('div');
  capa.className = 'capa-cotas';
  const ficha = document.createElement('div');
  ficha.className = 'ficha-cotas';
  capa.append(ficha);
  contenedor.append(capa);

  const escena = new THREE.Scene();
  escena.background = new THREE.Color('#eef1f4');
  escena.add(new THREE.HemisphereLight(0xffffff, 0x8899aa, 1.6));
  const luz = new THREE.DirectionalLight(0xffffff, 1.6);
  luz.position.set(1, 2, 1.5);
  escena.add(luz);
  const luz2 = new THREE.DirectionalLight(0xffffff, 0.7);
  luz2.position.set(-1.5, -0.5, -1);
  escena.add(luz2);

  // Dos cámaras: con perspectiva (vistas 3D) y ortográfica (frente y lateral, como un plano).
  const camaraPerspectiva = new THREE.PerspectiveCamera(35, 1, 0.5, 50000);
  const camaraOrtografica = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 50000);
  let camara = camaraPerspectiva;
  const controles = new OrbitControls(camara, renderer.domElement);
  controles.enableDamping = true;

  let modelo = null;
  let cotas = null;           // lo que devuelve construirCotas
  let etiquetas = [];         // [{datos, elemento, ancho, alto}]
  let ultimo = null;          // { renglon, datos } para redibujar al prender o apagar las cotas
  let tramoResaltado = null;
  let accesorioResaltado = null;
  let ultimaVista = 'inicial';
  let encuadrado = false;
  let cotasVisibles = true;
  let modoEdicion = false;
  let edicionAbierta = null;  // la etiqueta que se está editando
  let redibujarAlCerrar = false;

  // ---- tamaño: se ajusta solo cuando cambia el contenedor ----
  function ajustarTamano() {
    const ancho = contenedor.clientWidth || 300;
    const alto = contenedor.clientHeight || 260;
    renderer.setSize(ancho, alto, false);
    camaraPerspectiva.aspect = ancho / alto;
    camaraPerspectiva.updateProjectionMatrix();
    // La ortográfica conserva el alto que se ve y ajusta el ancho.
    const medioAlto = (camaraOrtografica.top - camaraOrtografica.bottom) / 2;
    camaraOrtografica.left = -medioAlto * (ancho / alto);
    camaraOrtografica.right = medioAlto * (ancho / alto);
    camaraOrtografica.updateProjectionMatrix();
  }
  // Si cambia el tamaño (se abre el editor 3D, se gira el celular) y el vendedor no movió
  // la cámara, se vuelve a encuadrar para que la pieza entre entera.
  let camaraMovida = false;
  controles.addEventListener('start', () => { camaraMovida = true; });
  let ultimoTamano = '';
  const observador = new ResizeObserver(() => {
    ajustarTamano();
    const tamano = `${contenedor.clientWidth}x${contenedor.clientHeight}`;
    if (tamano !== ultimoTamano && modelo && !camaraMovida && contenedor.clientWidth > 0) vista(ultimaVista);
    ultimoTamano = tamano;
  });
  observador.observe(contenedor);
  ajustarTamano();

  // ---- bucle de dibujo ----
  let activo = true;
  function dibujar() {
    if (!activo) return;
    controles.update();
    acomodarCotasDelPerfil();
    renderer.render(escena, camara);
    ubicarEtiquetas();
    requestAnimationFrame(dibujar);
  }
  requestAnimationFrame(dibujar);

  // ---- elegir tramo, tapa o boqueta con el mouse o el dedo ----
  const rayo = new THREE.Raycaster();
  const puntero = new THREE.Vector2();
  function objetoBajoPuntero(evento) {
    if (!modelo) return null;
    const rect = renderer.domElement.getBoundingClientRect();
    puntero.x = ((evento.clientX - rect.left) / rect.width) * 2 - 1;
    puntero.y = -((evento.clientY - rect.top) / rect.height) * 2 + 1;
    rayo.setFromCamera(puntero, camara);
    const elegibles = modelo.children.filter((o) => !o.userData.esRegla);
    const tocado = rayo.intersectObjects(elegibles, true)
      .find((t) => t.object.isMesh && (t.object.userData.tramo !== undefined || t.object.userData.accesorio));
    if (!tocado) return null;
    const datos = tocado.object.userData;
    return datos.accesorio ? { accesorio: datos.accesorio } : { tramo: datos.tramo };
  }
  let inicioToque = null;
  renderer.domElement.addEventListener('pointerdown', (e) => { inicioToque = { x: e.clientX, y: e.clientY }; });
  renderer.domElement.addEventListener('pointerup', (e) => {
    // Si casi no se movió, fue un "clic" (no un giro).
    if (inicioToque && Math.hypot(e.clientX - inicioToque.x, e.clientY - inicioToque.y) < 6) {
      const tocado = objetoBajoPuntero(e);
      if (tocado?.accesorio) opciones.alTocarAccesorio?.(tocado.accesorio);
      else if (tocado) opciones.alTocarTramo?.(tocado.tramo);
      else opciones.alTocarVacio?.();
    }
    inicioToque = null;
  });
  renderer.domElement.addEventListener('pointermove', (e) => {
    if (e.buttons) return;
    const tocado = objetoBajoPuntero(e);
    renderer.domElement.style.cursor = tocado ? 'pointer' : '';
    if (opciones.alPasarSobreTramo) opciones.alPasarSobreTramo(tocado && !tocado.accesorio ? tocado.tramo : null);
  });

  // ---- vistas ----

  /**
   * "Inicial": en una pieza plegada larga (una canaleta de 2,44 m con un perfil de 30 cm)
   * la vista isométrica deja el perfil chiquito y las cotas no se leen. Por eso arranca
   * mirando desde una punta: el perfil y sus cotas se ven grandes y el resto se aleja.
   */
  function vistaInicial() {
    if (ultimo?.renglon.tipoPieza !== 'plegada') return 'iso';
    const caja = new THREE.Box3().setFromObject(modelo.children.find((o) => o.userData.esPiezaPrincipal) || modelo);
    const tamano = caja.getSize(new THREE.Vector3());
    return tamano.z > 3 * Math.max(tamano.x, tamano.y) ? 'punta' : 'iso';
  }

  let tamanoEncuadrado = 0; // lado mayor de la pieza la última vez que se encuadró
  function vista(nombre) {
    if (!modelo) return;
    ultimaVista = nombre;
    camaraMovida = false;
    tamanoEncuadrado = ladoMayor(modelo);
    const efectiva = nombre === 'inicial' ? vistaInicial() : nombre;
    const direccion = DIRECCIONES_VISTA[efectiva] || DIRECCIONES_VISTA.iso;
    // Con las cotas prendidas se encuadra la pieza junto con sus cotas (y con un poco más de aire).
    const caja = new THREE.Box3().expandByObject(modelo);
    if (cotasVisibles && cotas) caja.expandByObject(cotas.grupo);
    if (efectiva === 'punta') {
      // Solo la punta de adelante (Z = largo) y un poco del largo.
      const ladoPerfil = Math.max(caja.max.x - caja.min.x, caja.max.y - caja.min.y);
      caja.min.z = Math.max(caja.min.z, caja.max.z - ladoPerfil * 1.2);
    }
    const margen = cotasVisibles ? 1.2 : 1.12;
    let centro;
    if (efectiva === 'frente' || efectiva === 'lateral') {
      // Frente y lateral sin perspectiva: se ven como un plano (con pendiente, los dos perfiles uno sobre otro).
      camara = camaraOrtografica;
      centro = encuadrarOrtografica(camara, caja, direccion, camaraPerspectiva.aspect, margen);
    } else {
      camara = camaraPerspectiva;
      camara.up.set(0, 1, 0);
      centro = encuadrar(camara, caja, direccion, margen);
    }
    controles.object = camara;
    controles.target.copy(centro);
    controles.update();
  }

  function aplicarResaltado() {
    if (!modelo) return;
    modelo.traverse((objeto) => {
      const datos = objeto.userData;
      if (!objeto.isMesh || !objeto.material?.emissive) return;
      if (datos.tramo === undefined && !datos.accesorio) return;
      const encendido = (datos.tramo !== undefined && datos.tramo === tramoResaltado && !datos.accesorio)
        || (datos.accesorio && datos.accesorio === accesorioResaltado);
      objeto.material.emissive.copy(encendido ? COLOR_RESALTADO : new THREE.Color(0x000000));
      objeto.material.emissiveIntensity = encendido ? 0.6 : 0;
    });
    for (const e of etiquetas) {
      e.elemento.classList.toggle('resaltada', e.datos.indiceTramo !== undefined && e.datos.indiceTramo === tramoResaltado);
    }
  }

  function ladoMayor(objeto) {
    const tamano = new THREE.Box3().setFromObject(objeto).getSize(new THREE.Vector3());
    return Math.max(tamano.x, tamano.y, tamano.z, 1);
  }

  function liberar(objeto) {
    objeto.traverse((o) => {
      if (o.geometry) o.geometry.dispose();
      if (o.material) (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => { m.map?.dispose(); m.dispose(); });
    });
  }

  // ---- cotas ----

  /** Las cotas del perfil se dibujan en la punta de la pieza que queda más cerca de la cámara. */
  function acomodarCotasDelPerfil() {
    if (!cotas?.grupoPerfil || ultimo?.renglon.tipoPieza !== 'plegada') return;
    const z = camara.position.z > cotas.largoCm / 2 ? cotas.largoCm : 0;
    if (cotas.grupoPerfil.position.z !== z) {
      cotas.grupoPerfil.position.z = z;
      cotas.grupoPerfil.updateMatrixWorld(true);
    }
  }

  function quitarCotas() {
    if (cotas) {
      escena.remove(cotas.grupo);
      liberar(cotas.grupo);
    }
    cotas = null;
    for (const e of etiquetas) e.elemento.remove();
    etiquetas = [];
    ficha.replaceChildren();
  }

  function armarCotas() {
    quitarCotas();
    if (!cotasVisibles || !modelo || !ultimo) return;
    try {
      cotas = construirCotas(ultimo.renglon, ultimo.datos, modelo);
    } catch (error) {
      console.warn('No se pudieron armar las cotas 3D:', error);
      return;
    }
    escena.add(cotas.grupo);
    cotas.grupo.updateMatrixWorld(true);
    // Primero las más importantes: son las que se ven si dos se pisan.
    etiquetas = [...cotas.etiquetas].sort((a, b) => b.prioridad - a.prioridad).map((datos) => {
      const elemento = document.createElement('button');
      elemento.type = 'button';
      elemento.className = `etiqueta-cota ${datos.clase}`;
      elemento.textContent = datos.texto;
      elemento.title = datos.titulo || '';
      elemento.addEventListener('click', (e) => { e.stopPropagation(); usarEtiqueta(etiqueta, elemento); });
      const etiqueta = { datos, elemento, ancho: 0, alto: 0 };
      capa.append(elemento);
      return etiqueta;
    });
    for (const item of cotas.ficha) {
      const elemento = document.createElement('button');
      elemento.type = 'button';
      elemento.className = 'etiqueta-cota cota-ficha';
      elemento.textContent = item.texto;
      elemento.title = item.titulo || '';
      elemento.addEventListener('click', (e) => { e.stopPropagation(); usarEtiqueta({ datos: item, elemento }, elemento); });
      ficha.append(elemento);
    }
    ficha.hidden = cotas.ficha.length === 0;
    aplicarResaltado();
  }

  /** Pone cada etiqueta sobre su punto 3D y esconde las que se pisan. */
  const punto = new THREE.Vector3();
  function ubicarEtiquetas() {
    if (!etiquetas.length) return;
    const ancho = contenedor.clientWidth;
    const alto = contenedor.clientHeight;
    if (!ancho || !alto) return;
    const ocupados = [];
    for (const e of etiquetas) {
      const { datos, elemento } = e;
      if (datos.soloEdicion && !modoEdicion) {
        elemento.hidden = true;
        continue;
      }
      punto.copy(datos.posicion).applyMatrix4(datos.ancla.matrixWorld).project(camara);
      if (punto.z < -1 || punto.z > 1) {
        elemento.hidden = true;
        continue;
      }
      elemento.hidden = false;
      if (!e.ancho) {
        e.ancho = elemento.offsetWidth;
        e.alto = elemento.offsetHeight;
      }
      const x = ((punto.x + 1) / 2) * ancho;
      const y = ((1 - punto.y) / 2) * alto;
      const caja = { x1: x - e.ancho / 2, y1: y - e.alto / 2, x2: x + e.ancho / 2, y2: y + e.alto / 2 };
      const editando = edicionAbierta === e;
      const pisa = !editando && ocupados.some((o) => caja.x1 < o.x2 && caja.x2 > o.x1 && caja.y1 < o.y2 && caja.y2 > o.y1);
      elemento.style.visibility = pisa ? 'hidden' : 'visible';
      if (!pisa) ocupados.push(caja);
      elemento.style.transform = `translate(${Math.round(x)}px, ${Math.round(y)}px) translate(-50%, -50%)`;
    }
  }

  /** Tocar una etiqueta: agregar tramo, elegir una parte o escribir la medida nueva. */
  function usarEtiqueta(etiqueta, elemento) {
    const { editar } = etiqueta.datos;
    if (!editar || edicionAbierta) return;
    if (editar.tipo === 'agregar' || editar.tipo === 'seleccionar') {
      opciones.alUsarCota?.(editar);
      return;
    }
    abrirEdicion(etiqueta, elemento);
  }

  function abrirEdicion(etiqueta, elemento) {
    const { datos } = etiqueta;
    edicionAbierta = etiqueta;
    elemento.classList.add('editando');
    const textoOriginal = elemento.textContent;
    let campo;
    if (datos.opciones) {
      campo = document.createElement('select');
      for (const o of datos.opciones) {
        const opcion = document.createElement('option');
        opcion.value = o.valor;
        opcion.textContent = o.etiqueta;
        opcion.selected = String(o.valor) === String(datos.valor);
        campo.append(opcion);
      }
    } else {
      campo = document.createElement('input');
      campo.type = 'text';
      campo.inputMode = 'decimal';
      campo.value = Number.isFinite(datos.valor) ? String(Math.round(datos.valor * 1000) / 1000).replace('.', ',') : '';
      campo.size = Math.max(4, campo.value.length + 1);
    }
    campo.className = 'campo-cota';
    campo.setAttribute('aria-label', datos.titulo || 'Medida');
    elemento.replaceChildren(campo);
    if (datos.unidad) elemento.append(document.createTextNode(` ${datos.unidad}`));

    let cerrado = false;
    const cerrar = (confirmado) => {
      if (cerrado) return;
      cerrado = true;
      edicionAbierta = null;
      elemento.classList.remove('editando');
      elemento.textContent = textoOriginal;
      etiqueta.ancho = 0;
      if (confirmado) {
        const resultado = opciones.alUsarCota?.(datos.editar, campo.value);
        if (resultado && resultado.ok === false) elemento.classList.add('con-error');
      }
      if (redibujarAlCerrar) {
        redibujarAlCerrar = false;
        armarCotas();
      }
    };
    campo.addEventListener('keydown', (e) => {
      // Que Enter y Esc no lleguen a los atajos de la pantalla (Esc cerraría el asistente).
      if (e.key === 'Enter') { e.preventDefault(); e.stopPropagation(); cerrar(true); }
      if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); cerrar(false); }
    });
    campo.addEventListener('click', (e) => e.stopPropagation());
    campo.addEventListener('blur', () => cerrar(true));
    if (datos.opciones) campo.addEventListener('change', () => cerrar(true));
    campo.focus();
    if (campo.select) campo.select();
  }

  return {
    /** Muestra un renglón (con sus tapas, boquetas y cotas). Mantiene la cámara salvo la primera vez. */
    mostrar(renglon, datos, { reencuadrar = false } = {}) {
      if (modelo) {
        escena.remove(modelo);
        liberar(modelo);
      }
      ultimo = { renglon: JSON.parse(JSON.stringify(renglon)), datos };
      modelo = construirModelo(renglon, datos, { regla: !cotasVisibles });
      escena.add(modelo);
      modelo.updateMatrixWorld(true);
      // Si el vendedor está escribiendo en una cota, las etiquetas se rehacen cuando termina.
      if (edicionAbierta) redibujarAlCerrar = true;
      else armarCotas();
      aplicarResaltado();
      // Se vuelve a encuadrar la primera vez, si se pide, o si la pieza cambió mucho de tamaño
      // (por ejemplo, una chapa de 10 cm que pasa a 50) y el vendedor no movió la cámara.
      const cambioMucho = tamanoEncuadrado > 0 && Math.abs(Math.log(ladoMayor(modelo) / tamanoEncuadrado)) > Math.log(1.4);
      if (!encuadrado || reencuadrar || (cambioMucho && !camaraMovida)) {
        vista(ultimaVista);
        encuadrado = true;
      }
    },
    resaltarTramo(indice) {
      tramoResaltado = indice;
      aplicarResaltado();
    },
    /** Resalta una tapa o boqueta ('tapa:izquierda', 'boqueta:0'…) o ninguna (null). */
    resaltarAccesorio(clave) {
      accesorioResaltado = clave;
      aplicarResaltado();
    },
    /** Prende o apaga las cotas. */
    mostrarCotas(visibles) {
      cotasVisibles = visibles;
      if (ultimo) this.mostrar(ultimo.renglon, ultimo.datos);
    },
    cotasVisibles: () => cotasVisibles,
    /** En el editor 3D se ven también los "+" para agregar tramos y las tapas que no están puestas. */
    modoEdicion(activado) {
      modoEdicion = activado;
      contenedor.classList.toggle('en-edicion', activado);
    },
    vista,
    /** Foto del dibujo actual (PNG en texto "data:image/png;base64,…"). */
    capturar() {
      renderer.render(escena, camara);
      return renderer.domElement.toDataURL('image/png');
    },
    destruir() {
      activo = false;
      observador.disconnect();
      quitarCotas();
      if (modelo) liberar(modelo);
      controles.dispose();
      renderer.dispose();
      renderer.domElement.remove();
      capa.remove();
    },
  };
}
