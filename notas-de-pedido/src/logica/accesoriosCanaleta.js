// =============================================================
// accesoriosCanaleta.js
// Tapas y boquetas que van PUESTAS en la canaleta (en el mismo renglón).
//
// Tapas (izquierda y derecha): ninguna, soldada o engrampada.
//   - Por defecto la tapa tiene la forma de la canaleta (en esa punta).
//   - "A medida": la tapa tiene su propio perfil (más baja, otra forma…),
//     siempre que ENTRE en la canaleta. Se apoya en el fondo de la canaleta.
//   - Pestaña de apoyo: lo que se suelda o engrampa (cm).
//
// Boquetas: de cualquiera de los tipos que se venden sueltos:
//   boqueta (redonda, cuadrada o rectangular), tronera, embudo colector
//   moldura o colector recto. Pueden ir:
//   - en el FONDO: posición = desde la punta izquierda hasta el centro;
//   - en una TAPA: altura del centro sobre el fondo y corrimiento desde el medio.
//   Donde va la boqueta, la chapa queda cortada (ver cortes.js).
//
// Las tapas y boquetas sueltas son productos aparte (ver catalogo.json).
// =============================================================

import { leerNumero, formatearCorto, redondear } from './numeros.js';
import { calcularGeometria, calcularLimites, buscarFondo } from './geometria.js';
import { calcularDesarrollo } from './desarrollo.js';
import { tienePendiente, perfilFinal } from './pendiente.js';
import { puntoEnPoligono, moverPuntos, contornoDeHuella } from './poligonos.js';

export const FORMAS_BOQUETA = ['redonda', 'cuadrada', 'rectangular'];

/** Tipos de boqueta: los mismos productos que se venden sueltos (plantillaId = de dónde sale el código). */
export const TIPOS_BOQUETA = [
  { valor: 'boqueta', texto: 'boqueta', plantillaId: 'boqueta_suelta' },
  { valor: 'tronera', texto: 'tronera', plantillaId: 'tronera' },
  { valor: 'embudo_colector_moldura', texto: 'embudo colector moldura', plantillaId: 'embudo_colector_moldura' },
  { valor: 'colector_recto', texto: 'colector recto', plantillaId: 'colector_recto' },
];

export const UBICACIONES_BOQUETA = [
  { valor: 'fondo', texto: 'en el fondo' },
  { valor: 'tapaIzquierda', texto: 'en la tapa izquierda' },
  { valor: 'tapaDerecha', texto: 'en la tapa derecha' },
];

/** Accesorios de una canaleta nueva: sin tapas ni boquetas. */
export function accesoriosVacios() {
  return { tapaIzquierda: 'ninguna', tapaDerecha: 'ninguna', boquetas: [] };
}

/** Boqueta nueva con los valores por defecto de config.json. */
export function crearBoqueta(config) {
  return { ...config.accesoriosCanaleta.boquetaPorDefecto };
}

/** Completa una boqueta (por ejemplo una guardada antes de que existieran los tipos). */
export function normalizarBoqueta(boqueta, config) {
  return {
    ...(config?.accesoriosCanaleta?.boquetaPorDefecto || {}),
    ...boqueta,
    tipo: boqueta.tipo || 'boqueta',
    ubicacion: boqueta.ubicacion || 'fondo',
  };
}

const f = (v) => formatearCorto(leerNumero(v));

/** "Ø10", "10x10", "10x5", "20x10 salida Ø10" según el tipo y la forma. */
export function medidaDeBoqueta(boqueta) {
  const tipo = boqueta.tipo || 'boqueta';
  if (tipo === 'tronera') return `${f(boqueta.bocaACm)}x${f(boqueta.bocaBCm)} salida Ø${f(boqueta.diametroSalidaCm)}`;
  if (tipo !== 'boqueta') return `${f(boqueta.ladoACm)}x${f(boqueta.ladoBCm)}`;
  if (boqueta.forma === 'redonda') return `Ø${f(boqueta.diametroCm)}`;
  if (boqueta.forma === 'cuadrada') return `${f(boqueta.ladoACm)}x${f(boqueta.ladoACm)}`;
  return `${f(boqueta.ladoACm)}x${f(boqueta.ladoBCm)}`;
}

