// =============================================================
// hojaImpresa.js
// Arma el CONTENIDO de la hoja impresa (sin dibujarla): qué se escribe y dónde.
// Regla: cada dato aparece UNA sola vez en la hoja (ver docs/DIAGNOSTICO.md, matriz R1 a R15).
//
// La hoja tiene dos zonas por renglón:
//  - FACTURACIÓN (fila de la tabla): descripción, código, piezas y cantidad. Es la "foto"
//    guardada al emitir: no se toca. Las tapas y boquetas puestas van en filas con su código.
//  - FABRICACIÓN (debajo): el dibujo 2D acotado (medidas, ángulos, tipo de tramo, flecha de
//    pintura), la FICHA DE MATERIAL junto al dibujo (material, calibre, color, lado de pintura)
//    y las NOTAS, que son solo lo que el dibujo NO dice (boca de una boqueta, pared de un corte,
//    observaciones, avisos).
// Única superposición admitida, pedida por la empresa: material, calibre y color figuran
// abreviados en la descripción ("pp negro CH 25") y completos en la ficha.
//
// No se pierde ningún dato de producción: lo que se quitó del texto está en un dibujo
// (ver la tabla de docs/CAMBIOS.md, cambio D9).
// =============================================================

import { datosDelRenglon, mostrar3d } from './fotoCalculo.js';
import { leerNumero, formatearCorto, formatearFecha, formatearHora } from './numeros.js';
import { empresaDeNota, identificadorDeNota, repartoPorPlanta, plantaDeRenglon, buscarPlanta } from './empresas.js';
import { tienePendiente } from './pendiente.js';
import { normalizarBoqueta, medidasDeTapa, tipoDeTapa } from './accesoriosCanaleta.js';
import { calcularDesarrollo } from './desarrollo.js';

const f = (valor) => {
  const n = leerNumero(valor);
  return Number.isFinite(n) ? formatearCorto(n) : '?';
};

/** ¿El renglón lleva dibujo en la hoja? (artículos, servicios y piezas con plano no) */
export function llevaDibujo(renglon) {
  return !renglon.sinDibujo && renglon.generador3d !== 'articulo';
}

/** Ficha de material que va junto al 2D. Vacía si el renglón no lleva chapa. */
export function fichaDeMaterial(renglon, materiales) {
  if (renglon.sinMaterial) return [];
  const material = materiales.materiales.find((m) => m.id === renglon.materialId);
  const calibre = materiales.calibres.find((c) => c.id === renglon.calibreId);
  const prepintada = renglon.terminacion === 'P';
  const ficha = [
    { rotulo: 'Material', valor: `${material?.nombre || renglon.materialId || '—'}${prepintada ? ' prepintada' : ''}` },
    { rotulo: 'Calibre', valor: calibre ? `C${calibre.numero} (${formatearCorto(calibre.espesorMm)} mm)` : '—' },
  ];
  if (prepintada) {
    ficha.push({ rotulo: 'Color', valor: materiales.colores.find((c) => c.id === renglon.colorId)?.nombre || '—' });
    ficha.push({ rotulo: 'Pintura', valor: renglon.ladoPintura === 'ambos' ? 'DE LOS DOS LADOS' : String(renglon.ladoPintura || '—').toUpperCase() });
  }
  return ficha;
}

/** Notas de tapas y boquetas: solo lo que la vista desde arriba y las caras NO muestran. */
function notasDeAccesorios(renglon, config) {
  const accesorios = renglon.accesorios;
  if (!accesorios) return [];
  const notas = [];
  for (const lado of ['izquierda', 'derecha']) {
    if (tipoDeTapa(accesorios, lado) === 'ninguna') continue;
    const medidas = medidasDeTapa(accesorios, lado, config);
    const partes = [];
    if (medidas.aMedida) partes.push(`a medida (${medidas.perfil.tramos.map((t) => f(t.medidaCm)).join(' + ')} = ${formatearCorto(calcularDesarrollo(medidas.perfil.tramos))} cm)`);
    const propias = accesorios[lado === 'izquierda' ? 'tapaIzquierdaMedidas' : 'tapaDerechaMedidas'];
    if (propias?.pestanaCm !== undefined) partes.push(`pestaña ${formatearCorto(medidas.pestanaCm)} cm`);
    if (partes.length) notas.push({ rotulo: `Tapa ${lado}`, valor: partes.join(', ') });
  }
  (accesorios.boquetas || []).forEach((original, i) => {
    const b = normalizarBoqueta(original, config);
    const partes = [];
    if (b.tipo === 'boqueta') partes.push(`boca ${f(b.largoBocaCm)} cm`);
    if (b.tipo === 'tronera') partes.push(`alto ${f(b.altoCm)} cm`);
    if (b.ubicacion !== 'fondo') {
      partes.push(`en la tapa ${b.ubicacion === 'tapaDerecha' ? 'derecha' : 'izquierda'}: centro a ${f(b.alturaCm)} cm del fondo`);
      if (leerNumero(b.desplazamientoCm)) partes.push(`corrida ${f(b.desplazamientoCm)} cm del medio`);
    }
    if (partes.length) notas.push({ rotulo: `Boqueta ${i + 1}`, valor: partes.join(', ') });
  });
  return notas;
}

/** Notas de cortes: solo la pared (alto y lado), que el dibujo de la cara no muestra. */
function notasDeCortes(renglon) {
  return (renglon.cortes || []).map((c, i) => (leerNumero(c.paredAlturaCm) > 0
    ? { rotulo: `Corte ${i + 1}`, valor: `pared de ${f(c.paredAlturaCm)} cm ${c.paredLado === 'adentro' ? 'hacia adentro' : 'hacia afuera'}` }
    : null)).filter(Boolean);
}

