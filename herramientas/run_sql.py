#!/usr/bin/env python3
"""Ejecuta un archivo .sql (una o varias sentencias) contra plano.db.

Pensado para cambios puntuales: escribe el UPDATE/INSERT en un archivo .sql
(puede ser de una sola línea) y corre este script -- evita pelear con el
escapado de comillas del shell al meter SQL directo en la línea de comandos.

Uso:
    python run_sql.py mi_cambio.sql
    python generate_svg.py
"""
import sqlite3
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python run_sql.py archivo.sql")
        sys.exit(1)

    archivo = Path(sys.argv[1])
    db_path = Path(__file__).parent / "plano.db"
    sql = archivo.read_text(encoding="utf-8")

    con = sqlite3.connect(db_path)
    try:
        con.executescript(sql)
        con.commit()
    finally:
        con.close()
    print(f"OK: {archivo} aplicado a {db_path}. Corre 'python generate_svg.py' para ver el resultado.")


if __name__ == "__main__":
    main()
