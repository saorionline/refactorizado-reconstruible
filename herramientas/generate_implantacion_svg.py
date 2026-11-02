#!/usr/bin/env python3
"""Genera el plano del Lote 22 con las zonas internas de la casa dentro de
cada bloque (SVG), combinando lote.db (dónde va cada bloque) y plano.db (qué
hay adentro: zonas, muros, puertas, muebles).

Uso:
    python generate_implantacion_svg.py [--lote lote.db] [--plano plano.db]
                                        [--out ../planos/lote22_implantacion_interiores.svg]

Cada bloque de lote.db dice en `grupo_plano` qué grupo de zonas de plano.db
lleva adentro ('bloque_central', 'ala_izquierda', 'ala_derecha'). El grupo se
centra en el bloque y gira con él; así, mover o girar un bloque en lote.db
mueve su interior, y cambiar un muro o una zona en plano.db cambia lo que se
ve dentro del bloque. Ninguna de las dos bases se edita desde aquí.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import generate_lote_svg as lote
import generate_svg as casa

EPS = 0.01


def caja_grupo(zonas: list[dict]) -> tuple[float, float, float, float]:
    return (min(z["x"] for z in zonas), min(z["y"] for z in zonas),
            max(z["x"] + z["ancho"] for z in zonas), max(z["y"] + z["profundidad"] for z in zonas))


def en_caja(x: float, y: float, caja) -> bool:
    x0, y0, x1, y1 = caja
    return x0 - EPS <= x <= x1 + EPS and y0 - EPS <= y <= y1 + EPS


def interior_de_bloque(b: dict, plano: dict) -> tuple[str | None, list[str], list[str]]:
    """SVG de las zonas del grupo de `b`, ya ubicado y girado en el lote.
    Devuelve (svg, avisos, leyenda)."""
    zonas = [z for z in plano["zonas"] if z["grupo"] == b["grupo_plano"]]
    if not zonas:
        return None, [f'{b["nombre"]}: no hay zonas del grupo "{b["grupo_plano"]}" en plano.db'], []
    caja = caja_grupo(zonas)
    gx0, gy0, gx1, gy1 = caja
    gw, gd = gx1 - gx0, gy1 - gy0
    avisos = []
    if abs(gw - b["ancho"]) > EPS or abs(gd - b["fondo"]) > EPS:
        avisos.append(f'{b["nombre"]}: el bloque mide {b["ancho"]:g} × {b["fondo"]:g} m pero sus zonas '
                      f'miden {gw:g} × {gd:g} m en plano.db')
    gcx, gcy = (gx0 + gx1) / 2, (gy0 + gy1) / 2
    ids = {z["id"] for z in zonas}

    # metros de la casa -> píxeles del lote: centro del grupo sobre centro del bloque
    cxm, cym = lote.centro(lote.esquinas(b))
    Lx, Ly = lote.px(cxm, cym)
    Hx, Hy = casa.px(gcx, gcy)
    k = lote.SCALE / casa.SCALE
    partes = [f'<g transform="translate({Lx:.1f},{Ly:.1f}) rotate({b["giro"]:g}) '
              f'scale({k:g}) translate({-Hx:.1f},{-Hy:.1f})">']
    partes += [casa.dibujar_zona_relleno(z) for z in zonas]
    partes += [casa.dibujar_especial(e) for e in plano["especiales"]
               if e["tipo"] == "alero" and gx0 - EPS <= e["x"] and e["x"] + e["ancho"] <= gx1 + EPS
               and abs(e["y"] - gy1) <= EPS]
    partes += [casa.dibujar_muro(m) for m in plano["muros"]
               if en_caja(m["x1"], m["y1"], caja) and en_caja(m["x2"], m["y2"], caja)]
    # solo puertas entre zonas del mismo grupo: las que unían bloques que
    # ahora están separados abrirían al vacío
    for p in plano["puertas"]:
        if not en_caja(p["x"], p["y"], caja):
            continue
        if p["zona_a"] in ids and p["zona_b"] in ids:
            partes.append(casa.dibujar_puerta(p))
        elif p["zona_a"] in ids:   # se avisa una sola vez, desde el bloque de zona_a
            avisos.append(f'no se dibuja la puerta {p["zona_a"]} - {p["zona_b"]} (une bloques separados)')
    partes += [casa.dibujar_modulo(m) for m in plano["modulos"] if m["zona_id"] in ids]
    partes.append("</g>")

    # etiquetas derechas (sin girar) en el centro de cada zona
    t = math.radians(b["giro"])
    leyenda = []
    for z in zonas:
        hx, hy = z["x"] + z["ancho"] / 2 - gcx, z["y"] + z["profundidad"] / 2 - gcy
        x, y = lote.px(cxm + hx * math.cos(t) - hy * math.sin(t), cym + hx * math.sin(t) + hy * math.cos(t))
        if z["label_mode"] == "ninguno":
            continue
        partes.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7.5" fill="{z["numero_color"]}"/>')
        partes.append(f'<text x="{x:.1f}" y="{y + 3.6:.1f}" font-size="9.5" font-weight="700" '
                      f'text-anchor="middle" fill="#ffffff">{z["numero"]}</text>')
    for z in sorted(zonas, key=lambda z: z["numero"]):
        area = z["ancho"] * z["profundidad"]
        extra = "" if z["cuenta_area"] else ", techada"
        leyenda.append(f'{z["numero"]} {z["nombre"]} ({area:g} m²{extra})')
    return "\n".join(partes), avisos, leyenda


def main() -> None:
    here = Path(__file__).parent
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--lote", default=str(here / "lote.db"))
    parser.add_argument("--plano", default=str(here / "plano.db"))
    parser.add_argument("--out", default=str(here.parent / "planos" / "lote22_implantacion_interiores.svg"))
    args = parser.parse_args()

    data = lote.cargar(Path(args.lote))
    plano = casa.cargar(Path(args.plano))

    interiores, avisos, notas = {}, [], []
    for b in data["bloques"]:
        if not b.get("grupo_plano"):
            continue
        svg, av, leyenda = interior_de_bloque(b, plano)
        if svg:
            interiores[b["id"]] = svg
        avisos += av
        if leyenda:
            notas.append(f'{b["nombre"]}: ' + " · ".join(leyenda))

    svg, revision = lote.generar_svg(
        data, interiores, titulo="Lote 22 · implantación con zonas internas",
        notas_extra=[f"⚠ {a}" for a in avisos] + notas)
    Path(args.out).write_text(svg, encoding="utf-8")
    print(f"OK: {args.out}")
    for b, problemas, n_curvas in revision:
        print(f"  {'OK ' if not problemas else 'MAL'} {b['nombre']:<9} {', '.join(problemas) or 'bien ubicado'}")
    for a in avisos:
        print(f"  AVISO: {a}")


if __name__ == "__main__":
    main()