/** "boqueta redonda Ø10", "tronera 20x10 salida Ø10", "colector recto 10x5". */
export function nombreDeBoqueta(boqueta) {
  const tipo = TIPOS_BOQUETA.find((t) => t.valor === (boqueta.tipo || 'boqueta'));
  const forma = (boqueta.tipo || 'boqueta') === 'boqueta' ? ` ${boqueta.forma}` : '';
  return `${tipo ? tipo.texto : 'boqueta'}${forma} ${medidaDeBoqueta(boqueta)}`;
}

/**
 * Lo que ocupa la boca de la boqueta sobre la chapa (es el corte que lleva la chapa).
 * ancho = a lo ancho del fondo (o de la tapa); alto = a lo largo de la canaleta (o hacia arriba en la tapa).
 * @returns {{forma: 'circulo', diametro} | {forma: 'rect', ancho, alto}}
 */
export function huellaDeBoqueta(boqueta) {
  const tipo = boqueta.tipo || 'boqueta';
  if (tipo === 'tronera') return { forma: 'rect', ancho: leerNumero(boqueta.bocaACm), alto: leerNumero(boqueta.bocaBCm) };
  if (tipo !== 'boqueta') return { forma: 'rect', ancho: leerNumero(boqueta.ladoACm), alto: leerNumero(boqueta.ladoBCm) };
  if (boqueta.forma === 'redonda') return { forma: 'circulo', diametro: leerNumero(boqueta.diametroCm) };
  const a = leerNumero(boqueta.ladoACm);
  return { forma: 'rect', ancho: a, alto: boqueta.forma === 'cuadrada' ? a : leerNumero(boqueta.ladoBCm) };
}

/** Medidas que tiene que tener cada tipo de boqueta. */
function camposDeBoqueta(boqueta) {
  const tipo = boqueta.tipo || 'boqueta';
  if (tipo === 'tronera') return ['bocaACm', 'bocaBCm', 'diametroSalidaCm', 'altoCm'];
  if (tipo !== 'boqueta') return ['ladoACm', 'ladoBCm'];
  const medidas = boqueta.forma === 'redonda' ? ['diametroCm'] : (boqueta.forma === 'cuadrada' ? ['ladoACm'] : ['ladoACm', 'ladoBCm']);
  return [...medidas, 'largoBocaCm'];
}

// -------------------------------------------------------------
// Tapas
// -------------------------------------------------------------

const campoTipoTapa = (lado) => (lado === 'izquierda' ? 'tapaIzquierda' : 'tapaDerecha');
const campoMedidasTapa = (lado) => (lado === 'izquierda' ? 'tapaIzquierdaMedidas' : 'tapaDerechaMedidas');

/** 'ninguna' | 'soldada' | 'engrampada' */
export function tipoDeTapa(accesorios, lado) {
  return accesorios?.[campoTipoTapa(lado)] || 'ninguna';
}

/** Medidas de la tapa: si es a medida (con su perfil) y la pestaña de apoyo. */
export function medidasDeTapa(accesorios, lado, config) {
  const medidas = accesorios?.[campoMedidasTapa(lado)] || {};
  const pestana = leerNumero(medidas.pestanaCm);
  return {
    aMedida: Boolean(medidas.aMedida && medidas.perfil?.tramos?.length),
    perfil: medidas.perfil || null,
    pestanaCm: pestana > 0 ? pestana : (config?.accesoriosCanaleta?.pestanaTapaCm ?? 1.5),
  };
}

/** Cambia las medidas de una tapa (devuelve accesorios nuevos). */
export function cambiarMedidasTapa(accesorios, lado, cambios) {
  const campo = campoMedidasTapa(lado);
  return { ...accesorios, [campo]: { ...(accesorios[campo] || {}), ...cambios } };
}

