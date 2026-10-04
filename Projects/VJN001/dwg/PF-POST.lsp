;;; ===========================================================================
;;; PF-POST.lsp — Post-proceso en AutoCAD del legajo Rev E (proyecto VJN001)
;;; UTN FRC · Proyecto Final · Sistema de distribución de fertilizantes — Redler AGD
;;;
;;; Completa dentro de AutoCAD lo que el DXF no puede guardar:
;;;   PF-CTB            copia PF-IRAM-MONO.ctb a la carpeta de estilos de trazado
;;;   PF-VARIABLES      variables de sistema de §6.2 (MSLTSCALE, ANNOAUTOSCALE, FIELDEVAL, HPASSOC…)
;;;   PF-ESTILO-TABLA   estilo de tabla IRAM-TABLA (2,5 mm, márgenes 1 mm, bordes 0,35 / 0,18)
;;;   PF-PAGINA         configuración de impresión de todos los layouts (DWG To PDF, A3, 1:1, CTB)
;;;   PF-CAMPOS         campos del rótulo: CÓDIGO = nombre del layout, IMPRESIÓN = fecha de trazado
;;;   PF-ANOTATIVO-INFO informe: estilos y bloques marcados como anotativos
;;;   PF-FASE1          corre todo lo anterior en orden
;;;   PF-GUARDAR-DWT    guarda el dibujo actual como plantilla PF-IRAM-A3.dwt
;;;
;;; Uso: abrir el DXF/DWG, APPLOAD > PF-POST.lsp, escribir PF-FASE1.
;;; ===========================================================================
(vl-load-com)

(defun pf:doc () (vla-get-ActiveDocument (vlax-get-acad-object)))
(defun pf:msg (s) (princ (strcat "\n  " s)))

;;; --------------------------------------------------------------- CTB
(defun c:PF-CTB (/ src dst)
  (setq src (strcat (getvar "DWGPREFIX") "PF-IRAM-MONO.ctb")
        dst (strcat (vla-get-PrinterStyleSheetPath
                      (vla-get-Files (vla-get-Preferences (vlax-get-acad-object))))
                    "\\PF-IRAM-MONO.ctb"))
  (cond ((not (findfile src))
         (pf:msg (strcat "! No se encontró " src " (debe estar junto al dibujo).")))
        ((findfile dst) (pf:msg "PF-IRAM-MONO.ctb ya está en la carpeta de estilos de trazado."))
        ((vl-file-copy src dst) (pf:msg (strcat "CTB copiado a " dst)))
        (t (pf:msg "! No se pudo copiar el CTB; copialo a mano a la carpeta Plot Styles.")))
  (princ))

