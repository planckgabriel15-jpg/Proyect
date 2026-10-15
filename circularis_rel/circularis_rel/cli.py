"""Línea de comandos para la instalación y la administración.

    circularis inicializar                     crea o actualiza la base y carga los datos iniciales
    circularis crear-usuario jefe "Nombre" JEFE
    circularis importar planilla.xlsx --simular
    circularis importar historico.xlsx --historico
    circularis plantillas                      plantillas Excel vacías en docs/plantillas
    circularis qr --salida qr.pdf              etiquetas QR de todas las máquinas
    circularis ficha AGR-001                   ficha de catastro en PDF
    circularis revision                        estado de la revisión del jefe (fase 0)
    circularis demo cargar | borrar            datos ficticios de demostración
    circularis app                             levanta la aplicación web
"""

from __future__ import annotations

import argparse
import getpass
import subprocess
import sys
from pathlib import Path

from sqlalchemy import select

from circularis_rel.config import RAIZ_PROYECTO, cargar_config
from circularis_rel.datos.db import BaseDatos


def _db() -> BaseDatos:
    return BaseDatos(cargar_config().url_db)


def migrar(url: str) -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(RAIZ_PROYECTO / "alembic.ini"))
    cfg.set_main_option("script_location", str(RAIZ_PROYECTO / "circularis_rel" / "datos" / "migraciones"))
    cfg.attributes["url"] = url
    command.upgrade(cfg, "head")


def cmd_inicializar(_args) -> int:
    from circularis_rel.datos.semillas import sembrar

    cfg = cargar_config()
    for d in (cfg.dir_datos, cfg.dir_fotos, cfg.dir_backups, cfg.dir_exportaciones):
        d.mkdir(parents=True, exist_ok=True)
    migrar(cfg.url_db)
    with BaseDatos(cfg.url_db).escritura() as s:
        agregados = sembrar(s)
    print("Base lista en", cfg.url_db)
    print("Datos iniciales agregados:", ", ".join(f"{k} {v}" for k, v in agregados.items()))
    return 0


def cmd_crear_usuario(args) -> int:
    from circularis_rel.servicios import auth

    tipo = "PIN (4 a 6 números)" if args.rol.upper() == "OPERARIO" else "contraseña (8 caracteres o más)"
    clave = getpass.getpass(f"{tipo}: ")
    if clave != getpass.getpass("Repetir: "):
        print("No coinciden.")
        return 1
    maquinas = [m.strip() for m in args.maquinas.split(",")] if args.maquinas else []
    try:
        with _db().escritura() as s:
            u = auth.crear_usuario(s, args.usuario, args.nombre, args.rol.upper(), clave, args.email, maquinas)
            print(f"Usuario '{u.usuario}' creado con rol {u.rol.value}.")
    except ValueError as e:
        print("Error:", e)
        return 1
    return 0


def cmd_importar(args) -> int:
    from circularis_rel.servicios.importador.aplicar import importar

    reporte = importar(_db(), Path(args.archivo), simular=args.simular, historico=args.historico)
    print(reporte.texto())
    return 0 if reporte.ok else 2


def cmd_plantillas(args) -> int:
    from circularis_rel.servicios.importador.plantillas import (
        plantilla_carga_inicial,
        plantilla_historico,
    )

    destino = Path(args.destino)
    plantilla_carga_inicial(destino / "carga_inicial.xlsx")
    plantilla_historico(destino / "historico.xlsx")
    print("Plantillas en", destino)
    return 0


def cmd_qr(args) -> int:
    from circularis_rel.datos.modelos import Activo
    from circularis_rel.servicios.qr import etiquetas_pdf

    cfg = cargar_config()
    with _db().lectura() as s:
        consulta = select(Activo.codigo, Activo.nombre).where(Activo.activo.is_(True)).order_by(Activo.codigo)
        if args.maquinas:
            consulta = consulta.where(Activo.codigo.in_([m.strip() for m in args.maquinas.split(",")]))
        maquinas = [tuple(r) for r in s.execute(consulta)]
    if not maquinas:
        print("No hay máquinas cargadas.")
        return 1
    Path(args.salida).write_bytes(etiquetas_pdf(maquinas, cfg.url_base))
    print(f"{len(maquinas)} etiquetas en {args.salida} (dirección: {cfg.url_base})")
    return 0


