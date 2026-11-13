# Catálogo del grupo: HIPER Argentina · Abasto Soluciones · G-TEC

Relevamiento hecho el **13/11/2026** sobre los sitios públicos de las tres empresas, para que el
programa de notas de pedido tenga los productos y servicios de todas.

> **Qué es y qué no es este documento.** Es la lista de lo que cada empresa **publica** en su sitio.
> De otras marcas solo se tomaron **nombres, medidas y presentaciones** (datos), no textos ni imágenes.
> **No se inventó nada**: lo que el sitio no dice quedó marcado **[A CONFIRMAR]** y los productos
> relevados salen en la nota con **"código pendiente"** (el código de facturación lo carga administración).
> Los datos crudos están en `docs/relevamiento/` y de ahí los pasa al programa `herramientas/cargar-relevamiento.js`,
> que también escribe la tabla de abajo (así el documento y el catálogo no pueden decir cosas distintas).

## 1. Cómo se relacionan las empresas

| Empresa | Qué hace | A quién le vende | Dónde | Fuente |
|---|---|---|---|---|
| **HIPER Argentina** ("Metalquímica Hiper S.A." en su sitio) | **Fabrica** zinguería (desde 1989) y perfiles para construcción en seco (planta de perfiles desde 2018) | **Mayorista**: ferreterías, corralones y distribuidores, con logística propia | Av. Japón 2230, Córdoba | https://hiperargentina.com/content/4-sobre-nosotros · https://hiperargentina.com/contacto · InfoNegocios, 28/08/2024: https://infonegocios.info/y-ademas/hiper-argentina-de-una-vision-familiar-a-un-gigante-nacional-en-zingueria-y-construccion-en-seco |
| **Abasto Soluciones** | **Vende al público** zinguería, chapas y materiales de construcción en seco; hace **plegados y cortes a medida** | Público y obras | 9 locales: 7 en Córdoba y 2 en Villa Carlos Paz | https://abastosoluciones.com.ar/content/4-sobre-nosotros · https://abastosoluciones.com.ar/locales |
| **G-TEC** Desarrollos y Servicios Industriales | **Diseña y fabrica** productos metálicos y presta **servicios**: corte láser de chapa y de caño, chorro de agua, plegado CNC, mecanizado y soldadura | Industria | Gral. Manuel Savio 5123, Parque Industrial Ferreyra, Córdoba | https://gtecdesarrollosyservicios.com/ |

**Relación HIPER – Abasto (lo que se pudo comprobar):** en la tienda de Abasto, **95 de los 210 productos
publicados llevan la marca "Hiper Argentina"** y son los mismos de la tienda de HIPER (mismos nombres y mismos
modelos). Otros 18 llevan la marca "Abasto" (chapas, artesanías, plegados y cortes a medida, sombreros
y caños enlozados) y unos 97 son de otras marcas (placas, aislantes, membranas, selladores, masillas y morteros).
Es decir: **HIPER fabrica y vende por mayor; Abasto vende al público lo de HIPER, lo propio y reventa**.

**Lo que NO se pudo comprobar en fuentes públicas** (queda [A CONFIRMAR], ver `PENDIENTES.md`, sección I):

- El **vínculo societario** entre las tres. El artículo de InfoNegocios habla de HIPER y no nombra a Abasto ni a G-TEC.
  El LinkedIn de G-TEC no se pudo abrir (pide iniciar sesión).
- **Dónde se hacen los plegados a medida** de Abasto (¿taller propio o planta de HIPER?). El programa supone un
  "Taller de plegado de Abasto".
- Si el **corte láser** que hoy el programa marca como "tercerizado" lo hace G-TEC.
- Las **canaletas** como producto: ninguna de las dos tiendas las publica (sí sus accesorios: tapas, esquineros,
  rinconeros, soportes y embudos de los modelos Americana, Moldura, Hiper, 1/2 caña y Rectangular). Por eso
  **no se cargaron perfiles nuevos de canaleta**: siguen las plantillas que ya estaban.

## 2. Qué se cargó en el programa

| | Productos o servicios publicados | Ya estaban en el programa | Agregados ahora |
|---|---|---|---|
| HIPER (hiperargentina.com) | 88 fichas (con sus modelos) | 30 | 57 plantillas (una ficha repetida se unió) |
| Abasto, lo que no está en el sitio de HIPER | 123 | 12 | 111 plantillas |
| G-TEC | 9 servicios + fabricación a medida | 0 | 9 servicios + 1 "pieza metalmecánica a medida" |
| **Total del catálogo** | | **51 plantillas de antes** | **178 nuevas = 229** |

Reglas con las que se cargó (para que se pueda revisar):

1. **Un producto con varios modelos es una sola plantilla** y el modelo se elige de una lista (los nombres de los
   modelos son los publicados, tal cual). Así el buscador encuentra "extractor 150" sin llenar la galería de tarjetas.
2. **Quién lo vende** (`empresas`): lo de marca Hiper Argentina lo venden HIPER y Abasto; lo de marca Abasto y la
   reventa, solo Abasto; los servicios, G-TEC. La "pieza especial libre" es de las tres.
3. **Dónde se hace** (`fabricaEn`): planta de HIPER, taller de Abasto, planta de G-TEC o **"tercero"** (otra marca:
   no se fabrica en el grupo).
4. **Stock o a pedido** (`abastecimiento`): los artículos salen de depósito; los plegados a medida, las piezas
   metalmecánicas y los servicios se hacen para la nota.
5. **Sin código inventado:** todo lo relevado sale con "código pendiente". Cuando administración tenga los códigos
   se cargan en `datos/catalogo.json` (campo `codigo` de la plantilla o de cada modelo), sin programar.
6. **Sin dibujo inventado:** artículos, servicios y piezas con plano no llevan dibujo 2D ni 3D.
7. **Cuatro productos que ya estaban** (curva articulada, codo rectangular, ramal y sombrero H) figuran en las webs
   con marca Hiper Argentina, pero el programa los trataba como armados en el taller. **No se cambió** hasta confirmarlo.
8. **G-TEC:** los límites publicados se usan como control al cargar: corte láser hasta 20 mm, láser de caño hasta
   8 mm y Ø 160 mm, chorro de agua hasta 150 mm, soldadura láser hasta 2,5 mm. En **plegado CNC** el sitio dice
   "hasta 12,7 mm" en el título y "6,3 mm" en el texto: el programa avisa a partir de 6,3 y no deja emitir pasando 12,7.

## 3. Tabla completa

Columnas pedidas: producto o servicio · empresa que lo vende · empresa o planta que lo fabrica · si ya estaba
en el programa (y con qué plantilla) · fuente. "Variantes publicadas" es la cantidad de modelos o medidas de la ficha.

<!-- TABLA:inicio -->

### HIPER Argentina (hiperargentina.com): 88 productos o servicios