;;; --------------------------------------------------------------- variables (§6.2)
(defun c:PF-VARIABLES (/ lst)
  (setq lst '(("INSUNITS" 4) ("LUNITS" 2) ("LUPREC" 0) ("AUNITS" 0) ("AUPREC" 1)
              ("MEASUREMENT" 1) ("LTSCALE" 1.0) ("PSLTSCALE" 1) ("MSLTSCALE" 1)
              ("CELTSCALE" 1.0) ("ANNOAUTOSCALE" 4) ("DIMASSOC" 2) ("DIMDSEP" ",")
              ("LWDISPLAY" 1) ("FIELDEVAL" 31) ("PLINEGEN" 1) ("HPASSOC" 1)
              ("TEXTSTYLE" "IRAM") ("CMLEADERSTYLE" "IRAM-REF") ("CLAYER" "AN-NOPLOT")))
  (foreach p lst
    (if (vl-catch-all-error-p (vl-catch-all-apply 'setvar p))
      (pf:msg (strcat "! No se pudo fijar " (car p)))
      (pf:msg (strcat (car p) " = " (vl-princ-to-string (getvar (car p)))))))
  (if (tblsearch "DIMSTYLE" "IRAM-OBRA")
    (vl-catch-all-apply 'vla-put-ActiveDimStyle
      (list (pf:doc) (vla-Item (vla-get-DimStyles (pf:doc)) "IRAM-OBRA"))))
  (princ))

;;; --------------------------------------------------------------- estilo de tabla
(defun c:PF-ESTILO-TABLA (/ dic ts r)
  (setq dic (vla-Item (vla-get-Dictionaries (pf:doc)) "ACAD_TABLESTYLE"))
  (if (vl-catch-all-error-p (setq ts (vl-catch-all-apply 'vla-Item (list dic "IRAM-TABLA"))))
    (setq ts (vla-AddObject dic "IRAM-TABLA" "AcDbTableStyle")))
  (vla-put-Description ts "IRAM: texto 2,5 mm, márgenes 1 mm, bordes 0,35 / 0,18")
  (vla-put-HorzCellMargin ts 1.0)
  (vla-put-VertCellMargin ts 1.0)
  (vla-put-TitleSuppressed ts :vlax-true)
  (vla-put-HeaderSuppressed ts :vlax-false)
  (vla-put-FlowDirection ts acTableTopToBottom)
  (foreach r (list acDataRow acHeaderRow acTitleRow)
    (vla-SetTextHeight ts r 2.5)
    (vla-SetTextStyle ts r (if (= r acDataRow) "IRAM-N" "IRAM-NEGRITA"))
    (vla-SetAlignment ts r acMiddleLeft)
    (vla-SetGridLineWeight ts (+ acHorzInside acVertInside) r acLnWt018)
    (vla-SetGridLineWeight ts (+ acHorzTop acHorzBottom acVertLeft acVertRight) r acLnWt035))
  (pf:msg "Estilo de tabla IRAM-TABLA listo.")
  (princ))

;;; --------------------------------------------------------------- configuración de página
(defun pf:pagina (lay)
  (vla-put-ConfigName lay "DWG To PDF.pc3")
  (vla-RefreshPlotDeviceInfo lay)
  (vla-put-CanonicalMediaName lay "ISO_full_bleed_A3_(420.00_x_297.00_MM)")
  (vla-put-PaperUnits lay acMillimeters)
  (vla-put-PlotType lay acLayout)
  (vla-put-StandardScale lay ac1_1)
  (vla-put-PlotRotation lay ac0degrees)
  (vla-put-StyleSheet lay "PF-IRAM-MONO.ctb")
  (vla-put-PlotWithPlotStyles lay :vlax-true)
  (vla-put-PlotWithLineweights lay :vlax-true)
  (vla-put-ShowPlotStyles lay :vlax-true))

(defun c:PF-PAGINA (/ n e)
  (setq n 0)
  (vlax-for lay (vla-get-Layouts (pf:doc))
    (if (= (vla-get-ModelType lay) :vlax-false)
      (if (vl-catch-all-error-p (setq e (vl-catch-all-apply 'pf:pagina (list lay))))
        (pf:msg (strcat "! " (vla-get-Name lay) ": " (vl-catch-all-error-message e)))
        (setq n (1+ n)))))
  (pf:msg (strcat "Configuración de página aplicada a " (itoa n) " layouts."))
  (princ))

;;; --------------------------------------------------------------- campos del rótulo
(defun c:PF-CAMPOS (/ n)
  (setq n 0)
  (vlax-for lay (vla-get-Layouts (pf:doc))
    (vlax-for ent (vla-get-Block lay)
      (if (and (= (vla-get-ObjectName ent) "AcDbBlockReference")
               (= (strcase (vla-get-EffectiveName ent)) "ROTULO-A3"))
        (foreach att (vlax-invoke ent 'GetAttributes)
          (cond ((= (vla-get-TagString att) "CODIGO")
                 (vla-put-TextString att "%<\\AcVar ctab>%")
                 (setq n (1+ n)))
                ((= (vla-get-TagString att) "IMPRESION")
                 (vla-put-TextString att "%<\\AcVar PlotDate \\f \"dd/MM/yyyy\">%")))))))
  (vla-Regen (pf:doc) acAllViewports)
  (pf:msg (strcat "Campos de CÓDIGO e IMPRESIÓN cargados en " (itoa n) " rótulos."))
  (princ))

;;; --------------------------------------------------------------- informe de anotatividad
(defun pf:anot-p (ename)
  (and ename (assoc -3 (entget ename '("AcadAnnotative")))))

(defun c:PF-ANOTATIVO-INFO (/ b)
  (pf:msg "Estilos y bloques anotativos (XDATA AcadAnnotative):")
  (foreach s '("IRAM" "IRAM-N" "IRAM-NEGRITA")
    (pf:msg (strcat "  STYLE    " s " : " (if (pf:anot-p (tblobjname "STYLE" s)) "anotativo" "no anotativo"))))
  (foreach s '("IRAM-OBRA" "IRAM-OBRA-3" "IRAM-MEC")
    (pf:msg (strcat "  DIMSTYLE " s " : " (if (pf:anot-p (tblobjname "DIMSTYLE" s)) "anotativo" "no anotativo"))))
  (foreach s '("NIVEL-CORTE" "NIVEL-CORTE-IZQ" "NIVEL-PLANTA" "CORTE" "LLAMADA-DETALLE" "TITULO-VISTA"
               "NORTE" "EJE" "FLUJO" "PASO-RECORRIDO" "ROTULO-A3" "LISTA-MATERIALES" "LM-FILA" "GLOBO")
    (setq b (tblobjname "BLOCK" s))
    (pf:msg (strcat "  BLOCK    " s " : "
                    (cond ((null b) "no existe")
                          ((pf:anot-p (cdr (assoc 330 (entget b)))) "anotativo")
                          (t "no anotativo")))))
  (princ))

;;; --------------------------------------------------------------- fase 1 completa
(defun c:PF-FASE1 ()
  (princ "\n=== PF-FASE1: plantilla PF-IRAM-A3 ===")
  (c:PF-CTB)
  (c:PF-VARIABLES)
  (c:PF-ESTILO-TABLA)
  (c:PF-PAGINA)
  (c:PF-CAMPOS)
  (c:PF-ANOTATIVO-INFO)
  (princ "\n=== Fin PF-FASE1. Copiá este informe (F2) y mandámelo. ===")
  (princ))

;;; --------------------------------------------------------------- guardar plantilla
(defun c:PF-GUARDAR-DWT (/ f tipo)
  (setq f (getfiled "Guardar plantilla PF-IRAM-A3" (strcat (getvar "DWGPREFIX") "PF-IRAM-A3.dwt") "dwt" 1))
  (setq tipo (if (boundp 'ac2018_Template) (eval 'ac2018_Template) 66))
  (if f
    (if (vl-catch-all-error-p (vl-catch-all-apply 'vla-SaveAs (list (pf:doc) f tipo)))
      (pf:msg "! No se pudo guardar como plantilla: usá GUARDARCOMO > Plantilla de dibujo (*.dwt).")
      (pf:msg (strcat "Plantilla guardada: " f))))
  (princ))

(princ "\nPF-POST.lsp cargado. Comandos: PF-FASE1, PF-GUARDAR-DWT, PF-ANOTATIVO-INFO.")
(princ)
