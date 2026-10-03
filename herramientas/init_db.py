#!/usr/bin/env python3
"""(Re)crea plano.db desde cero a partir de schema.sql. Destructivo: borra
cualquier cambio que solo exista en plano.db y no esté en schema.sql.

Uso: python init_db.py
"""
import sqlite3
from pathlib import Path


def main() -> None:
    here = Path(__file__).parent
    db_path = here / "plano.db"
    sql = (here / "schema.sql").read_text(encoding="utf-8")
    con = sqlite3.connect(db_path)
    con.executescript(sql)
    con.commit()
    con.close()
    print(f"OK: {db_path} reconstruida desde schema.sql")


if __name__ == "__main__":
    main()
