#!/usr/bin/env python3
"""Genera el plano de implantación del Lote 22 (SVG) a partir de lote.db.

Uso:
    python generate_lote_svg.py [--db lote.db] [--out ../planos/lote22_implantacion.svg]

El lote, las curvas de nivel y los bloques de la casa viven en SQLite, en
METROS reales. Este script SOLO traduce esos datos a píxeles SVG y revisa que
los bloques quepan. Para cambiar la composición se edita la base de datos
(ver queries_lote.sql) y se vuelve a correr este script.
"""
from __future__ import annotations

import argparse
import math
import sqlite3
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuración de dibujo (lo que es "nada más de SVG" vive aquí, no en la
# base de datos).
# ---------------------------------------------------------------------------
SCALE = 24.0            # píxeles por metro
ORIGIN_X = 90.0         # margen izquierdo (px) -> x = 0 m
ORIGIN_Y = 110.0        # margen superior (px) -> y = 0 m
CANVAS_W = 1100

COLOR_LOTE = "#1f2933"
COLOR_CURVA = "#a39e8f"
COLOR_RETIRO = "#c0763a"
COLOR_REJILLA = "#ebe7dd"
COLOR_TEXTO_SEC = "#3e4c59"
COLOR_TEXTO_TENUE = "#7b8794"
COLOR_OK = "#2e7d4f"
COLOR_MAL = "#c2412d"


def px(x_m: float, y_m: float) -> tuple[float, float]:
    """Convierte metros (coordenadas del lote) a píxeles del lienzo SVG."""
    return ORIGIN_X + x_m * SCALE, ORIGIN_Y + y_m * SCALE


def puntos(poli: list[tuple[float, float]]) -> str:
    return " ".join(f"{px(x, y)[0]:.1f},{px(x, y)[1]:.1f}" for x, y in poli)


def esc(texto: str) -> str:
    return (texto or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------
def cargar(db_path: Path) -> dict:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    curvas: dict[int, list[tuple[float, float]]] = {}
    for r in con.execute("SELECT curva, x, y FROM curvas_nivel ORDER BY curva, orden"):
        curvas.setdefault(r["curva"], []).append((r["x"], r["y"]))
    data = {
        "config": {r["clave"]: r["valor"] for r in con.execute("SELECT clave, valor FROM configuracion")},
        "vertices": [dict(r) for r in con.execute("SELECT * FROM lote_vertices ORDER BY orden")],
        "curvas": list(curvas.values()),
        "bloques": [dict(r) for r in con.execute("SELECT * FROM bloques ORDER BY x")],
    }
    con.close()
    return data


# ---------------------------------------------------------------------------
# Geometría (todo en metros)
# ---------------------------------------------------------------------------
def esquinas(b: dict) -> list[tuple[float, float]]:
    """Las 4 esquinas del bloque ya girado. x, y = esquina sup-izq de la
    huella; el giro (sentido reloj) se aplica sobre el centro de la huella."""
    recto = round(b["giro"]) % 180 == 90
    hw, hd = (b["fondo"], b["ancho"]) if recto else (b["ancho"], b["fondo"])
    cx, cy = b["x"] + hw / 2, b["y"] + hd / 2
    return [local(b, cx, cy, lx, ly) for lx, ly in
            ((-b["ancho"] / 2, -b["fondo"] / 2), (b["ancho"] / 2, -b["fondo"] / 2),
             (b["ancho"] / 2, b["fondo"] / 2), (-b["ancho"] / 2, b["fondo"] / 2))]


def local(b: dict, cx: float, cy: float, lx: float, ly: float) -> tuple[float, float]:
    t = math.radians(b["giro"])
    return cx + lx * math.cos(t) - ly * math.sin(t), cy + lx * math.sin(t) + ly * math.cos(t)


def centro(poli):
    return sum(p[0] for p in poli) / len(poli), sum(p[1] for p in poli) / len(poli)


def area(poli) -> float:
    """Área con signo (shoelace)."""
    return sum(poli[i][0] * poli[(i + 1) % len(poli)][1] - poli[(i + 1) % len(poli)][0] * poli[i][1]
               for i in range(len(poli))) / 2


def cruz(o, a, b) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def dentro(p, poli) -> bool:
    """Punto dentro de un polígono convexo (en cualquier sentido de giro)."""
    s = 1 if area(poli) > 0 else -1
    return all(s * cruz(poli[i], poli[(i + 1) % len(poli)], p) >= -1e-6 for i in range(len(poli)))


def insetar(poli, r: float):
    """Polígono interior a distancia r de cada lado (el retiro)."""
    if r <= 0:
        return poli
    s = 1 if area(poli) > 0 else -1
    n = len(poli)
    lineas = []
    for i in range(n):
        a, b = poli[i], poli[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        nx, ny = -dy / L * r * s, dx / L * r * s
        lineas.append(((a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny)))
    out = []
    for i in range(n):
        (p1, p2), (p3, p4) = lineas[i - 1], lineas[i]
        d = (p1[0] - p2[0]) * (p3[1] - p4[1]) - (p1[1] - p2[1]) * (p3[0] - p4[0])
        u = p1[0] * p2[1] - p1[1] * p2[0]
        v = p3[0] * p4[1] - p3[1] * p4[0]
        out.append(((u * (p3[0] - p4[0]) - (p1[0] - p2[0]) * v) / d,
                    (u * (p3[1] - p4[1]) - (p1[1] - p2[1]) * v) / d))
    return out


def se_superponen(P, Q) -> bool:
    """Ejes separadores; que dos bloques solo se toquen no cuenta."""
    for poli in (P, Q):
        for i in range(len(poli)):
            a, b = poli[i], poli[(i + 1) % len(poli)]
            ex, ey = -(b[1] - a[1]), b[0] - a[0]
            L = math.hypot(ex, ey)
            pp = [(p[0] * ex + p[1] * ey) / L for p in P]
            qq = [(q[0] * ex + q[1] * ey) / L for q in Q]
            if max(pp) <= min(qq) + 0.01 or max(qq) <= min(pp) + 0.01:
                return False
    return True


def segmentos_cruzan(a, b, c, d) -> bool:
    d1, d2, d3, d4 = cruz(c, d, a), cruz(c, d, b), cruz(a, b, c), cruz(a, b, d)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def curvas_que_cruza(poli, curvas) -> int:
    n = 0
    for c in curvas:
        toca = any(dentro(p, poli) for p in c) or any(
            segmentos_cruzan(c[i], c[i + 1], poli[j], poli[(j + 1) % len(poli)])
            for i in range(len(c) - 1) for j in range(len(poli)))
        n += toca
    return n


def revisar(data: dict) -> list[tuple[dict, list[str], int]]:
    lote = [(v["x"], v["y"]) for v in data["vertices"]]
    retiro = data["config"].get("retiro", 0)
    zona = insetar(lote, retiro)
    polis = {b["id"]: esquinas(b) for b in data["bloques"]}
    problemas = {b["id"]: [] for b in data["bloques"]}
    for b in data["bloques"]:
        if not all(dentro(p, lote) for p in polis[b["id"]]):
            problemas[b["id"]].append("se sale del lote")
        elif retiro > 0 and not all(dentro(p, zona) for p in polis[b["id"]]):
            problemas[b["id"]].append("invade el retiro")
    bs = data["bloques"]
    for i in range(len(bs)):
        for j in range(i + 1, len(bs)):
            if se_superponen(polis[bs[i]["id"]], polis[bs[j]["id"]]):
                problemas[bs[i]["id"]].append(f"se monta sobre {bs[j]['nombre']}")
                problemas[bs[j]["id"]].append(f"se monta sobre {bs[i]['nombre']}")
    return [(b, problemas[b["id"]], curvas_que_cruza(polis[b["id"]], data["curvas"])) for b in bs]


# ---------------------------------------------------------------------------
# Dibujo
# ---------------------------------------------------------------------------
def dibujar_rejilla(lote) -> str:
    xs, ys = [p[0] for p in lote], [p[1] for p in lote]
    out = []
    for x in range(math.floor(min(xs)), math.ceil(max(xs)) + 1):
        (x1, y1), (x2, y2) = px(x, min(ys)), px(x, max(ys))
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
    for y in range(math.floor(min(ys)), math.ceil(max(ys)) + 1):
        (x1, y1), (x2, y2) = px(min(xs), y), px(max(xs), y)
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
    return (f'<g clip-path="url(#clipLote)" stroke="{COLOR_REJILLA}" stroke-width="0.8">'
            + "".join(out) + "</g>")


def dibujar_linderos(vertices) -> str:
    """Nombre y medida de cada lado, por fuera del lote y siempre legible."""
    lote = [(v["x"], v["y"]) for v in vertices]
    s = 1 if area(lote) > 0 else -1
    out = []
    for i, v in enumerate(vertices):
        a, b = lote[i], lote[(i + 1) % len(lote)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        # normal hacia afuera (la opuesta a la que usa insetar)
        mx, my = (a[0] + b[0]) / 2 + dy / L * 0.9 * s, (a[1] + b[1]) / 2 - dx / L * 0.9 * s
        ang = math.degrees(math.atan2(dy, dx))
        if ang > 90:
            ang -= 180
        if ang < -90:
            ang += 180
        x, y = px(mx, my)
        medida = v["longitud_plano"] if v["longitud_plano"] else L
        out.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="12" fill="{COLOR_TEXTO_SEC}" text-anchor="middle" '
            f'dominant-baseline="middle" transform="rotate({ang:.2f} {x:.1f} {y:.1f})">'
            f'{medida:.2f} m · {esc(v["lindero"])}</text>')
    return "\n".join(out)


def dibujar_sube(cfg) -> str:
    ax, ay = cfg.get("esquina_alta_x"), cfg.get("esquina_alta_y")
    if ax is None or ay is None:
        return ""
    (x1, y1), (x2, y2) = px(ax - 6, ay + 5), px(ax - 1.4, ay + 1.2)
    tx, ty = px(ax - 6.3, ay + 6)
    return (
        f'<defs><marker id="flechaSube" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
        f'<path d="M0,0 L10,5 L0,10 Z" fill="{COLOR_RETIRO}"/></marker></defs>'
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{COLOR_RETIRO}" '
        f'stroke-width="2.4" marker-end="url(#flechaSube)"/>'
        f'<text x="{tx:.1f}" y="{ty + 10:.1f}" font-size="12" font-weight="700" fill="{COLOR_RETIRO}" '
        f'text-anchor="middle">SUBE · parte alta</text>')


def dibujar_brujula(cx: float, cy: float, azimut: float) -> str:
    """Brújula girada hacia el norte real; las letras se leen derechas."""
    letras = (("N", 0, -36, 15, "700"), ("S", 0, 36, 12, "400"),
              ("OR", 38, 0, 12, "400"), ("OCC", -42, 0, 12, "400"))
    out = [f'<g transform="translate({cx:.1f},{cy:.1f}) rotate({azimut:.1f})">',
           f'<circle r="21" fill="none" stroke="{COLOR_LOTE}" stroke-width="1.5"/>',
           f'<path d="M0,-28 L8.5,7.6 L0,1.9 L-8.5,7.6 Z" fill="{COLOR_LOTE}"/>']
    for txt, lx, ly, size, peso in letras:
        out.append(
            f'<text x="{lx}" y="{ly}" font-size="{size}" font-weight="{peso}" fill="{COLOR_LOTE}" '
            f'text-anchor="middle" dominant-baseline="middle" transform="rotate({-azimut:.1f} {lx} {ly})">{txt}</text>')
    out.append("</g>")
    return "\n".join(out)


def dibujar_bloque(b: dict, mal: bool, interior: str | None = None) -> str:
    """Bloque como masa de color, o -- si llega `interior` (SVG ya ubicado) --
    con sus zonas internas dentro y solo el contorno encima."""
    poli = esquinas(b)
    cxm, cym = centro(poli)
    if interior is not None:
        color = COLOR_MAL if mal else COLOR_LOTE
        out = [interior, f'<polygon points="{puntos(poli)}" fill="none" stroke="{color}" '
                         f'stroke-width="3.5" stroke-linejoin="miter"/>']
        if b["marca_frente"]:
            f = b["fondo"] / 2
            tri = [local(b, cxm, cym, -0.5, f + 0.25), local(b, cxm, cym, 0.5, f + 0.25),
                   local(b, cxm, cym, 0, f + 0.95)]
            out.append(f'<polygon points="{puntos(tri)}" fill="{COLOR_LOTE}"/>')
        return "\n".join(out)
    trazo = f'stroke="{COLOR_MAL}" stroke-width="3"' if mal else f'stroke="{COLOR_LOTE}" stroke-width="1.6"'
    out = [f'<polygon points="{puntos(poli)}" fill="{b["color"]}" fill-opacity="0.9" {trazo}/>']
    if b["marca_frente"]:
        # triángulo por fuera del lado del frente (local +y = 'fondo' de abajo)
        f = b["fondo"] / 2
        tri = [local(b, cxm, cym, -0.5, f + 0.12), local(b, cxm, cym, 0.5, f + 0.12),
               local(b, cxm, cym, 0, f + 0.85)]
        out.append(f'<polygon points="{puntos(tri)}" fill="{COLOR_LOTE}"/>')
    x, y = px(cxm, cym)
    for yy, txt, size, peso in ((y - 2, b["nombre"], 14, "700"),
                                (y + 15, f'{b["ancho"]:g} × {b["fondo"]:g} m', 11, "400")):
        out.append(f'<text x="{x:.1f}" y="{yy:.1f}" font-size="{size}" font-weight="{peso}" '
                   f'text-anchor="middle" fill="#ffffff" stroke="#ffffff" stroke-width="3" paint-order="stroke">{esc(txt)}</text>')
        out.append(f'<text x="{x:.1f}" y="{yy:.1f}" font-size="{size}" font-weight="{peso}" '
                   f'text-anchor="middle" fill="{COLOR_LOTE}">{esc(txt)}</text>')
    return "\n".join(out)


def dibujar_escala(x0: float, y0: float) -> str:
    out = []
    for i in range(5):
        fill = COLOR_LOTE if i % 2 == 0 else "#ffffff"
        out.append(f'<rect x="{x0 + i * SCALE:.1f}" y="{y0:.1f}" width="{SCALE:.1f}" height="6" '
                   f'fill="{fill}" stroke="{COLOR_LOTE}" stroke-width="1"/>')
    out.append(f'<text x="{x0:.1f}" y="{y0 + 20:.1f}" font-size="11" fill="{COLOR_TEXTO_SEC}">0</text>')
    out.append(f'<text x="{x0 + 5 * SCALE:.1f}" y="{y0 + 20:.1f}" font-size="11" fill="{COLOR_TEXTO_SEC}" '
               f'text-anchor="middle">5 m</text>')
    return "\n".join(out)


def generar_svg(data: dict, interiores: dict[str, str] | None = None,
                titulo: str = "Lote 22 · implantación de la casa",
                notas_extra: list[str] | None = None) -> tuple[str, list]:
    """`interiores` (opcional): {id_bloque: SVG de sus zonas ya ubicado en el
    lote}; lo usa generate_implantacion_svg.py. `notas_extra`: líneas que se
    agregan al final, debajo de la revisión."""
    interiores = interiores or {}
    cfg = data["config"]
    lote = [(v["x"], v["y"]) for v in data["vertices"]]
    revision = revisar(data)
    partes = [
        f'<defs><clipPath id="clipLote"><polygon points="{puntos(lote)}"/></clipPath></defs>',
        f'<polygon points="{puntos(lote)}" fill="#fbfaf6"/>',
        dibujar_rejilla(lote),
    ]
    partes += [f'<polyline points="{puntos(c)}" fill="none" stroke="{COLOR_CURVA}" stroke-width="1.6" '
               f'stroke-dasharray="8 5" clip-path="url(#clipLote)"/>' for c in data["curvas"]]
    partes.append(f'<polygon points="{puntos(lote)}" fill="none" stroke="{COLOR_LOTE}" stroke-width="4" stroke-linejoin="round"/>')
    retiro = cfg.get("retiro", 0)
    if retiro > 0:
        partes.append(f'<polygon points="{puntos(insetar(lote, retiro))}" fill="none" stroke="{COLOR_RETIRO}" '
                      f'stroke-width="2" stroke-dasharray="10 6"/>')
    partes.append(dibujar_linderos(data["vertices"]))
    partes.append(dibujar_sube(cfg))
    for b, problemas, _ in revision:
        partes.append(dibujar_bloque(b, bool(problemas), interiores.get(b["id"])))

    xs, ys = [p[0] for p in lote], [p[1] for p in lote]
    bx, by = px(max(xs) + 0, min(ys) - 2.3)
    partes.append(dibujar_brujula(bx - 30, by, cfg.get("norte_azimut", 0)))

    # ---- revisión y resumen, debajo del lote -------------------------------
    y0 = px(0, max(ys))[1] + 60
    partes.append(dibujar_escala(ORIGIN_X, y0 - 30))
    partes.append(f'<text x="40" y="{y0 + 20:.1f}" font-size="15" font-weight="700" fill="{COLOR_LOTE}">Revisión</text>')
    fila = y0 + 44
    for b, problemas, n_curvas in revision:
        ok = not problemas
        estado = "bien ubicado" if ok else ", ".join(problemas)
        partes.append(
            f'<text x="40" y="{fila:.1f}" font-size="13" fill="{COLOR_OK if ok else COLOR_MAL}">'
            f'{"✓" if ok else "✗"} <tspan font-weight="700" fill="{COLOR_LOTE}">{esc(b["nombre"])}</tspan>'
            f'<tspan fill="{COLOR_TEXTO_SEC}"> · {esc(estado)} · x {b["x"]:g}, y {b["y"]:g}, giro {b["giro"]:g}° · '
            f'cruza {n_curvas} curva{"" if n_curvas == 1 else "s"} de nivel</tspan></text>')
        fila += 22
    huella = sum(b["ancho"] * b["fondo"] for b in data["bloques"])
    area_lote = abs(area(lote))
    notas = [
        f"Huella {huella:g} m² · ocupa {huella / area_lote * 100:.1f} % del lote "
        f"(≈ {area_lote:.0f} m² con las 4 medidas; el plano dice {cfg.get('area_plano', 0):g} m²).",
        "Curvas de nivel calcadas de la imagen, sin valores confirmados. Más curvas cruzadas = más corte y relleno.",
        "El triángulo negro marca el frente de la casa.",
    ] + (notas_extra or [])
    for n in notas:
        partes.append(f'<text x="40" y="{fila + 8:.1f}" font-size="12" fill="{COLOR_TEXTO_TENUE}">{esc(n)}</text>')
        fila += 20

    canvas_h = fila + 30
    cabecera = [
        f'<rect width="{CANVAS_W}" height="{canvas_h:.0f}" fill="#ffffff"/>',
        f'<text x="40" y="44" font-size="22" font-weight="700" fill="{COLOR_LOTE}">{esc(titulo)}</text>',
        f'<text x="40" y="68" font-size="13" fill="{COLOR_TEXTO_SEC}">Generado desde lote.db · arriba la parte alta (Lote 20), izquierda la vía principal</text>',
    ]
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {canvas_h:.0f}" '
        f'width="{CANVAS_W}" height="{canvas_h:.0f}" font-family="Segoe UI, Arial, sans-serif">\n'
        + "\n".join(cabecera + partes) + "\n</svg>\n"
    )
    return svg, revision


def main() -> None:
    here = Path(__file__).parent
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", default=str(here / "lote.db"))
    parser.add_argument("--out", default=str(here.parent / "planos" / "lote22_implantacion.svg"))
    args = parser.parse_args()

    svg, revision = generar_svg(cargar(Path(args.db)))
    Path(args.out).write_text(svg, encoding="utf-8")
    print(f"OK: {args.out}")
    for b, problemas, n_curvas in revision:
        print(f"  {'OK ' if not problemas else 'MAL'} {b['nombre']:<9} {', '.join(problemas) or 'bien ubicado'}"
              f" - cruza {n_curvas} curva{'' if n_curvas == 1 else 's'}")


if __name__ == "__main__":
    main()