def cmd_ficha(args) -> int:
    from circularis_rel.servicios.catastro import ficha_pdf

    with _db().lectura() as s:
        datos = ficha_pdf(s, args.codigo)
    salida = Path(args.salida or f"ficha_{args.codigo}.pdf")
    salida.write_bytes(datos)
    print("Ficha en", salida)
    return 0


def cmd_revision(_args) -> int:
    from circularis_rel.servicios.catastro import estado_revision

    with _db().lectura() as s:
        estados = estado_revision(s)
    for e in estados:
        marca = "✔" if e.revisado else "·"
        print(f"{marca} {e.codigo:10} {e.nombre[:35]:35} comp. {e.posiciones:3}  crít. {e.posiciones_criticas:2}  "
              f"clase {e.criticidad or '-'}  catastro {e.catastro_completo:.0%}  {'; '.join(e.faltantes)}")
    print(f"Revisadas: {sum(e.revisado for e in estados)} de {len(estados)}")
    return 0


def cmd_demo(args) -> int:
    from circularis_rel.servicios.demo import USUARIOS_DEMO, borrar_demo, cargar_demo

    db = _db()
    if args.accion == "cargar":
        tz = None if args.sin_historia else cargar_config().zona_horaria
        reporte = cargar_demo(db, tz=tz)
        print(reporte.texto())
        if reporte.aplicado:
            print("Usuarios DEMO (claves públicas, borrar antes de usar en serio):")
            for u, _n, rol, clave, _m in USUARIOS_DEMO:
                print(f"  {u:16} {rol:10} {clave}")
        return 0 if reporte.aplicado else 2
    borrar_demo(db)
    print("Datos DEMO borrados.")
    return 0


def cmd_app(args) -> int:
    inicio = RAIZ_PROYECTO / "circularis_rel" / "app" / "inicio.py"
    return subprocess.call([sys.executable, "-m", "streamlit", "run", str(inicio),
                            "--server.port", str(args.puerto), "--server.address", args.direccion,
                            "--browser.gatherUsageStats", "false"], cwd=RAIZ_PROYECTO)


def cmd_tareas(args) -> int:
    from circularis_rel.tareas.worker import correr

    return correr(args.una_vez)


def cmd_restaurar(args) -> int:
    from circularis_rel.tareas import backup

    cfg = cargar_config()
    if cfg.url_db.startswith("sqlite:///") and Path(cfg.url_db.removeprefix("sqlite:///")).exists():
        previo = backup.hacer_backup(cfg.url_db, cfg.dir_backups / "antes_de_restaurar")
        print("Backup de la base actual en", previo)
    backup.restaurar(Path(args.archivo), cfg.url_db, cfg.dir_fotos)
    print("Restaurado. Reiniciar los servicios CircularisApp y CircularisTareas.")
    return 0


def cmd_exportar(args) -> int:
    from circularis_rel.servicios.exportacion import exportar_todo

    with _db().lectura() as s:
        Path(args.salida).write_bytes(exportar_todo(s))
    print("Exportado en", args.salida)
    return 0


def cmd_iniciar_captura(_args) -> int:
    from circularis_rel.servicios.vidas import iniciar_vidas

    with _db().escritura() as s:
        n = iniciar_vidas(s)
    print(f"{n} vidas en servicio creadas (edad desconocida) para empezar la captura.")
    return 0


