// =============================================================
// empresas.js
// El GRUPO: tres empresas (Abasto Soluciones, HIPER Argentina y G-TEC) que venden
// con el mismo programa, y las plantas donde se fabrica.
//
// Una sola unión, sin datos repetidos:
//   vendedor → sucursal → empresa          (datos/sucursales.json: "empresaId")
//   plantilla → quién la vende ("empresas") y dónde se hace ("fabricaEn")
//   nota → empresa + sucursal de origen    (nota.empresaId, nota.sucursalId)
//
// De acá salen: el catálogo que ve cada vendedor, el identificador completo de la
// nota (AB-C-123), el logo de la hoja impresa y a qué planta va cada renglón.
// "datos.grupo" es datos/empresas.json: { grupo, empresas: [...], plantas: [...] }.
// =============================================================

export const TERCERO = 'tercero';

export const TIPOS_DE_RENGLON = [
  { valor: 'plegada', texto: 'Pieza plegada', ayuda: 'Perfil dibujado por tramos (canaleta, babeta, cumbrera…)' },
  { valor: 'especial', texto: 'Pieza especial', ayuda: 'Con medidas propias pero sin tramos (boqueta, caño, sombrero…)' },
  { valor: 'articulo', texto: 'Artículo de reventa', ayuda: 'Se vende tal cual, sale de depósito' },
  { valor: 'metalmecanica', texto: 'Pieza metalmecánica a medida', ayuda: 'Descripción, medidas, material y espesor en mm, con plano opcional' },
  { valor: 'servicio', texto: 'Servicio', ayuda: 'Alcance, unidad (horas, piezas…) y lugar' },
];

/**
 * Tipo de renglón (se DERIVA, no se guarda dos veces): "tipoPieza" dice cómo se calcula
 * (plegada, especial, metalmecanica, servicio) y un especial sin material es un artículo.
 */
export function tipoDeRenglon(renglon) {
  if (renglon.tipoPieza === 'plegada' || renglon.tipoPieza === 'metalmecanica' || renglon.tipoPieza === 'servicio') return renglon.tipoPieza;
  return renglon.sinMaterial ? 'articulo' : 'especial';
}

export const listaEmpresas = (datos) => datos.grupo?.empresas || [];
export const listaPlantas = (datos) => datos.grupo?.plantas || [];

export function buscarEmpresa(datos, empresaId) {
  return listaEmpresas(datos).find((e) => e.id === empresaId) || null;
}

export function buscarPlanta(datos, plantaId) {
  return listaPlantas(datos).find((p) => p.id === plantaId) || null;
}

/** Empresa de una sucursal. Una sucursal sin empresa (datos viejos) es de la primera empresa de la lista. */
export function empresaDeSucursal(datos, sucursalId) {
  const sucursal = (datos.sucursales || []).find((s) => s.id === sucursalId);
  return buscarEmpresa(datos, sucursal?.empresaId) || listaEmpresas(datos)[0] || null;
}

/** Empresa que emite la nota: la guardada en la nota o, si es vieja, la de su sucursal. */
export function empresaDeNota(nota, datos) {
  return buscarEmpresa(datos, nota?.empresaId) || empresaDeSucursal(datos, nota?.sucursalId);
}

export function sucursalesDeEmpresa(datos, empresaId) {
  const primera = listaEmpresas(datos)[0]?.id;
  return (datos.sucursales || []).filter((s) => (s.empresaId || primera) === empresaId);
}

export function vendedoresDeEmpresa(datos, empresaId) {
  const ids = new Set(sucursalesDeEmpresa(datos, empresaId).map((s) => s.id));
  return (datos.vendedores || []).filter((v) => ids.has(v.sucursalHabitualId));
}

/**
 * Identificador completo de la nota: PREFIJO de la empresa + letra de la sucursal + número.
 *   AB-C-123   (Abasto, sucursal Colón, nota 123)
 * El número sigue siendo correlativo por sucursal (regla 5.1); como cada sucursal es de una
 * sola empresa, queda correlativo por empresa y sucursal. Borrador: "AB-C-borrador".
 */
export function identificadorDeNota(nota, datos) {
  const empresa = empresaDeNota(nota, datos);
  const sucursal = (datos.sucursales || []).find((s) => s.id === nota?.sucursalId);
  const numero = nota?.numero ?? 'borrador';
  return [empresa?.prefijo, sucursal?.letra, numero].filter((parte) => parte !== undefined && parte !== null && parte !== '').join('-');
}

