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
        reporte = cargar_demo(db)
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
    c.set_defaults(f=cmd_demo)
    c = sub.add_parser("app")
    c.add_argument("--puerto", type=int, default=8501)
    c.add_argument("--direccion", default="0.0.0.0")
    c.set_defaults(f=cmd_app)
    args = p.parse_args(argv)
    return args.f(args)


if __name__ == "__main__":
    raise SystemExit(main())