/** Perfil de la canaleta en esa punta (con pendiente, la derecha tiene el perfil final). */
export function perfilDeLaPunta(renglon, lado) {
  return lado === 'derecha' && tienePendiente(renglon) ? perfilFinal(renglon.perfil) : renglon.perfil;
}

/** Perfil de la tapa: el suyo si es a medida; si no, el de la canaleta en esa punta. */
export function perfilDeTapa(renglon, lado, config) {
  const medidas = medidasDeTapa(renglon.accesorios, lado, config);
  return medidas.aMedida ? medidas.perfil : perfilDeLaPunta(renglon, lado);
}

/**
 * Dónde va la tapa: se dibuja desde el mismo punto de arranque que la canaleta y
 * se baja (o se sube) hasta apoyar en el fondo (SUPUESTO, ver PENDIENTES.md).
 * @returns {{perfil, dy, poligonoCanaleta, poligonoTapa, geometriaCanaleta}}
 */
export function ubicarTapa(renglon, lado, config) {
  const perfil = perfilDeTapa(renglon, lado, config);
  const geometriaCanaleta = calcularGeometria(perfilDeLaPunta(renglon, lado), config);
  const geometriaTapa = calcularGeometria(perfil, config);
  const dy = redondear(calcularLimites(geometriaCanaleta.puntos).minY - calcularLimites(geometriaTapa.puntos).minY, 6);
  return {
    perfil,
    dy,
    poligonoCanaleta: geometriaCanaleta.puntos,
    poligonoTapa: moverPuntos(geometriaTapa.puntos, 0, dy),
    geometriaCanaleta,
  };
}

/** ¿La tapa (a medida) entra en la canaleta? Se revisan todas sus esquinas y el medio de cada lado. */
export function tapaEntra(renglon, lado, config) {
  const { poligonoCanaleta, poligonoTapa } = ubicarTapa(renglon, lado, config);
  const puntos = [];
  poligonoTapa.forEach((p, i) => {
    const q = poligonoTapa[(i + 1) % poligonoTapa.length];
    puntos.push(p, { x: (p.x + q.x) / 2, y: (p.y + q.y) / 2 });
  });
  const afuera = puntos.filter((p) => !puntoEnPoligono(p, poligonoCanaleta, 0.1)).length;
  return afuera
    ? { entra: false, mensaje: `Tapa ${lado}: la tapa a medida no entra en la canaleta (se sale del perfil)` }
    : { entra: true, mensaje: null };
}

/** Centro de una boqueta puesta en una tapa, en el plano de la tapa (cm, como el perfil). */
export function centroDeBoquetaEnTapa(renglon, boqueta, config) {
  const lado = boqueta.ubicacion === 'tapaDerecha' ? 'derecha' : 'izquierda';
  const { geometriaCanaleta } = ubicarTapa(renglon, lado, config);
  const fondo = buscarFondo(geometriaCanaleta.segmentos).punto;
  const minY = calcularLimites(geometriaCanaleta.puntos).minY;
  return { x: fondo.x + (leerNumero(boqueta.desplazamientoCm) || 0), y: minY + (leerNumero(boqueta.alturaCm) || 0) };
}

// -------------------------------------------------------------
// Revisión, descripción y detalle
// -------------------------------------------------------------

/**
 * Revisa tapas y boquetas.
 * @param {object} renglon  (opcional) la canaleta: hace falta para ver si la tapa a medida
 *                          y las boquetas puestas en las tapas entran
 * @returns {Array<{nivel:'error'|'aviso', mensaje}>}
 */
