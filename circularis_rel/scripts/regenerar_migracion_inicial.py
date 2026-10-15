"""Regenera la migración 0001 desde los modelos. SOLO mientras no haya ninguna base en producción
(fase 0). Después de la puesta en marcha, cada cambio va en una migración nueva.

Uso:  python scripts/regenerar_migracion_inicial.py
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
VERSIONES = RAIZ / "circularis_rel" / "datos" / "migraciones" / "versions"
ARCHIVO = VERSIONES / "0001_esquema_inicial.py"

TRIGGERS_UP = '''    # ### end Alembic commands ###

    # Triggers de reglas de negocio (solo SQLite; ver ddl_extra.py y DECISIONES D-018).
    if op.get_bind().dialect.name == "sqlite":
        from circularis_rel.datos.ddl_extra import sentencias_sqlite

        for sql in sentencias_sqlite():
            op.execute(sql)
'''

TRIGGERS_DOWN = '''def downgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        for (nombre,) in op.get_bind().exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type = 'trigger'"
        ).fetchall():
            op.execute(f"DROP TRIGGER IF EXISTS {nombre}")
'''


def main() -> None:
    ARCHIVO.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, CIRCULARIS_DB_URL=f"sqlite:///{Path(tmp) / 'vacia.db'}")
        subprocess.run([sys.executable, "-m", "alembic", "revision", "--autogenerate", "-m", "esquema inicial",
                        "--rev-id", "0001"], cwd=RAIZ, env=env, check=True)
    texto = ARCHIVO.read_text(encoding="utf-8")
    texto = texto.replace("    # ### end Alembic commands ###\n", TRIGGERS_UP, 1)
    texto = texto.replace("def downgrade() -> None:\n", TRIGGERS_DOWN, 1)
    ARCHIVO.write_text(texto, encoding="utf-8")
    print("Migración regenerada:", ARCHIVO.relative_to(RAIZ))


if __name__ == "__main__":
    main()
