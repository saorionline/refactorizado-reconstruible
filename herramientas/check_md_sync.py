#!/usr/bin/env python3
"""Compara el cuadro de áreas en Markdown contra plano.db (la base de datos
que usa generate_svg.py) y avisa si algo quedó desincronizado.

El Markdown (documentos/propuesta_01_cuadro_de_areas_v2.md) es el documento
que lee una persona; plano.db es el que usa el programa para dibujar. Este
script es el puente: lee las filas numeradas del Markdown ("| 16 | Estudio
(2 personas) | 5.0 | 2.0 | 10.0 | ... |") y las compara con la tabla
`zonas` de la base de datos por número de zona.

Uso:
    python check_md_sync.py [--db plano.db] [--md ruta/al/cuadro.md]
"""
from __future__ import annotations

import argparse
import re
import sqlite3
from pathlib import Path

FILA_RE = re.compile(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|")


def parsear_md(md_path: Path) -> dict[int, dict]:
    filas: dict[int, dict] = {}
    for linea in md_path.read_text(encoding="utf-8").splitlines():
        m = FILA_RE.match(linea.strip())
        if not m:
            continue
        numero = int(m.group(1))
        filas[numero] = {
            "nombre": m.group(2).strip(),
            "largo": float(m.group(3)),
            "ancho": float(m.group(4)),
            "area": float(m.group(5)),
        }
    return filas


def cargar_zonas(db_path: Path) -> dict[int, dict]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    zonas = {
        row["numero"]: dict(row)
        for row in con.execute("SELECT * FROM zonas WHERE numero IS NOT NULL")
    }
    con.close()
    return zonas


def comparar(md_filas: dict[int, dict], zonas: dict[int, dict]) -> list[str]:
    problemas = []
    for numero, fila_md in sorted(md_filas.items()):
        zona = zonas.get(numero)
        if zona is None:
            problemas.append(f"#{numero} '{fila_md['nombre']}': está en el Markdown pero no en plano.db")
            continue
        area_db = round(zona["ancho"] * zona["profundidad"], 2)
        if abs(area_db - fila_md["area"]) > 0.05:
            problemas.append(
                f"#{numero} '{fila_md['nombre']}': área del Markdown={fila_md['area']} m² "
                f"vs. plano.db={area_db} m² ({zona['ancho']}×{zona['profundidad']})"
            )
        if abs(zona["ancho"] - fila_md["largo"]) > 0.01:
            problemas.append(
                f"#{numero} '{fila_md['nombre']}': Largo del Markdown={fila_md['largo']} "
                f"vs. ancho(X) de plano.db={zona['ancho']}"
            )
        if abs(zona["profundidad"] - fila_md["ancho"]) > 0.01:
            problemas.append(
                f"#{numero} '{fila_md['nombre']}': Ancho del Markdown={fila_md['ancho']} "
                f"vs. profundidad(Y) de plano.db={zona['profundidad']}"
            )

    for numero, zona in sorted(zonas.items()):
        if numero not in md_filas:
            problemas.append(f"#{numero} '{zona['nombre']}': está en plano.db pero no aparece en el Markdown")

    return problemas


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=str(Path(__file__).parent / "plano.db"))
    ap.add_argument(
        "--md",
        default=str(Path(__file__).parent.parent / "documentos" / "propuesta_01_cuadro_de_areas_v2.md"),
    )
    args = ap.parse_args()

    md_filas = parsear_md(Path(args.md))
    zonas = cargar_zonas(Path(args.db))
    problemas = comparar(md_filas, zonas)

    print(f"Filas leídas del Markdown: {len(md_filas)}  ·  Zonas con número en plano.db: {len(zonas)}")
    if not problemas:
        print("OK: el Markdown y plano.db coinciden en número, dimensiones y área por zona.")
        return
    print(f"\n{len(problemas)} diferencia(s) encontradas:\n")
    for p in problemas:
        print(f"  - {p}")


if __name__ == "__main__":
    main()