export function validarAccesorios(accesorios, largoCm, config, renglon = null) {
  const problemas = [];
  if (!accesorios) return problemas;
  const tipos = config.accesoriosCanaleta.tiposDeTapa;
  for (const lado of ['izquierda', 'derecha']) {
    const tipo = tipoDeTapa(accesorios, lado);
    if (!tipos.includes(tipo)) {
      problemas.push({ nivel: 'error', mensaje: `Tapa ${lado}: elegí ninguna, soldada o engrampada` });
      continue;
    }
    if (tipo === 'ninguna' || !renglon?.perfil?.tramos?.length) continue;
    const medidas = medidasDeTapa(accesorios, lado, config);
    const pestana = leerNumero(accesorios[campoMedidasTapa(lado)]?.pestanaCm);
    if (accesorios[campoMedidasTapa(lado)]?.pestanaCm !== undefined && !(pestana > 0)) {
      problemas.push({ nivel: 'error', mensaje: `Tapa ${lado}: la pestaña de apoyo tiene que ser mayor a 0` });
    }
    if (medidas.aMedida) {
      const revision = tapaEntra(renglon, lado, config);
      if (!revision.entra) problemas.push({ nivel: 'error', mensaje: revision.mensaje });
    }
  }

  const largo = leerNumero(largoCm);
  (accesorios.boquetas || []).forEach((original, i) => {
    const b = normalizarBoqueta(original, config);
    const n = i + 1;
    if (!TIPOS_BOQUETA.some((t) => t.valor === b.tipo)) {
      problemas.push({ nivel: 'error', mensaje: `Boqueta ${n}: elegí el tipo` });
      return;
    }
    if (b.tipo === 'boqueta' && !FORMAS_BOQUETA.includes(b.forma)) {
      problemas.push({ nivel: 'error', mensaje: `Boqueta ${n}: elegí la forma` });
      return;
    }
    if (camposDeBoqueta(b).some((campo) => !(leerNumero(b[campo]) > 0))) {
      problemas.push({ nivel: 'error', mensaje: `Boqueta ${n}: falta una medida` });
      return;
    }
    const huella = huellaDeBoqueta(b);

    if (b.ubicacion === 'fondo') {
      const posicion = leerNumero(b.posicionCm);
      const medioLargo = (huella.forma === 'circulo' ? huella.diametro : huella.alto) / 2;
      if (!Number.isFinite(posicion) || posicion < 0 || (largo > 0 && posicion > largo)) {
        problemas.push({ nivel: 'error', mensaje: `Boqueta ${n}: la posición tiene que estar entre 0 y ${formatearCorto(largo || 0)} cm` });
      } else if (largo > 0 && (posicion - medioLargo < 0 || posicion + medioLargo > largo)) {
        problemas.push({ nivel: 'aviso', mensaje: `Boqueta ${n}: queda pegada a la punta de la canaleta (se sale del largo)` });
      }
      return;
    }

    // En una tapa: la tapa tiene que existir y la boca tiene que entrar en ella.
    const lado = b.ubicacion === 'tapaDerecha' ? 'derecha' : 'izquierda';
    if (!UBICACIONES_BOQUETA.some((u) => u.valor === b.ubicacion)) {
      problemas.push({ nivel: 'error', mensaje: `Boqueta ${n}: elegí dónde va` });
    } else if (tipoDeTapa(accesorios, lado) === 'ninguna') {
      problemas.push({ nivel: 'error', mensaje: `Boqueta ${n}: va en la tapa ${lado}, pero la canaleta no tiene tapa ${lado}` });
    } else if (renglon?.perfil?.tramos?.length) {
      const centro = centroDeBoquetaEnTapa(renglon, b, config);
      const { poligonoTapa } = ubicarTapa(renglon, lado, config);
      const contorno = contornoDeHuella(centro, huella);
      if (contorno.some((p) => !puntoEnPoligono(p, poligonoTapa, 0.05))) {
        problemas.push({ nivel: 'error', mensaje: `Boqueta ${n}: no entra en la tapa ${lado} (cambiá la altura, el corrimiento o la medida)` });
      }
    }
  });
  return problemas;
}

/** ¿La tapa de ese lado es a medida? (sin config: solo mira si tiene su perfil) */
function esAMedida(accesorios, lado) {
  const medidas = accesorios?.[campoMedidasTapa(lado)];
  return Boolean(medidas?.aMedida && medidas.perfil?.tramos?.length);
}

