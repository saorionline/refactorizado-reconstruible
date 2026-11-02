#!/usr/bin/env python3
"""Dibuja el acomodo elegido del bloque central (7.80 × 9.75 m) en SVG.

Uso:
    python generate_bloque_central_svg.py [--out ../planos/propuestas_bloque_central.svg]

Es un boceto de distribución, independiente de plano.db: las zonas, muros,
entradas y ventanas viven en las listas de abajo. Para cambiar el dibujo se
editan esas listas y se vuelve a correr el script.

Unidades de rejilla: u = 0.4875 m (todas las medidas de la tabla son
múltiplos). El bloque mide 16 × 20 u. Orientación como en el plano del lote:
vía a la izquierda, Lote 20 arriba, Lote 24 abajo, Lote 23 a la derecha.
"""
from __future__ import annotations

import argparse
from pathlib import Path

U = 0.4875               # metros por unidad de rejilla
ANCHO_U, ALTO_U = 16, 20  # bloque de 7.80 × 9.75 m

C = {"social": "#f3ece0", "serv": "#e9e5f0", "estudio": "#d7e8e0", "terraza": "#e2ecd9"}

# ---------------------------------------------------------------------------
# Datos del acomodo (todo en unidades de rejilla)
# ---------------------------------------------------------------------------
#        num  nombre         x   y   w   h  color     ¿muro?
ZONAS = [(1, "Cocina",       0,  0, 12,  4, "social",  False),
         (5, "Lavandería",  12,  0,  4,  4, "serv",    True),
         (2, "Comedor",      0,  4, 12,  5, "social",  False),
         (4, "Terraza",      0,  9,  3, 11, "terraza", False),
         (3, "Sala",         3,  9,  9, 11, "social",  False),
         (0, "4b Terraza",  12,  4,  4,  9, "terraza", False),
         (16, "Estudio",    12, 13,  4,  7, "estudio", False)]

NOTAS = ["Baño (17) y bodega (18) sin muros: ahora son parte de la sala (4.39 × 5.36)",
         "Estudio 1.95 × 3.41 en la esquina Lote 24 / Lote 23 (absorbe el acceso), con entrada desde el Lote 23",
         "Terraza 4b 1.95 × 4.39 sin muro, con 2 peldaños 0.24 × 4.39 hacia el Lote 23",
         "Terraza de la vía 1.46 × 5.36 con 2 peldaños de 0.24 × 5.36 hacia la vía",
         "Ventanas hacia el Lote 20, centradas: cocina 3.85 m · lavandería 1.40 m"]

# muros sueltos (x1, y1, x2, y2), además de los de las zonas con muro
MUROS = [(0, 9, 3, 9),      # comedor | terraza de la vía (1.46 m)
         (12, 13, 16, 13)]  # estudio | terraza 4b (1.95 m)

M30 = 0.30 / U              # marco de 30 cm de muro a cada lado de un ventanal
MARCOS = [(3, 9, 3, 9 + M30), (3, 20 - M30, 3, 20),      # terraza vía -> sala
          (12, 4, 12, 4 + M30), (12, 13 - M30, 12, 13)]  # terraza 4b -> comedor

# ventanas: línea roja delgada que reemplaza ese tramo de muro
_c = 6 - 3.85 / 2 / U       # cocina mide 12 u; ventana de 3.85 m centrada
_l = 1.40 / 2 / U           # lavandería: 4 u desde x = 12; ventana de 1.40 m centrada
VENTANAS = [(_c, 0, 12 - _c, 0),          # cocina -> Lote 20
            (14 - _l, 0, 14 + _l, 0)]     # lavandería -> Lote 20

# entradas y ventanales (naranja): (eje, coordenada fija, desde, hasta)
#   eje 'x' = sobre un muro vertical (x fijo); eje 'y' = sobre uno horizontal
ENTRADAS = [("x", 0, 4 + M30, 9 - M30),    # vía -> comedor, 30 cm de muro a cada lado
            ("x", 3, 9 + M30, 20 - M30),   # ventanal terraza -> sala
            ("x", 16, 15.6, 17.4),         # Lote 23 -> estudio
            ("x", 12, 4 + M30, 13 - M30),  # ventanal terraza 4b -> comedor
            ("x", 12, 1, 2.85)]            # cocina -> lavandería

PELDANO = 0.24 / U          # 24 cm de huella

# ---------------------------------------------------------------------------
# Dibujo
# ---------------------------------------------------------------------------
S = 38.0                    # píxeles por metro
GAP, MX, MY = 110, 70, 150


