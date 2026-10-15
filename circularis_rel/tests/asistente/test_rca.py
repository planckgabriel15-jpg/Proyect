"""5 Porqués, ciclo PDCA y OT modificativa [12.D]."""

import pytest

from circularis_rel.asistente import rca
from circularis_rel.datos.enums import EstadoOT, EstadoPDCA, Rol, TipoOT
from circularis_rel.datos.modelos import OrdenTrabajo, Usuario
from circularis_rel.servicios.permisos import PermisoDenegado
from circularis_rel.servicios.registro import ErrorRegistro


def test_ciclo_completo(db, planta):
    with db.escritura() as s:
        a = rca.crear(s, planta.jefe, "Las cuchillas pierden filo antes de tiempo", id_activo=planta.activo,
                      id_tipo=planta.tipo, id_modo=planta.modo)
        assert a.estado_pdca == EstadoPDCA.PLANIFICAR and len(a.contenido["pdca"]) == 1
        with pytest.raises(ErrorRegistro, match="causa raíz"):
            rca.avanzar(s, planta.jefe, a.id)
        rca.guardar_porques(s, planta.jefe, a.id, ["Entra material con piedras", "No se zarandea", "La zaranda está rota", "", ""],
                            accion="Reparar la zaranda y revisar cada semana", responsable="Encargado de turno")
        assert a.causa_raiz == "La zaranda está rota"  # vacía: el último porqué
        assert a.contenido["porques"] == ["Entra material con piedras", "No se zarandea", "La zaranda está rota"]
        ot = rca.convertir_en_ot(s, planta.jefe, a.id)
        assert ot.tipo == TipoOT.MODIFICATIVO and ot.estado == EstadoOT.PLANIFICADA and a.id_ot_generada == ot.id
        assert "zaranda" in ot.observaciones
        with pytest.raises(ErrorRegistro, match="ya tiene"):
            rca.convertir_en_ot(s, planta.jefe, a.id)
        rca.avanzar(s, planta.jefe, a.id, "Zaranda reparada")
        assert a.estado_pdca == EstadoPDCA.HACER
        rca.avanzar(s, planta.jefe, a.id)
        assert a.estado_pdca == EstadoPDCA.CHEQUEAR
        with pytest.raises(ErrorRegistro, match="Anotá"):
            rca.avanzar(s, planta.jefe, a.id)
        rca.avanzar(s, planta.jefe, a.id, "Dos meses sin fallas por filo")
        rca.avanzar(s, planta.jefe, a.id, "Revisión de la zaranda en el check-list semanal")
        assert a.estado_pdca == EstadoPDCA.CERRADO
        assert [p["estado"] for p in a.contenido["pdca"]] == [e.value for e in rca.ORDEN_PDCA]
        with pytest.raises(ErrorRegistro):
            rca.avanzar(s, planta.jefe, a.id, "otra")
        with pytest.raises(ErrorRegistro, match="cerrado"):
            rca.guardar_porques(s, planta.jefe, a.id, ["x"])


def test_validaciones(db, planta):
    with db.escritura() as s:
        with pytest.raises(ErrorRegistro):
            rca.crear(s, planta.jefe, "  ")
        a = rca.crear(s, planta.jefe, "Problema sin máquina")
        with pytest.raises(ErrorRegistro, match="vacíos"):
            rca.guardar_porques(s, planta.jefe, a.id, ["uno", "", "tres"])
        with pytest.raises(ErrorRegistro, match="Hasta"):
            rca.guardar_porques(s, planta.jefe, a.id, ["1", "2", "3", "4", "5", "6"])
        with pytest.raises(ErrorRegistro, match="acción"):
            rca.convertir_en_ot(s, planta.jefe, rca.crear(s, planta.jefe, "x", id_activo=planta.activo).id)
        rca.guardar_porques(s, planta.jefe, a.id, ["uno"], accion="algo")
        with pytest.raises(ErrorRegistro, match="máquina"):
            rca.convertir_en_ot(s, planta.jefe, a.id)
        assert s.query(OrdenTrabajo).count() == 0


def test_operario_no_carga_analisis(db, planta):
    with db.escritura() as s:
        op = Usuario(usuario="op", nombre="Operario", rol=Rol.OPERARIO, hash_password="x")
        s.add(op)
        s.flush()
        with pytest.raises(PermisoDenegado):
            rca.crear(s, op.id, "algo")