/** Texto corto para la descripción: "c/ 2 tapas soldadas y 1 boqueta". */
export function describirAccesorios(accesorios) {
  if (!accesorios) return '';
  const partes = [];
  const izq = tipoDeTapa(accesorios, 'izquierda');
  const der = tipoDeTapa(accesorios, 'derecha');
  const hayIzq = izq !== 'ninguna';
  const hayDer = der !== 'ninguna';
  const marca = (lado) => (esAMedida(accesorios, lado) ? ' a medida' : '');
  if (hayIzq && hayDer && izq === der && marca('izquierda') === marca('derecha')) partes.push(`2 tapas ${izq}s${marca('izquierda') ? ' a medida' : ''}`);
  else {
    if (hayIzq) partes.push(`tapa izq. ${izq}${marca('izquierda')}`);
    if (hayDer) partes.push(`tapa der. ${der}${marca('derecha')}`);
  }
  // Boquetas agrupadas por tipo: "1 boqueta", "2 boquetas", "1 tronera"…
  const porTipo = new Map();
  for (const b of accesorios.boquetas || []) {
    const tipo = TIPOS_BOQUETA.find((t) => t.valor === (b.tipo || 'boqueta')) || TIPOS_BOQUETA[0];
    porTipo.set(tipo.texto, (porTipo.get(tipo.texto) || 0) + 1);
  }
  for (const [texto, cantidad] of porTipo) {
    const plural = cantidad > 1 ? texto.replace(/^(\S+)/, (palabra) => `${palabra}s`) : texto;
    partes.push(`${cantidad} ${plural}`);
  }
  if (!partes.length) return '';
  // "a", "a y b", "a, b y c"
  const texto = partes.length > 1 ? `${partes.slice(0, -1).join(', ')} y ${partes[partes.length - 1]}` : partes[0];
  return `c/ ${texto}`;
}

/**
 * Líneas de detalle para la nota impresa (lo que producción necesita saber).
 * @param {object} renglon  (opcional) para escribir las medidas de las tapas a medida
 */
export function detalleDeAccesorios(accesorios, renglon = null, config = null) {
  if (!accesorios) return [];
  const lineas = [];
  for (const lado of ['izquierda', 'derecha']) {
    const tipo = tipoDeTapa(accesorios, lado);
    if (tipo === 'ninguna') continue;
    const medidas = medidasDeTapa(accesorios, lado, config);
    let linea = `Tapa ${lado}: ${tipo}`;
    if (medidas.aMedida) {
      const tramos = medidas.perfil.tramos.map((t) => f(t.medidaCm)).join(' + ');
      linea += `, a medida (${tramos} = ${formatearCorto(calcularDesarrollo(medidas.perfil.tramos))} cm)`;
    }
    if (accesorios[campoMedidasTapa(lado)]?.pestanaCm !== undefined) linea += `, pestaña ${formatearCorto(medidas.pestanaCm)} cm`;
    lineas.push(linea);
  }
  (accesorios.boquetas || []).forEach((original, i) => {
    const b = normalizarBoqueta(original, config);
    let linea = `Boqueta ${i + 1}: ${nombreDeBoqueta(b)}`;
    if (b.tipo === 'boqueta') linea += `, boca ${f(b.largoBocaCm)} cm`;
    if (b.tipo === 'tronera') linea += `, alto ${f(b.altoCm)} cm`;
    if (b.ubicacion === 'fondo') {
      linea += `, centro a ${f(b.posicionCm)} cm de la punta izquierda`;
    } else {
      linea += `, en la tapa ${b.ubicacion === 'tapaDerecha' ? 'derecha' : 'izquierda'}: centro a ${f(b.alturaCm)} cm del fondo`;
      if (leerNumero(b.desplazamientoCm)) linea += `, corrida ${f(b.desplazamientoCm)} cm del medio`;
    }
    lineas.push(linea);
  });
  return lineas;
}