// ---------- catálogo por empresa ----------

/** ¿La plantilla es del catálogo de esa empresa? "empresas" vacío o ausente = compartida por todo el grupo. */
export function plantillaEsDeEmpresa(plantilla, empresaId) {
  const lista = plantilla.empresas || [];
  return lista.length === 0 || lista.includes(empresaId);
}

/**
 * Plantillas que ve el vendedor: las de su empresa o, con el interruptor "ver todo el grupo", todas.
 * @returns {Array} plantillas (mismo orden del catálogo)
 */
export function plantillasVisibles(catalogo, empresaId, verTodoElGrupo = false) {
  if (verTodoElGrupo || !empresaId) return catalogo.plantillas;
  return catalogo.plantillas.filter((p) => plantillaEsDeEmpresa(p, empresaId));
}

// ---------- dónde se hace cada renglón ----------

/** "stock" (se entrega de depósito) o "a_pedido" (se fabrica para la nota). */
export function abastecimientoDe(renglon, plantilla = null) {
  if (renglon.abastecimiento) return renglon.abastecimiento;
  if (plantilla?.abastecimiento) return plantilla.abastecimiento;
  return tipoDeRenglon(renglon) === 'articulo' ? 'stock' : 'a_pedido';
}

/**
 * Planta que tiene que ocuparse del renglón.
 * - A pedido y con planta propia (plegados de Abasto, piezas y servicios de G-TEC): esa planta,
 *   aunque la nota la emita otra empresa del grupo → la nota se reparte sola.
 * - De stock, de otra marca ("tercero") o sin planta fija: la planta de la empresa que emite
 *   (lo prepara su depósito).
 * @returns {{plantaId: string|null, motivo: 'fabrica'|'deposito'}}
 */
export function plantaDeRenglon(renglon, nota, datos) {
  const plantilla = (datos.catalogo?.plantillas || []).find((p) => p.id === renglon.plantillaId) || null;
  const propia = empresaDeNota(nota, datos)?.plantaPorDefecto || listaPlantas(datos)[0]?.id || null;
  const fabricaEn = renglon.fabricaEn !== undefined ? renglon.fabricaEn : (plantilla?.fabricaEn ?? null);
  if (abastecimientoDe(renglon, plantilla) !== 'a_pedido' || fabricaEn === TERCERO) return { plantaId: propia, motivo: 'deposito' };
  return { plantaId: buscarPlanta(datos, fabricaEn) ? fabricaEn : propia, motivo: 'fabrica' };
}

/**
 * Cómo se reparte la nota entre plantas.
 * @returns {Array<{plantaId, nombre, renglones: number[]}>} renglones = posiciones (0 = primer renglón)
 */
export function repartoPorPlanta(nota, datos) {
  const grupos = [];
  (nota.renglones || []).forEach((renglon, i) => {
    const { plantaId } = plantaDeRenglon(renglon, nota, datos);
    let grupo = grupos.find((g) => g.plantaId === plantaId);
    if (!grupo) grupos.push(grupo = { plantaId, nombre: buscarPlanta(datos, plantaId)?.nombre || plantaId || 'sin planta', renglones: [] });
    grupo.renglones.push(i);
  });
  return grupos;
}

/**
 * Máquina que hace ese trabajo EN ESA PLANTA. El modelo de tiempos habla de las máquinas del
 * taller de Abasto (guillotina, plegadora, banco…); en otra planta se usa la equivalente:
 * la del mismo id, la que dice "reemplazaA", la del mismo tipo o, si no hay, la primera de la planta.
 */
export function maquinaEnPlanta(maquinaId, plantaId, prod, motivo = 'fabrica') {
  const maquinas = prod.maquinas || [];
  const deLaPlanta = maquinas.filter((m) => (m.planta || null) === plantaId);
  if (!plantaId || !deLaPlanta.length) return maquinaId;
  const deposito = deLaPlanta.find((m) => m.tipo === 'deposito');
  if (motivo === 'deposito' && deposito) return deposito.id;
  const original = maquinas.find((m) => m.id === maquinaId);
  const equivalente = deLaPlanta.find((m) => m.id === maquinaId)
    || deLaPlanta.find((m) => (m.reemplazaA || []).includes(maquinaId))
    || (original && deLaPlanta.find((m) => m.tipo === original.tipo));
  return (equivalente || deLaPlanta[0]).id;
}