def P(x: float, y: float) -> tuple[float, float]:
    """Unidades de rejilla -> píxeles del lienzo."""
    return MX + x * U * S, MY + y * U * S


def linea(a, b, color: str, grosor: float) -> str:
    (x1, y1), (x2, y2) = P(*a), P(*b)
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{grosor}"/>')


def comprobar_zonas() -> None:
    """Las zonas deben llenar el bloque exacto, sin huecos ni encimes."""
    celdas: dict[tuple[int, int], str] = {}
    for _, nom, x, y, w, h, _, _ in ZONAS:
        for cx in range(x, x + w):
            for cy in range(y, y + h):
                assert (cx, cy) not in celdas, f"{nom} se encima con {celdas[(cx, cy)]}"
                celdas[(cx, cy)] = nom
    assert len(celdas) == ANCHO_U * ALTO_U, f"faltan {ANCHO_U * ALTO_U - len(celdas)} celdas por llenar"


def dibujar_zona(num, nom, x, y, w, h, col, muro) -> list[str]:
    (x0, y0), (x1, y1) = P(x, y), P(x + w, y + h)
    borde = 'stroke="#1f2933" stroke-width="3"' if muro else 'stroke="#9aa5b1" stroke-width="1" stroke-dasharray="5 4"'
    out = [f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" fill="{C[col]}" {borde}/>']
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    etiqueta = (f"{num} " if num else "") + nom
    dims = f"{w * U:.2f} × {h * U:.2f}"
    if w < 4:   # zonas angostas (terraza): texto vertical
        rot = f'transform="rotate(-90 {cx:.1f} {cy:.1f})"'
        out.append(f'<text x="{cx:.1f}" y="{cy - 2:.1f}" font-size="11" font-weight="700" text-anchor="middle" fill="#1f2933" {rot}>{etiqueta}</text>')
        out.append(f'<text x="{cx:.1f}" y="{cy + 11:.1f}" font-size="10" text-anchor="middle" fill="#3e4c59" {rot}>{dims}</text>')
    elif w == 4:   # columna de 1.95 m: letra más pequeña
        out.append(f'<text x="{cx:.1f}" y="{cy - 3:.1f}" font-size="10" font-weight="700" text-anchor="middle" fill="#1f2933">{etiqueta}</text>')
        out.append(f'<text x="{cx:.1f}" y="{cy + 11:.1f}" font-size="9.5" text-anchor="middle" fill="#3e4c59">{dims}</text>')
    else:
        out.append(f'<text x="{cx:.1f}" y="{cy - 3:.1f}" font-size="12" font-weight="700" text-anchor="middle" fill="#1f2933">{etiqueta}</text>')
        out.append(f'<text x="{cx:.1f}" y="{cy + 12:.1f}" font-size="10.5" text-anchor="middle" fill="#3e4c59">{dims}</text>')
    return out


def dibujar_terraza_abierta(x, y, w, h) -> list[str]:
    """Bordes de la terraza sobre el perímetro sin muro, y 2 peldaños hacia
    afuera si da a la vía o al Lote 23."""
    out = []
    for (ax, ay), (bx, by) in (((x, y), (x + w, y)), ((x + w, y), (x + w, y + h)),
                               ((x, y + h), (x + w, y + h)), ((x, y), (x, y + h))):
        if (ax == bx and ax in (0, ANCHO_U)) or (ay == by and ay in (0, ALTO_U)):
            (x1, y1), (x2, y2) = P(ax, ay), P(bx, by)
            dx, dy = (0, 2.5) if ax == bx else (2.5, 0)   # no comerse la esquina del muro vecino
            out.append(f'<line x1="{x1 + dx:.1f}" y1="{y1 + dy:.1f}" x2="{x2 - dx:.1f}" y2="{y2 - dy:.1f}" stroke="{C["terraza"]}" stroke-width="6"/>')
            out.append(linea((ax, ay), (bx, by), "#52606d", 1))
    lado = -1 if x == 0 else (1 if x + w == ANCHO_U else 0)
    if not lado:
        return out
    borde = 0 if lado < 0 else ANCHO_U
    for k in (1, 2):
        xa, xb = sorted((borde + lado * (k - 1) * PELDANO, borde + lado * k * PELDANO))
        (x0, y0), (x1, y1) = P(xa, y), P(xb, y + h)
        out.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" '
                   f'fill="#efefef" stroke="#52606d" stroke-width="1"/>')
    (lx, ly0), (_, ly1) = P(borde + lado * (2 * PELDANO + 0.5), y), P(0, y + h)
    ly = (ly0 + ly1) / 2
    out.append(f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="9.5" fill="#52606d" text-anchor="middle" '
               f'transform="rotate({90 * lado} {lx:.1f} {ly:.1f})">2 peldaños 0.24 × {h * U:.2f}</text>')
    return out


