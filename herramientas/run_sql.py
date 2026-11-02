#!/usr/bin/env python3
"""Ejecuta un archivo .sql (una o varias sentencias) contra plano.db (o la
base que indiques con --db).

Pensado para cambios puntuales: escribe el UPDATE/INSERT en un archivo .sql
(puede ser de una sola línea) y corre este script -- evita pelear con el
escapado de comillas del shell al meter SQL directo en la línea de comandos.

Uso:
    python run_sql.py mi_cambio.sql                  (plano de la casa)
    python generate_svg.py

    python run_sql.py --db lote.db mi_cambio.sql     (implantación en el lote)
    python generate_lote_svg.py
"""
import argparse
import sqlite3
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Ejecuta un archivo .sql contra la base de datos.")
    parser.add_argument("archivo", help="archivo .sql a aplicar")
    parser.add_argument("--db", default="plano.db", help="base de datos (por defecto plano.db)")
    args = parser.parse_args()

    archivo = Path(args.archivo)
    db_path = Path(__file__).parent / args.db
    sql = archivo.read_text(encoding="utf-8")

    con = sqlite3.connect(db_path)
    try:
        con.executescript(sql)
        con.commit()
    finally:
        con.close()
    script = "generate_lote_svg.py" if db_path.name == "lote.db" else "generate_svg.py"
    print(f"OK: {archivo} aplicado a {db_path}. Corre 'python {script}' para ver el resultado.")


if __name__ == "__main__":
    main()
