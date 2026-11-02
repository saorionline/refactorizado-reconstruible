#!/usr/bin/env python3
"""(Re)crea una base de datos desde cero a partir de su archivo .sql.
Destructivo: borra cualquier cambio que solo exista en la base y no esté en
el .sql.

Uso:
    python init_db.py                                (plano.db desde schema.sql)
    python init_db.py --sql lote.sql --db lote.db    (lote.db desde lote.sql)
"""
import argparse
import sqlite3
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconstruye una base de datos desde su .sql.")
    parser.add_argument("--sql", default="schema.sql")
    parser.add_argument("--db", default="plano.db")
    args = parser.parse_args()

    here = Path(__file__).parent
    db_path = here / args.db
    sql = (here / args.sql).read_text(encoding="utf-8")
    con = sqlite3.connect(db_path)
    con.executescript(sql)
    con.commit()
    con.close()
    print(f"OK: {db_path} reconstruida desde {args.sql}")


if __name__ == "__main__":
    main()