/** Avisos que ya están dichos en otro lugar de la hoja (no se repiten). */
function avisoYaDicho(aviso, foto) {
  return aviso.startsWith('Código pendiente') || aviso.startsWith('Código genérico')
    || (Boolean(foto.empalmeTexto) && aviso.startsWith('Supera el largo de la chapa'));
}

/**
 * Contenido de un renglón de la hoja.
 * @returns {{id, numero, descripcion, codigo, piezas, cantidad, adicionales, ficha, notas, dibujo, con3d}}
 *   dibujo: 'perfil' | 'pendiente' | 'especial' | null (sin dibujo)
 */
export function armarRenglonDeHoja(renglon, indice, nota, datos, variasPlantas = false) {
  const { vivo, foto } = datosDelRenglon(renglon, datos);
  const usaPerfil = renglon.tipoPieza === 'plegada' || renglon.usaPerfil;
  const conPendiente = Boolean(tienePendiente(renglon) && vivo.pendiente);
  const conDibujo = llevaDibujo(renglon);

  const notas = [];
  if (conPendiente) notas.push({ rotulo: 'Pendiente', valor: foto.pendienteTexto || vivo.pendiente.texto });
  notas.push(...notasDeAccesorios(renglon, datos.config), ...notasDeCortes(renglon));
  (usaPerfil ? renglon.perfil?.tramos || [] : []).forEach((tramo, n) => {
    if (tramo.observacion) notas.push({ rotulo: `Tramo ${n + 1}`, valor: tramo.observacion });
  });
  for (const aviso of (foto.avisos || []).filter((a) => !avisoYaDicho(a, foto))) notas.push({ rotulo: 'Aviso', valor: aviso });
  if (renglon.observaciones) notas.push({ rotulo: 'Observaciones', valor: renglon.observaciones });
  if (variasPlantas) {
    const destino = plantaDeRenglon(renglon, nota, datos);
    notas.push({ rotulo: destino.motivo === 'deposito' ? 'Sale del depósito de' : 'Lo hace', valor: buscarPlanta(datos, destino.plantaId)?.nombre || '—' });
  }

  return {
    id: renglon.id,
    numero: indice + 1,
    descripcion: foto.descripcion,
    // El estado del código va UNA vez, en su columna.
    codigo: foto.codigo ? `${foto.codigo}${foto.codigoGenerico ? ' (genérico)' : ''}` : 'PENDIENTE',
    piezas: formatearCorto(foto.cantidad.piezas, 2),
    cantidad: foto.cantidad.unidad === 'chapas' ? foto.cantidad.texto : `${foto.cantidad.texto} ${foto.cantidad.abreviatura ?? 'u.'}`,
    adicionales: (foto.codigosAdicionales || []).map((extra) => ({ descripcion: `+ ${extra.descripcion} (puesta en la canaleta)`, codigo: extra.codigo, cantidad: `${extra.cantidad} u.` })),
    ficha: fichaDeMaterial(renglon, datos.materiales),
    notas,
    dibujo: !conDibujo ? null : (conPendiente ? 'pendiente' : (usaPerfil ? 'perfil' : 'especial')),
    con3d: conDibujo && mostrar3d(renglon, nota, datos),
  };
}

/**
 * Contenido completo de la hoja de una nota.
 * @returns {{empresa, origen, emitida, numero, identificador, fecha, factura, cliente, entrega, urgente, renglones, pie}}
 */
export function armarHoja(nota, datos) {
  const emitida = nota.estado === 'emitida';
  const variasPlantas = repartoPorPlanta(nota, datos).length > 1;
  const momento = new Date(nota.fechaEmision || nota.fechaCreacion || Date.now());
  const sucursal = (datos.sucursales || []).find((s) => s.id === nota.sucursalId);
  const vendedor = (datos.vendedores || []).find((v) => v.id === nota.vendedorId);
  const [a, m, d] = String(nota.fechaEntrega || '').split('-');
  return {
    empresa: empresaDeNota(nota, datos),
    origen: sucursal?.nombre || nota.sucursalId || '—',
    emitida,
    numero: emitida ? String(nota.numero) : 'BORRADOR',
    identificador: identificadorDeNota(nota, datos),
    fecha: formatearFecha(momento),
    factura: nota.factura || '—',
    cliente: nota.cliente || '—',
    // La entrega comprometida y la urgencia las usa producción: van una vez, en el encabezado, si se cargaron.
    entrega: nota.fechaEntrega ? `${d}/${m}/${a}` : null,
    urgente: nota.prioridad === 'urgente',
    renglones: (nota.renglones || []).map((renglon, i) => armarRenglonDeHoja(renglon, i, nota, datos, variasPlantas)),
    // La fecha ya está en el encabezado: en el pie va solo la hora de emisión.
    pie: { vendedor: vendedor?.nombre || nota.vendedorId || '—', emision: emitida ? `Emitida a las ${formatearHora(momento)}` : 'BORRADOR (sin emitir)' },
  };
}

/** Todos los textos de un renglón de la hoja (para revisar que nada se repita). */
export function textosDeRenglon(renglonDeHoja, textosDeDibujos = []) {
  return {
    facturacion: [renglonDeHoja.descripcion, renglonDeHoja.codigo, ...renglonDeHoja.adicionales.flatMap((x) => [x.descripcion, x.codigo])],
    fabricacion: [
      ...renglonDeHoja.ficha.map((x) => `${x.rotulo}: ${x.valor}`),
      ...renglonDeHoja.notas.map((x) => `${x.rotulo}: ${x.valor}`),
      ...textosDeDibujos,
    ],
  };
}