| Producto o servicio | Categoría en la web | Variantes publicadas | Lo vende | Lo fabrica | ¿Ya estaba en el programa? | Fuente |
|---|---|---|---|---|---|---|
| Rejilla ventilación aprobadas 20 x 20 | Zinguería aprobada para gas y ventilación | 1 | HIPER y Abasto | HIPER | sí (rejilla_ventilacion) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/1-rejilla-ventilacion-aprobadas-20-x-20.html) |
| Rejilla ventilación aprobadas 15 x 15 | Zinguería aprobada para gas y ventilación | 1 | HIPER y Abasto | HIPER | sí (rejilla_ventilacion) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/2-rejilla-ventilacion-aprobadas-15-x-15.html) |
| Rejilla ventilación aprobadas 15 x 30 | Zinguería aprobada para gas y ventilación | 1 | HIPER y Abasto | HIPER | sí (rejilla_ventilacion) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/3-rejilla-ventilacion-aprobadas-15-x-30.html) |
| Rejilla ventilación aprobadas 20 x 20 | Zinguería aprobada para gas y ventilación | 1 | HIPER y Abasto | HIPER | sí (rejilla_ventilacion) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/4-rejilla-ventilacion-aprobadas-20-x-20.html) |
| Curvas abiertas | Zinguería aprobada para gas y ventilación | 8 | HIPER y Abasto | HIPER | no → agregado (h_curvas_abiertas) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/10-curvas-abiertas.html) |
| Curvas herméticas | Zinguería aprobada para gas y ventilación | 8 | HIPER y Abasto | HIPER | no → agregado (h_curvas_hermeticas) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/11-curvas-hermeticas.html) |
| Curvas articuladas | Zinguería aprobada para gas y ventilación | 13 | HIPER y Abasto | HIPER | sí (curva_articulada) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/12-curvas-articuladas.html) |
| Sombreros no reglamentarios | Zinguería aprobada para gas y ventilación | 8 | HIPER y Abasto | HIPER | no → agregado (h_sombreros_no_reglamentarios) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/14-sombreros-no-reglamentarios.html) |
| Sombreretes aprobados | Zinguería aprobada para gas y ventilación | 8 | HIPER y Abasto | HIPER | sí (sombrerete_aprobado) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/15-sombreretes-aprobados.html) |
| Sombreros hache | Zinguería aprobada para gas y ventilación | 8 | HIPER y Abasto | HIPER | sí (sombrero_h) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/16-sombreros-hache.html) |
| Aireador para membrana | Zinguería aprobada para gas y ventilación | — | HIPER y Abasto | HIPER | no → agregado (h_aireador_para_membrana) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/17-aireador-para-membrana.html) |
| Sombreros salamandra / canadienses | Zinguería aprobada para gas y ventilación | 5 | HIPER y Abasto | HIPER | sí (sombrero_canadiense) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/18-sombreros-salamandra-canadienses.html) |
| Reducciones cónicas | Zinguería aprobada para gas y ventilación | 5 | HIPER y Abasto | HIPER | no → agregado (h_reducciones_conicas) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/20-reducciones-conicas.html) |
| Reducciones cilíndricas | Zinguería aprobada para gas y ventilación | 8 | HIPER y Abasto | HIPER | no → agregado (h_reducciones_cilindricas) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/21-reducciones-cilindricas.html) |
| Conductos pasapared para rejilla de vent. | Zinguería aprobada para gas y ventilación | 12 | HIPER y Abasto | HIPER | sí (conducto_pasapared) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/22-conductos-pasapared-para-rejilla-de-vent.html) |
| Puerta marco aprobada | Zinguería aprobada para gas y ventilación | 2 | HIPER y Abasto | HIPER | sí (puerta_marco) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/23-puerta-marco-aprobada.html) |
| Cerradura repuesto conj. puerta marco | Zinguería aprobada para gas y ventilación | — | HIPER y Abasto | HIPER | sí (cerradura_puerta_marco) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/24-cerradura-repuesto-conj-puerta-marco.html) |
| Puerta marco c/gabinete de chapa | Zinguería aprobada para gas y ventilación | 4 | HIPER y Abasto | HIPER | sí (puerta_marco_gabinete) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/25-puerta-marco-c-gabinete-de-chapa.html) |
| Ramales 45º | Zinguería aprobada para gas y ventilación | 4 | HIPER y Abasto | HIPER | sí (ramal) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/26-ramales-45.html) |
| Ramales 90º | Zinguería aprobada para gas y ventilación | 4 | HIPER y Abasto | HIPER | sí (ramal) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/27-ramales-90.html) |
| Extractores eólicos | Zinguería para techos y plegados especiales | 3 | HIPER y Abasto | HIPER | no → agregado (h_extractores_eolicos) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/28-extractores-eolicos.html) |
| Extractores eólicos | Zinguería para techos y plegados especiales | 2 | HIPER y Abasto | HIPER | no → agregado (h_extractores_eolicos, misma plantilla) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/29-extractores-eolicos.html) |
| Babeta sinusoidal | Zinguería para techos y plegados especiales | 1 | HIPER y Abasto | HIPER | sí (babeta_sobre_chapa_sinusoidal) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/32-babeta-sinusoidal.html) |
| Babeta trapezoidal | Zinguería para techos y plegados especiales | 1 | HIPER y Abasto | HIPER | sí (babeta_sobre_chapa_trapezoidal) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/33-babeta-trapezoidal.html) |
| Adaptación 5x10 a 100 | Zinguería para techos y plegados especiales | 1 | HIPER y Abasto | HIPER | no → agregado (h_adaptacion_5x10_a_100) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/46-adaptacion-5x10-a-100.html) |
| Cuchara aljibe | Zinguería para techos y plegados especiales | 1 | HIPER y Abasto | HIPER | no → agregado (h_cuchara_aljibe) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/47-cuchara-aljibe.html) |
| Codo rectangular plano 90º | Zinguería para techos y plegados especiales | 2 | HIPER y Abasto | HIPER | sí (codo_rectangular) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/49-codo-rectangular-plano-90.html) |
| Codo rectangular plano vertical 90º | Zinguería para techos y plegados especiales | 1 | HIPER y Abasto | HIPER | sí (codo_rectangular) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/51-codo-rectangular-plano-vertical-90.html) |
| Codo soldado 45º | Zinguería para techos y plegados especiales | 2 | HIPER y Abasto | HIPER | no → agregado (h_codo_soldado_45) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/52-codo-soldado-45.html) |
| Codo rectangular vertical 90º | Zinguería para techos y plegados especiales | 2 | HIPER y Abasto | HIPER | sí (codo_rectangular) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/55-codo-rectangular-vertical-90.html) |
| Rinconero 1/2 caña | Zinguería para techos y plegados especiales | 3 | HIPER y Abasto | HIPER | no → agregado (h_rinconero_1_2_cana) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/58-rinconero-1-2-cana.html) |
| Esquinero 1/2 caña | Zinguería para techos y plegados especiales | 3 | HIPER y Abasto | HIPER | no → agregado (h_esquinero_1_2_cana) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/59-esquinero-1-2-cana.html) |
| Intermedia 1/2 caña | Zinguería para techos y plegados especiales | 3 | HIPER y Abasto | HIPER | no → agregado (h_intermedia_1_2_cana) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/60-intermedia-1-2-cana.html) |
| Esquinero moldura | Zinguería para techos y plegados especiales | 1 | HIPER y Abasto | HIPER | no → agregado (h_esquinero_moldura) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/61-esquinero-moldura.html) |
| Tapa rectangular | Zinguería para techos y plegados especiales | 4 | HIPER y Abasto | HIPER | no → agregado (h_tapa_rectangular) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/62-tapa-rectangular.html) |
| Tapa con boqueta rectangular | Zinguería para techos y plegados especiales | 4 | HIPER y Abasto | HIPER | no → agregado (h_tapa_con_boqueta_rectangular) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/63-tapa-con-boqueta-rectangular.html) |
| Tapa americana | Zinguería para techos y plegados especiales | 2 | HIPER y Abasto | HIPER | no → agregado (h_tapa_americana) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/67-tapa-americana.html) |
| Tapa con boqueta americana | Zinguería para techos y plegados especiales | 2 | HIPER y Abasto | HIPER | no → agregado (h_tapa_con_boqueta_americana) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/68-tapa-con-boqueta-americana.html) |
| Intermedia americana | Zinguería para techos y plegados especiales | 1 | HIPER y Abasto | HIPER | no → agregado (h_intermedia_americana) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/69-intermedia-americana.html) |
| Rinconero americana | Zinguería para techos y plegados especiales | 1 | HIPER y Abasto | HIPER | no → agregado (h_rinconero_americana) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/70-rinconero-americana.html) |
| Esquinero americana | Zinguería para techos y plegados especiales | 1 | HIPER y Abasto | HIPER | sí (std_esquinero_americana) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/71-esquinero-americana.html) |
| Tapa con boqueta Hiper | Zinguería para techos y plegados especiales | 2 | HIPER y Abasto | HIPER | no → agregado (h_tapa_con_boqueta_hiper) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/72-tapa-con-boqueta-hiper.html) |
| Tapa Hiper | Zinguería para techos y plegados especiales | 2 | HIPER y Abasto | HIPER | no → agregado (h_tapa_hiper) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/73-tapa-hiper.html) |
| Tapa con boqueta moldura | Zinguería para techos y plegados especiales | 2 | HIPER y Abasto | HIPER | no → agregado (h_tapa_con_boqueta_moldura) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/77-tapa-con-boqueta-moldura.html) |
| Tapa moldura | Zinguería para techos y plegados especiales | 2 | HIPER y Abasto | HIPER | no → agregado (h_tapa_moldura) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/78-tapa-moldura.html) |
| Cenefa punta de lis (2 m) | Zinguería para techos y plegados especiales | — | HIPER y Abasto | HIPER | sí (cenefa_punta_lis) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/81-cenefa-punta-de-lis-2-mt.html) |
| Cenefa flor de lis (2 m) | Zinguería para techos y plegados especiales | — | HIPER y Abasto | HIPER | sí (cenefa_flor_lis) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/82-cenefa-flor-de-lis-2-mt.html) |
| Cenefa piña (2 m) | Zinguería para techos y plegados especiales | — | HIPER y Abasto | HIPER | sí (cenefa_pina) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/83-cenefa-pina-2-mt.html) |
| Embudo colector moldura | Zinguería para techos y plegados especiales | — | HIPER y Abasto | HIPER | sí (embudo_colector_moldura) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/84-embudo-colector-moldura.html) |
| Embudo colector recto 5 x 10 | Zinguería para techos y plegados especiales | — | HIPER y Abasto | HIPER | sí (colector_recto) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/85-embudo-colector-recto-5-x-10.html) |
| Soporte canaleta americana | Zinguería para techos y plegados especiales | 2 | HIPER y Abasto | HIPER | sí (soporte_canaleta) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/88-soporte-canaleta-americana.html) |
| Soporte canaleta Hiper | Zinguería para techos y plegados especiales | 2 | HIPER y Abasto | HIPER | sí (soporte_canaleta) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/89-soporte-canaleta-hiper.html) |
| Soporte canaleta moldura | Zinguería para techos y plegados especiales | 2 | HIPER y Abasto | HIPER | sí (soporte_canaleta) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/90-soporte-canaleta-moldura.html) |
| Soporte para caño rectangular | Zinguería para techos y plegados especiales | 3 | HIPER y Abasto | HIPER | sí (soporte_cano_rectangular) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/91-soporte-para-cano-rectangular.html) |
| Bandas selladoras compriband | Zinguería para techos y plegados especiales | 3 | HIPER y Abasto | HIPER | sí (compriband) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/92-bandas-selladoras-compriband.html) |
| Pasatechos (sellos herméticos) | Zinguería para techos y plegados especiales | 12 | HIPER y Abasto | HIPER | no → agregado (h_pasatechos_sellos_hermeticos) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/95-pasatechos-sellos-hermeticos.html) |
| Tapa cámara chapa reforzada | Accesorios sanitarios | 7 | HIPER y Abasto | HIPER | no → agregado (h_tapa_camara_chapa_reforzada) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/93-tapa-camara-chapa-reforzada.html) |
| Hiperflex | Accesorios sanitarios | 15 | HIPER y Abasto | HIPER | no → agregado (h_hiperflex) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/94-hiperflex.html) |
| Rejas hierro fundido | Accesorios sanitarios | 4 | HIPER y Abasto | HIPER | no → agregado (h_rejas_hierro_fundido) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/96-rejas-hierro-fundido.html) |
| Reja de plástica | Accesorios sanitarios | 2 | HIPER y Abasto | HIPER | no → agregado (h_reja_de_plastica) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/97-reja-de-plastica.html) |
| Grampa 1/2 omega | Accesorios sanitarios | 6 | HIPER y Abasto | HIPER | no → agregado (h_grampa_1_2_omega) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/98-grampa-1-2-omega.html) |
| Grampa amurar | Accesorios sanitarios | 10 | HIPER y Abasto | HIPER | no → agregado (h_grampa_amurar) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/99-grampa-amurar.html) |
| Grampa omega | Accesorios sanitarios | 17 | HIPER y Abasto | HIPER | no → agregado (h_grampa_omega) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/100-grampa-omega.html) |
| Soportes lavatorios y termotanque | Accesorios sanitarios | 4 | HIPER y Abasto | HIPER | no → agregado (h_soportes_lavatorios_y_termotanque) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/101-soportes-lavatorios-y-termotanque.html) |
| Clavo gancho x KG. | Accesorios sanitarios | — | HIPER y Abasto | HIPER | no → agregado (h_clavo_gancho_x_kg) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/102-clavo-gancho-x-kg.html) |
| Fleje perforado chapa 0.7 x 30 mts. | Accesorios sanitarios | — | HIPER y Abasto | HIPER | no → agregado (h_fleje_perforado_chapa_0_7_x_30_mts) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/103-fleje-perforado-chapa-07-x-30-mts.html) |
| Torniquetes | Accesorios sanitarios | 2 | HIPER y Abasto | HIPER | no → agregado (h_torniquetes) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/104-torniquetes.html) |
| Torn bronce | Accesorios sanitarios | 3 | HIPER y Abasto | HIPER | no → agregado (h_torn_bronce) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/105-torn-bronce.html) |
| Plancheta | Calefacción y fogoneros | 1 | HIPER y Abasto | HIPER | no → agregado (h_plancheta) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/106-plancheta.html) |
| Fogonero mediano + parrilla | Calefacción y fogoneros | 1 | HIPER y Abasto | HIPER | no → agregado (h_fogonero_mediano_parrilla) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/107-fogonero-mediano-parrilla.html) |
| Estaca mediana | Calefacción y fogoneros | 1 | HIPER y Abasto | HIPER | no → agregado (h_estaca_mediana) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/108-estaca-mediana.html) |
| Fogonero grande | Calefacción y fogoneros | 1 | HIPER y Abasto | HIPER | no → agregado (h_fogonero_grande) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/109-fogonero-grande.html) |
| Estaca grande | Calefacción y fogoneros | 1 | HIPER y Abasto | HIPER | no → agregado (h_estaca_grande) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/110-estaca-grande.html) |
| Parrilla grande con soportes | Calefacción y fogoneros | 1 | HIPER y Abasto | HIPER | no → agregado (h_parrilla_grande_con_soportes) | [ficha](https://hiperargentina.com/zingueria-y-accesorios-sanitarios/111-parrilla-grande-con-soportes.html) |
| Montante | Perfiles Drywall | 5 | HIPER y Abasto | HIPER | no → agregado (h_montante) | [ficha](https://hiperargentina.com/perfiles-para-construccion-en-seco/112-montante.html) |
| Solera | Perfiles Drywall | 5 | HIPER y Abasto | HIPER | no → agregado (h_solera) | [ficha](https://hiperargentina.com/perfiles-para-construccion-en-seco/113-solera.html) |
| Omega | Perfiles Drywall | 1 | HIPER y Abasto | HIPER | no → agregado (h_omega) | [ficha](https://hiperargentina.com/perfiles-para-construccion-en-seco/114-omega.html) |
| Buña perimetral | Perfiles Drywall | 1 | HIPER y Abasto | HIPER | no → agregado (h_buna_perimetral) | [ficha](https://hiperargentina.com/perfiles-para-construccion-en-seco/115-buna-perimetral.html) |
| Cantonera | Perfiles Drywall | 1 | HIPER y Abasto | HIPER | no → agregado (h_cantonera) | [ficha](https://hiperargentina.com/perfiles-para-construccion-en-seco/116-cantonera.html) |
| Ángulo de ajuste | Perfiles Drywall | 1 | HIPER y Abasto | HIPER | no → agregado (h_angulo_de_ajuste) | [ficha](https://hiperargentina.com/perfiles-para-construccion-en-seco/117-angulo-de-ajuste.html) |
| Perfiles PGC | Perfiles Steel Frame | 10 | HIPER y Abasto | HIPER | no → agregado (h_perfiles_pgc) | [ficha](https://hiperargentina.com/perfiles-para-construccion-en-seco/118-perfiles-pgc.html) |
| Perfiles PGU | Perfiles Steel Frame | 7 | HIPER y Abasto | HIPER | no → agregado (h_perfiles_pgu) | [ficha](https://hiperargentina.com/perfiles-para-construccion-en-seco/119-perfiles-pgu.html) |
| Anclaje steel | Accesorios para Steel Frame | 1 | HIPER y Abasto | HIPER | no → agregado (h_anclaje_steel) | [ficha](https://hiperargentina.com/perfiles-para-construccion-en-seco/121-anclaje-steel.html) |
| Cartela | Accesorios para Steel Frame | 2 | HIPER y Abasto | HIPER | no → agregado (h_cartela) | [ficha](https://hiperargentina.com/perfiles-para-construccion-en-seco/122-cartela.html) |
| Soporte L chico | Accesorios para Steel Frame | 1 | HIPER y Abasto | HIPER | no → agregado (h_soporte_l_chico) | [ficha](https://hiperargentina.com/perfiles-para-construccion-en-seco/123-soporte-l-chico.html) |
| Soporte L grande | Accesorios para Steel Frame | 1 | HIPER y Abasto | HIPER | no → agregado (h_soporte_l_grande) | [ficha](https://hiperargentina.com/perfiles-para-construccion-en-seco/124-soporte-l-grande.html) |
| Tensor cruz de San Andrés | Accesorios para Steel Frame | 1 | HIPER y Abasto | HIPER | no → agregado (h_tensor_cruz_de_san_andres) | [ficha](https://hiperargentina.com/perfiles-para-construccion-en-seco/125-tensor-cruz-de-san-andres.html) |
| Conector cabio | Accesorios para Steel Frame | 1 | HIPER y Abasto | HIPER | no → agregado (h_conector_cabio) | [ficha](https://hiperargentina.com/perfiles-para-construccion-en-seco/127-conector-cabio.html) |

### Abasto Soluciones (abastosoluciones.com.ar), lo que no está en el sitio de HIPER: 123 productos o servicios

| Producto o servicio | Categoría en la web | Variantes publicadas | Lo vende | Lo fabrica | ¿Ya estaba en el programa? | Fuente |
|---|---|---|---|---|---|---|
| BASES EXTRACTORES EÓLICOS | Zinguería para techos | 3 | Abasto (marca Hiper Argentina) | HIPER | no → agregado (h_bases_extractores_eolicos) | [ficha](https://abastosoluciones.com.ar/zingueria/30-bases-extractores-eolicos.html) |
| Balde | Artesanías | — | Abasto | Abasto (marca propia) [A CONFIRMAR dónde] | sí (balde) | [ficha](https://abastosoluciones.com.ar/zingueria/222-balde.html) |
| Palangana | Artesanías | — | Abasto | Abasto (marca propia) [A CONFIRMAR dónde] | sí (palangana) | [ficha](https://abastosoluciones.com.ar/zingueria/223-palangana.html) |
| Regadera | Artesanías | — | Abasto | Abasto (marca propia) [A CONFIRMAR dónde] | sí (regadera) | [ficha](https://abastosoluciones.com.ar/zingueria/224-regadera.html) |
| Espina perimetral | Artesanías | — | Abasto | Abasto (marca propia) [A CONFIRMAR dónde] | no → agregado (ab_espina_perimetral) | [ficha](https://abastosoluciones.com.ar/zingueria/225-espina-perimetral.html) |
| CAÑOS CHAPA N°30 | Caños, codos y curvas | 8 | Abasto (marca Hiper Argentina) | HIPER | en parte (cano, a medida) → agregado (h_canos_chapa_n_30) | [ficha](https://abastosoluciones.com.ar/zingueria/5-canos-chapa-n30.html) |
| CAÑOS X 2 / 3 MTS. SOLDADOS | Caños, codos y curvas | 4 | Abasto (marca Hiper Argentina) | HIPER | en parte (cano, a medida) → agregado (h_canos_x_2_3_mts_soldados) | [ficha](https://abastosoluciones.com.ar/zingueria/6-canos-x-2-3-mts-soldados.html) |
| CAÑOS CHAPA N°25 | Caños, codos y curvas | 12 | Abasto (marca Hiper Argentina) | HIPER | en parte (cano, a medida) → agregado (h_canos_chapa_n_25) | [ficha](https://abastosoluciones.com.ar/zingueria/7-canos-chapa-n25.html) |
| CAÑOS RECTANGULARES | Caños, codos y curvas | 3 | Abasto (marca Hiper Argentina) | HIPER | en parte (cano, a medida) → agregado (h_canos_rectangulares) | [ficha](https://abastosoluciones.com.ar/zingueria/8-canos-rectangulares.html) |
| CAÑOS 1/2 METRO | Caños, codos y curvas | 4 | Abasto (marca Hiper Argentina) | HIPER | en parte (cano, a medida) → agregado (h_canos_1_2_metro) | [ficha](https://abastosoluciones.com.ar/zingueria/9-canos-1-2-metro.html) |
| CAÑOS ACERO INOXIDABLE 0,5 MM. | Caños, codos y curvas | 4 | Abasto (marca Hiper Argentina) | HIPER | en parte (cano, a medida) → agregado (h_canos_acero_inoxidable_0_5_mm) | [ficha](https://abastosoluciones.com.ar/zingueria/19-canos-acero-inoxidable-05-mm.html) |
| Caño Enlozado | Caños, codos y curvas | — | Abasto | Abasto (marca propia) [A CONFIRMAR dónde] | sí (cano_enlozado) | [ficha](https://abastosoluciones.com.ar/zingueria/234-cano-enlozado.html) |
| Codo Enlozado | Caños, codos y curvas | — | Abasto | Abasto (marca propia) [A CONFIRMAR dónde] | no → agregado (ab_codo_enlozado) | [ficha](https://abastosoluciones.com.ar/zingueria/235-codo-enlozado.html) |
| Babetas | Plegados y cortes | — | Abasto | Abasto (marca propia) [A CONFIRMAR dónde] | sí (babeta_l_15) | [ficha](https://abastosoluciones.com.ar/zingueria/226-babetas.html) |
| Cumbreras | Plegados y cortes | — | Abasto | Abasto (marca propia) [A CONFIRMAR dónde] | sí (cumbrera_lisa_15) | [ficha](https://abastosoluciones.com.ar/zingueria/227-cumbreras.html) |
| 1/2 Cumbrera | Plegados y cortes | — | Abasto | Abasto (marca propia) [A CONFIRMAR dónde] | sí (media_cumbrera) | [ficha](https://abastosoluciones.com.ar/zingueria/228-1-2-cumbrera.html) |
| Limaholla | Plegados y cortes | — | Abasto | Abasto (marca propia) [A CONFIRMAR dónde] | sí (limahoya) | [ficha](https://abastosoluciones.com.ar/zingueria/229-limaholla.html) |
| Troneras | Plegados y cortes | — | Abasto | Abasto (marca propia) [A CONFIRMAR dónde] | sí (tronera) | [ficha](https://abastosoluciones.com.ar/zingueria/230-troneras.html) |
| Boquetas | Plegados y cortes | — | Abasto | Abasto (marca propia) [A CONFIRMAR dónde] | sí (boqueta_suelta) | [ficha](https://abastosoluciones.com.ar/zingueria/231-boquetas.html) |
| Canadiense | Sombreros | — | Abasto | Abasto (marca propia) [A CONFIRMAR dónde] | sí (sombrero_canadiense) | [ficha](https://abastosoluciones.com.ar/zingueria/232-canadiense.html) |
| Tipo Spiro | Sombreros | — | Abasto | Abasto (marca propia) [A CONFIRMAR dónde] | sí (sombrero_spiro) | [ficha](https://abastosoluciones.com.ar/zingueria/233-tipo-spiro.html) |
| CODO SOLDADO 90º | Accesorios | 2 | Abasto (marca Hiper Argentina) | HIPER | no → agregado (h_codo_soldado_90) | [ficha](https://abastosoluciones.com.ar/zingueria/53-codo-soldado-90.html) |
| Placa Estandar | Placas | — | Abasto | tercero (reventa) | no → agregado (ab_placa_estandar) | [ficha](https://abastosoluciones.com.ar/construccion/135-placa-estandar.html) |
| Placa Resistente al Fuego | Placas | — | Abasto | tercero (reventa) | no → agregado (ab_placa_resistente_al_fuego) | [ficha](https://abastosoluciones.com.ar/construccion/136-placa-resistente-al-fuego.html) |
| Placa Ciel | Placas | — | Abasto | tercero (reventa) | no → agregado (ab_placa_ciel) | [ficha](https://abastosoluciones.com.ar/construccion/137-placa-ciel.html) |
| Placa Anti Humedas | Placas | — | Abasto | tercero (reventa) | no → agregado (ab_placa_anti_humedas) | [ficha](https://abastosoluciones.com.ar/construccion/138-placa-anti-humedas.html) |
| Placa Resistente a Humedad | Placas | — | Abasto | tercero (reventa) | no → agregado (ab_placa_resistente_a_humedad) | [ficha](https://abastosoluciones.com.ar/placas/139-placa-resistente-a-humedad.html) |
| Placa Uso Múltiple | Placas | — | Abasto | tercero (reventa) | no → agregado (ab_placa_uso_multiple) | [ficha](https://abastosoluciones.com.ar/construccion/191-placa-uso-multiple.html) |
| Paredes Exteriores | Placas | — | Abasto | tercero (reventa) | no → agregado (ab_paredes_exteriores) | [ficha](https://abastosoluciones.com.ar/construccion/192-paredes-exteriores.html) |
| Entrepisos | Placas | — | Abasto | tercero (reventa) | no → agregado (ab_entrepisos) | [ficha](https://abastosoluciones.com.ar/construccion/193-entrepisos.html) |
| Multicapa Clavable | Placas | — | Abasto | tercero (reventa) | no → agregado (ab_multicapa_clavable) | [ficha](https://abastosoluciones.com.ar/construccion/194-multicapa-clavable.html) |
| Tablero Estructural Certificado | Placas | — | Abasto | tercero (reventa) | no → agregado (ab_tablero_estructural_certificado) | [ficha](https://abastosoluciones.com.ar/construccion/261-tablero-estructural-certificcado.html) |
| Aislante Acustiver | Aislantes | — | Abasto | tercero (reventa) | no → agregado (ab_aislante_acustiver) | [ficha](https://abastosoluciones.com.ar/construccion/155-aislante-acustiver.html) |
| Aislante Bajo Teja | Aislantes | — | Abasto | tercero (reventa) | no → agregado (ab_aislante_bajo_teja) | [ficha](https://abastosoluciones.com.ar/construccion/156-aislante-bajo-teja.html) |
| Aislante Fieltro Liviano | Aislantes | — | Abasto | tercero (reventa) | no → agregado (ab_aislante_fieltro_liviano) | [ficha](https://abastosoluciones.com.ar/construccion/157-aislante-fieltro-liviano.html) |
| Aislante Fieltro Fachada | Aislantes | — | Abasto | tercero (reventa) | no → agregado (ab_aislante_fieltro_fachada) | [ficha](https://abastosoluciones.com.ar/construccion/158-aislante-fieltro-fachada.html) |
| Aislante Fieltro Aluminio | Aislantes | — | Abasto | tercero (reventa) | no → agregado (ab_aislante_fieltro_aluminio) | [ficha](https://abastosoluciones.com.ar/construccion/159-aislante-fieltro-aluminio.html) |
| Aislante Fieltro Poli | Aislantes | — | Abasto | tercero (reventa) | no → agregado (ab_aislante_fieltro_poli) | [ficha](https://abastosoluciones.com.ar/construccion/160-aislante-fieltro-poli.html) |
| Aislante Rolac Plata Cub | Aislantes | — | Abasto | tercero (reventa) | no → agregado (ab_aislante_rolac_plata_cub) | [ficha](https://abastosoluciones.com.ar/construccion/161-aislante-rolac-plata-cub.html) |
| Aisante Hidrorepelente | Aislantes | — | Abasto | tercero (reventa) | no → agregado (ab_aisante_hidrorepelente) | [ficha](https://abastosoluciones.com.ar/construccion/162-aisante-hidrorepelente.html) |
| Banda Acústica | Aislantes | — | Abasto | tercero (reventa) | no → agregado (ab_banda_acustica) | [ficha](https://abastosoluciones.com.ar/construccion/163-banda-acustica.html) |
| Cil de Polietileno | Aislantes | — | Abasto | tercero (reventa) | no → agregado (ab_cil_de_polietileno) | [ficha](https://abastosoluciones.com.ar/construccion/164-cil-de-polietileno.html) |
| Doble Aluminio con Red | Aislantes | — | Abasto | tercero (reventa) | no → agregado (ab_doble_aluminio_con_red) | [ficha](https://abastosoluciones.com.ar/construccion/165-doble-aluminio-con-red.html) |
| Rufi Doble Aluminio | Aislantes | — | Abasto | tercero (reventa) | no → agregado (ab_rufi_doble_aluminio) | [ficha](https://abastosoluciones.com.ar/construccion/166-rufi-doble-aluminio.html) |
| Rufi Aluminio | Aislantes | — | Abasto | tercero (reventa) | no → agregado (ab_rufi_aluminio) | [ficha](https://abastosoluciones.com.ar/construccion/167-rufi-aluminio.html) |
| Red Plástica | Aislantes | — | Abasto | tercero (reventa) | no → agregado (ab_red_plastica) | [ficha](https://abastosoluciones.com.ar/construccion/168-red-plastica.html) |
| Akustar | Aislantes | — | Abasto | tercero (reventa) | no → agregado (ab_akustar) | [ficha](https://abastosoluciones.com.ar/construccion/169-akustar.html) |
| Curtain Wall | Aislantes | — | Abasto | tercero (reventa) | no → agregado (ab_curtain_wall) | [ficha](https://abastosoluciones.com.ar/construccion/170-curtain-wall.html) |
| Iso Acustic | Aislantes | — | Abasto | tercero (reventa) | no → agregado (ab_iso_acustic) | [ficha](https://abastosoluciones.com.ar/construccion/171-iso-acustic.html) |
| Paneletics | Aislantes | — | Abasto | tercero (reventa) | no → agregado (ab_paneletics) | [ficha](https://abastosoluciones.com.ar/construccion/172-paneletics.html) |
| Panel Fachada | Aislantes | — | Abasto | tercero (reventa) | no → agregado (ab_panel_fachada) | [ficha](https://abastosoluciones.com.ar/construccion/173-panel-fachada.html) |
| Panel Fachada VN | Aislantes | — | Abasto | tercero (reventa) | no → agregado (ab_panel_fachada_vn) | [ficha](https://abastosoluciones.com.ar/construccion/174-panel-fachada-vn.html) |
| Pintura Asfáltica | Impermeabilizantes | — | Abasto | tercero (reventa) | no → agregado (ab_pintura_asfaltica) | [ficha](https://abastosoluciones.com.ar/construccion/195-pintura-asfaltica.html) |
| Emulsión Asfáltica | Impermeabilizantes | — | Abasto | tercero (reventa) | no → agregado (ab_emulsion_asfaltica) | [ficha](https://abastosoluciones.com.ar/construccion/196-emulsion-asfaltica.html) |
| GeoTrans | Impermeabilizantes | — | Abasto | tercero (reventa) | no → agregado (ab_geotrans) | [ficha](https://abastosoluciones.com.ar/construccion/197-geotrans.html) |
| Membrana Techos | Impermeabilizantes | — | Abasto | tercero (reventa) | no → agregado (ab_membrana_techos) | [ficha](https://abastosoluciones.com.ar/construccion/198-membrana-techos.html) |
| Techos L | Impermeabilizantes | — | Abasto | tercero (reventa) | no → agregado (ab_techos_l) | [ficha](https://abastosoluciones.com.ar/construccion/199-techos-l.html) |
| Techos F | Impermeabilizantes | — | Abasto | tercero (reventa) | no → agregado (ab_techos_f) | [ficha](https://abastosoluciones.com.ar/construccion/200-techos-f.html) |
| Asfáltica | Impermeabilizantes | — | Abasto | tercero (reventa) | no → agregado (ab_asfaltica) | [ficha](https://abastosoluciones.com.ar/construccion/201-asfaltica.html) |
| Sikalastic 612 | Impermeabilizantes | — | Abasto | tercero (reventa) | no → agregado (ab_sikalastic_612) | [ficha](https://abastosoluciones.com.ar/construccion/202-sikalastic-612.html) |
| Sikalastic 560 | Impermeabilizantes | — | Abasto | tercero (reventa) | no → agregado (ab_sikalastic_560) | [ficha](https://abastosoluciones.com.ar/construccion/203-sikalastic-560.html) |
| SikaFill Fibrado | Impermeabilizantes | — | Abasto | tercero (reventa) | no → agregado (ab_sikafill_fibrado) | [ficha](https://abastosoluciones.com.ar/construccion/204-sikafill-fibrado.html) |
| SikaFill Techos | Impermeabilizantes | — | Abasto | tercero (reventa) | no → agregado (ab_sikafill_techos) | [ficha](https://abastosoluciones.com.ar/construccion/205-sikafill-techos.html) |
| Tapa Goteras | Impermeabilizantes | — | Abasto | tercero (reventa) | no → agregado (ab_tapa_goteras) | [ficha](https://abastosoluciones.com.ar/construccion/206-tapa-goteras.html) |
| Sika Ladrillos | Impermeabilizantes | — | Abasto | tercero (reventa) | no → agregado (ab_sika_ladrillos) | [ficha](https://abastosoluciones.com.ar/construccion/207-sika-ladrillos.html) |
| Sika Frentes | Impermeabilizantes | — | Abasto | tercero (reventa) | no → agregado (ab_sika_frentes) | [ficha](https://abastosoluciones.com.ar/construccion/208-sika-frentes.html) |
| Sikacryl | Selladores | — | Abasto | tercero (reventa) | no → agregado (ab_sikacryl) | [ficha](https://abastosoluciones.com.ar/construccion/209-sikacryl.html) |
| Sikasil E | Selladores | — | Abasto | tercero (reventa) | no → agregado (ab_sikasil_e) | [ficha](https://abastosoluciones.com.ar/construccion/210-sikasil-e.html) |
| Sika Sanisil | Selladores | — | Abasto | tercero (reventa) | no → agregado (ab_sika_sanisil) | [ficha](https://abastosoluciones.com.ar/construccion/211-sika-sanisil.html) |
| Sikasil C | Selladores | — | Abasto | tercero (reventa) | no → agregado (ab_sikasil_c) | [ficha](https://abastosoluciones.com.ar/construccion/212-sikasil-c.html) |
| Sikaflex A1 Plus | Selladores | — | Abasto | tercero (reventa) | no → agregado (ab_sikaflex_a1_plus) | [ficha](https://abastosoluciones.com.ar/construccion/213-sikaflex-a1-plus.html) |
| Sikaflex 11 FC | Selladores | — | Abasto | tercero (reventa) | no → agregado (ab_sikaflex_11_fc) | [ficha](https://abastosoluciones.com.ar/construccion/214-sikaflex-11-fc.html) |
| Sikabond | Selladores | — | Abasto | tercero (reventa) | no → agregado (ab_sikabond) | [ficha](https://abastosoluciones.com.ar/construccion/215-sikabond.html) |
| Sikaflex Crystal | Selladores | — | Abasto | tercero (reventa) | no → agregado (ab_sikaflex_crystal) | [ficha](https://abastosoluciones.com.ar/construccion/216-sikaflex-crystal.html) |
| SikaBoom | Selladores | — | Abasto | tercero (reventa) | no → agregado (ab_sikaboom) | [ficha](https://abastosoluciones.com.ar/construccion/217-sikaboom.html) |
| Sikaflex 501 | Selladores | — | Abasto | tercero (reventa) | no → agregado (ab_sikaflex_501) | [ficha](https://abastosoluciones.com.ar/construccion/218-sikaflex-501.html) |
| Anchorfix 2 | Adhesivos | — | Abasto | tercero (reventa) | no → agregado (ab_anchorfix_2) | [ficha](https://abastosoluciones.com.ar/construccion/219-anchorfix-2.html) |
| Sikadur 31 | Adhesivos | — | Abasto | tercero (reventa) | no → agregado (ab_sikadur_31) | [ficha](https://abastosoluciones.com.ar/construccion/220-sikadur-31.html) |
| Sikadur 32 Gel | Adhesivos | — | Abasto | tercero (reventa) | no → agregado (ab_sikadur_32_gel) | [ficha](https://abastosoluciones.com.ar/construccion/221-sikadur-32-gel.html) |
| Masilla Lista para Usar | Masillas | — | Abasto | tercero (reventa) | no → agregado (ab_masilla_lista_para_usar) | [ficha](https://abastosoluciones.com.ar/construccion/140-masilla-lista-para-usar.html) |
| Masilla Secado Rápido | Masillas | — | Abasto | tercero (reventa) | no → agregado (ab_masilla_secado_rapido) | [ficha](https://abastosoluciones.com.ar/construccion/141-masilla-secado-rapido.html) |
| Masilla Semi Cubiertos | Masillas | — | Abasto | tercero (reventa) | no → agregado (ab_masilla_semi_cubiertos) | [ficha](https://abastosoluciones.com.ar/construccion/142-masilla-semi-cubiertos.html) |
| Masilla Anti Humedad | Masillas | — | Abasto | tercero (reventa) | no → agregado (ab_masilla_anti_humedad) | [ficha](https://abastosoluciones.com.ar/construccion/143-masilla-anti-humedad.html) |
| Masilla Superboard | Masillas | — | Abasto | tercero (reventa) | no → agregado (ab_masilla_superboard) | [ficha](https://abastosoluciones.com.ar/construccion/144-masilla-superboard.html) |
| Membrana Megafacil | Membranas | — | Abasto | tercero (reventa) | no → agregado (ab_membrana_megafacil) | [ficha](https://abastosoluciones.com.ar/construccion/145-membrana-megafacil.html) |
| Membrana No Crack | Membranas | — | Abasto | tercero (reventa) | no → agregado (ab_membrana_no_crack) | [ficha](https://abastosoluciones.com.ar/construccion/146-membrana-no-crack.html) |
| Membrana Megalum | Membranas | — | Abasto | tercero (reventa) | no → agregado (ab_membrana_megalum) | [ficha](https://abastosoluciones.com.ar/construccion/147-membrana-megalum.html) |
| Membrana Geotrans | Membranas | — | Abasto | tercero (reventa) | no → agregado (ab_membrana_geotrans) | [ficha](https://abastosoluciones.com.ar/construccion/148-membrana-geotrans.html) |
| Membraba GeoMax | Membranas | — | Abasto | tercero (reventa) | no → agregado (ab_membraba_geomax) | [ficha](https://abastosoluciones.com.ar/construccion/150-membraba-geomax.html) |
| Membraba Auminio MGX | Membranas | — | Abasto | tercero (reventa) | no → agregado (ab_membraba_auminio_mgx) | [ficha](https://abastosoluciones.com.ar/construccion/151-membraba-auminio-mgx.html) |
| Weber ALU | Membranas | — | Abasto | tercero (reventa) | no → agregado (ab_weber_alu) | [ficha](https://abastosoluciones.com.ar/construccion/152-weber-alu.html) |
| Weber ALU Plus | Membranas | — | Abasto | tercero (reventa) | no → agregado (ab_weber_alu_plus) | [ficha](https://abastosoluciones.com.ar/construccion/153-weber-alu-plus.html) |
| Weber ALU Max | Membranas | — | Abasto | tercero (reventa) | no → agregado (ab_weber_alu_max) | [ficha](https://abastosoluciones.com.ar/construccion/154-weber-alu-max.html) |
| Sika Antisol | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_sika_antisol) | [ficha](https://abastosoluciones.com.ar/construccion/236-sika-antisol.html) |
| Sikasim | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_sikasim) | [ficha](https://abastosoluciones.com.ar/construccion/237-sikasim.html) |
| Sikalatex | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_sikalatex) | [ficha](https://abastosoluciones.com.ar/construccion/238-sikalatex.html) |
| Sika Grout 212 | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_sika_grout_212) | [ficha](https://abastosoluciones.com.ar/construccion/239-sika-grout-212.html) |
| Sika Molotop 620 | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_sika_molotop_620) | [ficha](https://abastosoluciones.com.ar/construccion/240-sika-molotop-620.html) |
| Sika 1 | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_sika_1) | [ficha](https://abastosoluciones.com.ar/construccion/241-sika-1.html) |
| Sika Intertol | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_sika_intertol) | [ficha](https://abastosoluciones.com.ar/construccion/242-sika-intertol.html) |
| Weber Basic | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_weber_basic) | [ficha](https://abastosoluciones.com.ar/construccion/243-weber-basic.html) |
| Weber Gris | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_weber_gris) | [ficha](https://abastosoluciones.com.ar/construccion/244-weber-gris.html) |
| Weber Pro | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_weber_pro) | [ficha](https://abastosoluciones.com.ar/construccion/245-weber-pro.html) |
| Weber Impermeable | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_weber_impermeable) | [ficha](https://abastosoluciones.com.ar/construccion/246-weber-impermeable.html) |
| Weber Fino | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_weber_fino) | [ficha](https://abastosoluciones.com.ar/construccion/247-weber-fino.html) |
| Weber Fino Interior | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_weber_fino_interior) | [ficha](https://abastosoluciones.com.ar/construccion/248-weber-fino-interior.html) |
| Weber Fino Exterior | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_weber_fino_exterior) | [ficha](https://abastosoluciones.com.ar/construccion/249-weber-fino-exterior.html) |
| Weber Therm | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_weber_therm) | [ficha](https://abastosoluciones.com.ar/construccion/250-weber-therm.html) |
| Promex I | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_promex_i) | [ficha](https://abastosoluciones.com.ar/construccion/251-promex-i.html) |
| Promex E | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_promex_e) | [ficha](https://abastosoluciones.com.ar/construccion/252-promex-e.html) |
| Pastina | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_pastina) | [ficha](https://abastosoluciones.com.ar/construccion/253-pastina.html) |
| Pastina Prestige | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_pastina_prestige) | [ficha](https://abastosoluciones.com.ar/construccion/254-pastina-prestige.html) |
| Iggamflex | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_iggamflex) | [ficha](https://abastosoluciones.com.ar/construccion/255-iggamflex.html) |
| Ceresita | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_ceresita) | [ficha](https://abastosoluciones.com.ar/construccion/256-ceresita.html) |
| Ceresita C 50 | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_ceresita_c_50) | [ficha](https://abastosoluciones.com.ar/construccion/257-ceresita-c-50.html) |
| Base Coat | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_base_coat) | [ficha](https://abastosoluciones.com.ar/construccion/258-base-coat.html) |
| Yeso Yamaco | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_yeso_yamaco) | [ficha](https://abastosoluciones.com.ar/construccion/259-yeso-yamaco.html) |
| Sika Tex 75 | Aditivos y morteros | — | Abasto | tercero (reventa) | no → agregado (ab_sika_tex_75) | [ficha](https://abastosoluciones.com.ar/construccion/260-sika-tex-75.html) |
| Chapa Sinusoidal Galvanizada | Chapa sinusoidal | — | Abasto | Abasto (marca propia) [A CONFIRMAR dónde] | no → agregado (ab_chapa_sinusoidal_galvanizada) | [ficha](https://abastosoluciones.com.ar/chapas/128-chapa-sinusoidal-galvanizada.html) |
| Chapa Sinusoidal negra | Chapa sinusoidal | — | Abasto | Abasto (marca propia) [A CONFIRMAR dónde] | no → agregado (ab_chapa_sinusoidal_negra) | [ficha](https://abastosoluciones.com.ar/chapa-sinusoidal/130-chapa-sinusoidal-negra.html) |
| Chapa Trapezoidal Galvanizada | Chapa trapezoidal | — | Abasto | Abasto (marca propia) [A CONFIRMAR dónde] | no → agregado (ab_chapa_trapezoidal_galvanizada) | [ficha](https://abastosoluciones.com.ar/chapas/129-chapa-trapezoidal-galvanizada.html) |
| Chapa Trapezoidal negra | Chapa trapezoidal | — | Abasto | Abasto (marca propia) [A CONFIRMAR dónde] | no → agregado (ab_chapa_trapezoidal_negra) | [ficha](https://abastosoluciones.com.ar/chapa-trapezoidal/131-chapa-trapezoidal-negra.html) |
| Chapas Polipropileno | Chapas polipropileno | — | Abasto | tercero (reventa) | no → agregado (ab_chapas_polipropileno) | [ficha](https://abastosoluciones.com.ar/chapas/134-chapas-polipropileno.html) |

### G-TEC (gtecdesarrollosyservicios.com): 10 productos o servicios

| Producto o servicio | Categoría en la web | Variantes publicadas | Lo vende | Lo fabrica | ¿Ya estaba en el programa? | Fuente |
|---|---|---|---|---|---|---|
| Desarrollo especial (diseño y simulación 3D) | Servicios | — | G-TEC | G-TEC | no → agregado (gt_desarrollo_especial) | [ficha](https://gtecdesarrollosyservicios.com/) |
| Corte láser de chapa | Servicios | — | G-TEC | G-TEC | no → agregado (gt_corte_laser) | [ficha](https://gtecdesarrollosyservicios.com/) |
| Corte láser de caño | Servicios | — | G-TEC | G-TEC | no → agregado (gt_corte_laser_cano) | [ficha](https://gtecdesarrollosyservicios.com/) |
| Corte por chorro de agua | Servicios | — | G-TEC | G-TEC | no → agregado (gt_chorro_agua) | [ficha](https://gtecdesarrollosyservicios.com/) |
| Plegado CNC | Servicios | — | G-TEC | G-TEC | no → agregado (gt_plegado_cnc) | [ficha](https://gtecdesarrollosyservicios.com/) |
| Mecanizado CNC (fresado, torneado y roscado) | Servicios | — | G-TEC | G-TEC | no → agregado (gt_mecanizado_cnc) | [ficha](https://gtecdesarrollosyservicios.com/) |
| Soldadura MIG | Servicios | — | G-TEC | G-TEC | no → agregado (gt_soldadura_mig) | [ficha](https://gtecdesarrollosyservicios.com/) |
| Soldadura láser | Servicios | — | G-TEC | G-TEC | no → agregado (gt_soldadura_laser) | [ficha](https://gtecdesarrollosyservicios.com/) |
| Soldadura robotizada | Servicios | — | G-TEC | G-TEC | no → agregado (gt_soldadura_robotizada) | [ficha](https://gtecdesarrollosyservicios.com/) |
| Pieza metalmecánica a medida (prototipos y series) | Fabricación a medida | — | G-TEC | G-TEC | no → agregado (gt_pieza_a_medida) | [ficha](https://gtecdesarrollosyservicios.com/) |

<!-- TABLA:fin -->