def generar_svg() -> str:
    comprobar_zonas()
    W = max(900, int(MX * 2 + ANCHO_U * U * S))   # mínimo para que quepan título y leyenda
    H = int(MY + ALTO_U * U * S + 230)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Segoe UI, Arial, sans-serif">',
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
           '<text x="40" y="42" font-size="22" font-weight="700" fill="#1f2933">Bloque central · acomodo elegido (7.80 × 9.75 m = 76 m²)</text>',
           '<text x="40" y="66" font-size="13" fill="#3e4c59">Vía a la izquierda · Lote 20 arriba · Lote 24 abajo. Muros en la lavandería, comedor | terraza y estudio | terraza 4b; lo demás es abierto (punteado).</text>',
           '<text x="40" y="86" font-size="13" fill="#3e4c59"><tspan fill="#d9480f" font-weight="700">━━</tspan> entradas y ventanales: vía → comedor (continuo) · terraza → sala · terraza 4b → comedor · Lote 23 → estudio</text>',
           '<text x="40" y="106" font-size="13" fill="#3e4c59"><tspan fill="#1f2933" font-weight="700">━━</tspan> muro (30 cm de marco a cada lado de las entradas) · terrazas abiertas, sin muro, con 2 peldaños · <tspan fill="#e03131" font-weight="700">─</tspan> ventana</text>',
           f'<text x="{MX}" y="{MY - 26}" font-size="16" font-weight="700" fill="#1f2933">Opción A</text>']
    for z in ZONAS:
        out += dibujar_zona(*z)
    (bx0, by0), (bx1, by1) = P(0, 0), P(ANCHO_U, ALTO_U)
    out.append(f'<rect x="{bx0:.1f}" y="{by0:.1f}" width="{bx1 - bx0:.1f}" height="{by1 - by0:.1f}" fill="none" stroke="#1f2933" stroke-width="5"/>')
    for _, _, x, y, w, h, col, _ in ZONAS:
        if col == "terraza":
            out += dibujar_terraza_abierta(x, y, w, h)
    out += [linea(m[:2], m[2:], "#1f2933", 3) for m in MUROS]
    out += [linea(m[:2], m[2:], "#1f2933", 5) for m in MARCOS]
    for v in VENTANAS:
        out += [linea(v[:2], v[2:], "#ffffff", 6), linea(v[:2], v[2:], "#e03131", 1.6)]
    for eje, fijo, a, b in ENTRADAS:
        p1, p2 = ((fijo, a), (fijo, b)) if eje == "x" else ((a, fijo), (b, fijo))
        out += [linea(p1, p2, "#ffffff", 7), linea(p1, p2, "#d9480f", 4)]

    my = (by0 + by1) / 2
    out.append(f'<text x="{bx0 - 44:.1f}" y="{my:.1f}" font-size="11" fill="#7b8794" text-anchor="middle" transform="rotate(-90 {bx0 - 44:.1f} {my:.1f})">VÍA</text>')
    out.append(f'<text x="{(bx0 + bx1) / 2:.1f}" y="{by0 - 8:.1f}" font-size="11" fill="#7b8794" text-anchor="middle">LOTE 20</text>')
    out.append(f'<text x="{(bx0 + bx1) / 2:.1f}" y="{by1 + 18:.1f}" font-size="11" fill="#7b8794" text-anchor="middle">LOTE 24</text>')
    out.append(f'<text x="{bx1 + 44:.1f}" y="{my:.1f}" font-size="11" fill="#7b8794" text-anchor="middle" transform="rotate(90 {bx1 + 44:.1f} {my:.1f})">LOTE 23</text>')
    for k, n in enumerate(NOTAS):
        out.append(f'<text x="{MX}" y="{by1 + 48 + k * 18:.0f}" font-size="12" fill="#3e4c59">• {n}</text>')
    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    here = Path(__file__).parent
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(here.parent / "planos" / "propuestas_bloque_central.svg"))
    args = parser.parse_args()
    Path(args.out).write_text(generar_svg(), encoding="utf-8")
    print(f"OK: {args.out}")


if __name__ == "__main__":
    main()