def cmd_weibull(args) -> int:
    """Motor desde la línea de comandos: CSV con columnas edad,estado[,edad_inf] (estado F, S o I)."""
    import csv

    from circularis_rel.motor import kpis
    from circularis_rel.motor import weibull as W
    from circularis_rel.motor.tipos import Observacion

    with open(args.archivo, encoding="utf-8") as f:
        obs = [Observacion(float(r["edad"]), r["estado"].strip().upper(),
                           float(r["edad_inf"]) if r.get("edad_inf") else None) for r in csv.DictReader(f)]
    res = W.ajustar(obs, beta_ref=args.beta_ref, metodo_forzado=args.metodo)
    for nombre, a in (("Vigente", res.vigente), ("Alternativa", res.alternativa)):
        if a is None:
            continue
        print(f"{nombre}: {a.metodo}  fallas {a.n_fallas}  suspensiones {a.n_suspensiones}  intervalos {a.n_intervalo}")
        if a.valido:
            print(f"  β = {a.beta:.3f}  η = {a.eta:.1f}  IC {a.nivel_ic:.0%} ({a.metodo_ic}): β {a.beta_ic}  η {a.eta_ic}")
            print(f"  r² = {a.r2}  r² crítico = {a.r2_critico}  confianza {a.confianza}  lectura {a.interpretacion}")
            print(f"  MTTF = {kpis.mttf(a.beta, a.eta):.1f}  B10 = {kpis.vida_b(0.1, a.beta, a.eta):.1f}")
            if args.edad is not None and args.delta:
                print(f"  P(falla en {args.delta:g} | edad {args.edad:g}) = "
                      f"{kpis.prob_condicional(args.edad, args.delta, a.beta, a.eta):.1%}")
        for adv in a.advertencias:
            print("  ⚠", adv)
    print(f"Motor {W.__version__} · hash de datos {res.hash_datos[:12]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="circularis", description="Sistema de confiabilidad de Circularis")
    sub = p.add_subparsers(dest="comando", required=True)
    sub.add_parser("inicializar").set_defaults(f=cmd_inicializar)
    c = sub.add_parser("crear-usuario")
    c.add_argument("usuario")
    c.add_argument("nombre")
    c.add_argument("rol", choices=["OPERARIO", "ENCARGADO", "JEFE", "GERENCIA", "operario", "encargado", "jefe", "gerencia"])
    c.add_argument("--email")
    c.add_argument("--maquinas", help="Códigos separados por coma (operarios)")
    c.set_defaults(f=cmd_crear_usuario)
    c = sub.add_parser("importar")
    c.add_argument("archivo")
    c.add_argument("--simular", action="store_true")
    c.add_argument("--historico", action="store_true")
    c.set_defaults(f=cmd_importar)
    c = sub.add_parser("plantillas")
    c.add_argument("--destino", default=str(RAIZ_PROYECTO / "docs" / "plantillas"))
    c.set_defaults(f=cmd_plantillas)
    c = sub.add_parser("qr")
    c.add_argument("--salida", default="etiquetas_qr.pdf")
    c.add_argument("--maquinas")
    c.set_defaults(f=cmd_qr)
    c = sub.add_parser("ficha")
    c.add_argument("codigo")
    c.add_argument("--salida")
    c.set_defaults(f=cmd_ficha)
    sub.add_parser("revision").set_defaults(f=cmd_revision)
    c = sub.add_parser("demo")
    c.add_argument("accion", choices=["cargar", "borrar"])
    c.add_argument("--sin-historia", action="store_true", help="solo el catálogo, sin partes ni fallas ficticias")
    c.set_defaults(f=cmd_demo)
    c = sub.add_parser("app")
    c.add_argument("--puerto", type=int, default=8501)
    c.add_argument("--direccion", default="0.0.0.0")
    c.set_defaults(f=cmd_app)
    c = sub.add_parser("tareas", help="proceso de tareas programadas (servicio)")
    c.add_argument("--una-vez", choices=["nocturno", "faltantes", "backup", "prueba_restauracion", "cola", "plan",
                                         "alertas_diarias", "mails", "mails_resumen", "reporte_mensual", "resumen_semanal",
                                         "tendencias", "ocurrencias_amfe"])
    c.set_defaults(f=cmd_tareas)
    c = sub.add_parser("restaurar", help="restaura un backup (hace antes un backup de la base actual)")
    c.add_argument("archivo")
    c.set_defaults(f=cmd_restaurar)
    c = sub.add_parser("exportar", help="exportación total a Excel")
    c.add_argument("--salida", default="circularis_exportacion.xlsx")
    c.set_defaults(f=cmd_exportar)
    sub.add_parser("iniciar-captura", help="crea las vidas iniciales de cada componente").set_defaults(f=cmd_iniciar_captura)
    c = sub.add_parser("weibull", help="ajusta Weibull a un CSV (edad,estado[,edad_inf])")
    c.add_argument("archivo")
    c.add_argument("--beta-ref", type=float)
    c.add_argument("--metodo", choices=["RRX", "MLE", "WEIBAYES"])
    c.add_argument("--edad", type=float)
    c.add_argument("--delta", type=float)
    c.set_defaults(f=cmd_weibull)
    args = p.parse_args(argv)
    return args.f(args)


if __name__ == "__main__":
    raise SystemExit(main())
