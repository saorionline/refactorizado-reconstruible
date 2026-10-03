#!/usr/bin/env python3
"""Genera el plano cenital (SVG) a partir de la base de datos plano.db.

Uso:
    python generate_svg.py [--db plano.db] [--out ../planos/plano_cenital_propuesta_01.svg]

Todo lo arquitectónico (zonas, muros, puertas, muebles) vive en SQLite, en
METROS reales. Este script SOLO traduce esos datos a píxeles SVG. Para
cambiar el plano (mover un muro, agrandar una zona, mover una puerta) se
edita la base de datos (ver queries_ejemplo.sql) y se vuelve a correr este
script -- no se edita el SVG a mano.
"""
from __future__ import annotations

import argparse
import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuración de dibujo (todo lo que es "nada más de SVG" vive aquí, no en
# la base de datos: escala, márgenes, colores de línea, tamaños de fuente).
# ---------------------------------------------------------------------------
SCALE = 48.0            # píxeles por metro
ORIGIN_X = 97.6          # margen izquierdo del lienzo (px) -> corresponde a x=0 m
ORIGIN_Y = 150.0         # margen superior del lienzo (px) -> corresponde a y=0 m
CANVAS_W = 1100

COLOR_MURO = "#1f2933"
COLOR_PUNTEADA = "#9aa5b1"
COLOR_COTA = "#2f7fb5"
COLOR_TEXTO_SEC = "#3e4c59"
COLOR_TEXTO_TENUE = "#7b8794"
COLOR_MUEBLE = "#52606d"

GROSOR = {"exterior": 7, "interior": 3.5, "punteada": 1}

GRUPO_TITULOS = {
    "bloque_central": "Bloque central",
    "ala_izquierda": "Ala izquierda",
    "ala_derecha": "Ala derecha",
}
GRUPO_ORDEN = ["bloque_central", "ala_izquierda", "ala_derecha"]
# columna x (px) donde arranca cada bloque del cuadro de áreas (abajo del plano)
GRUPO_COL_X = {"bloque_central": 40, "ala_izquierda": 400, "ala_derecha": 740}


def px(x_m: float, y_m: float) -> tuple[float, float]:
    """Convierte metros (coordenadas del plano) a píxeles del lienzo SVG."""
    return ORIGIN_X + x_m * SCALE, ORIGIN_Y + y_m * SCALE


def esc(texto: str) -> str:
    return (texto or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------
def cargar(db_path: Path) -> dict:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    data = {
        "zonas": [dict(r) for r in con.execute("SELECT * FROM zonas ORDER BY numero")],
        "muros": [dict(r) for r in con.execute("SELECT * FROM muros")],
        "puertas": [dict(r) for r in con.execute("SELECT * FROM puertas")],
        "modulos": [dict(r) for r in con.execute("SELECT * FROM modulos")],
        "especiales": [dict(r) for r in con.execute("SELECT * FROM elementos_especiales")],
    }
    con.close()
    return data


# ---------------------------------------------------------------------------
# Dibujo: zonas -- el RELLENO se dibuja primero (fondo del plano) y la
# ETIQUETA se dibuja al final de todo (después de muebles/puertas) para que
# el texto nunca quede tapado por un mueble u otro trazo encima.
# ---------------------------------------------------------------------------
def dibujar_zona_relleno(z: dict) -> str:
    x, y = px(z["x"], z["y"])
    w, h = z["ancho"] * SCALE, z["profundidad"] * SCALE
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{z["fill_color"]}"/>'


def dibujar_zona_etiqueta(z: dict) -> str:
    x, y = px(z["x"], z["y"])
    w, h = z["ancho"] * SCALE, z["profundidad"] * SCALE
    cx = x + w / 2
    out = []
    if z["label_mode"] == "texto":
        area = z["ancho"] * z["profundidad"]
        size_titulo = 12 if z["ancho"] >= 2.5 else 10
        size_dims = 11 if z["ancho"] >= 2.5 else 9
        y_titulo = y + max(14, min(h * 0.14, 20))
        y_dims = y + h - max(8, min(h * 0.08, 14))
        # halo blanco detrás del texto para que se lea aunque haya un mueble debajo
        for yy, txt, size, weight, color in (
            (y_titulo, z["nombre"].upper(), size_titulo, "700", "#1f2933"),
            (y_dims, f'{z["ancho"]:.2f} × {z["profundidad"]:.2f} = {area:.1f} m²', size_dims, "400", COLOR_TEXTO_SEC),
        ):
            out.append(
                f'<text x="{cx:.1f}" y="{yy:.1f}" font-size="{size}" font-weight="{weight}" '
                f'text-anchor="middle" fill="#ffffff" stroke="#ffffff" stroke-width="3" '
                f'paint-order="stroke">{esc(txt)}</text>'
            )
            out.append(
                f'<text x="{cx:.1f}" y="{yy:.1f}" font-size="{size}" font-weight="{weight}" '
                f'text-anchor="middle" fill="{color}">{esc(txt)}</text>'
            )
    elif z["label_mode"] == "circulo":
        ccx, ccy = x + w / 2, y + h / 2
        r = 8 if z["ancho"] >= 1.2 else 7
        out.append(f'<circle cx="{ccx:.1f}" cy="{ccy:.1f}" r="{r}" fill="{z["numero_color"]}"/>')
        out.append(
            f'<text x="{ccx:.1f}" y="{ccy + 4:.1f}" font-size="11" font-weight="700" '
            f'text-anchor="middle" fill="#fff">{z["numero"]}</text>'
        )
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Dibujo: muros
# ---------------------------------------------------------------------------
def dibujar_muro(m: dict) -> str:
    x1, y1 = px(m["x1"], m["y1"])
    x2, y2 = px(m["x2"], m["y2"])
    grosor = GROSOR[m["tipo"]]
    if m["tipo"] == "punteada":
        return (
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{COLOR_PUNTEADA}" stroke-width="{grosor}" stroke-dasharray="5 4"/>'
        )
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{COLOR_MURO}" stroke-width="{grosor}" stroke-linecap="square"/>'
    )


# ---------------------------------------------------------------------------
# Dibujo: puertas (hueco blanco + hoja + arco de giro)
# ---------------------------------------------------------------------------
def dibujar_puerta(p: dict) -> str:
    eje, cx_m, cy_m, ancho = p["eje"], p["x"], p["y"], p["ancho"]
    out = []

    if eje == "x":
        x_a, _ = px(cx_m - ancho / 2, cy_m)
        x_b, y = px(cx_m + ancho / 2, cy_m)
        hinge_x = x_a if p["bisagra"] == "izquierda" else x_b
        free_x = x_b if p["bisagra"] == "izquierda" else x_a
        dy = -ancho * SCALE if p["hacia"] == "fondo" else ancho * SCALE
        panel_x, panel_y = hinge_x, y + dy
        free_pt = (free_x, y)
        hinge_pt = (hinge_x, y)
    else:  # eje == 'y'
        _, y_a = px(cx_m, cy_m - ancho / 2)
        x, y_b = px(cx_m, cy_m + ancho / 2)
        hinge_y = y_a if p["bisagra"] == "fondo" else y_b
        free_y = y_b if p["bisagra"] == "fondo" else y_a
        dx = -ancho * SCALE if p["hacia"] == "izquierda" else ancho * SCALE
        panel_x, panel_y = x + dx, hinge_y
        free_pt = (x, free_y)
        hinge_pt = (x, hinge_y)

    # hueco: borra el muro con una línea blanca gruesa
    gx1, gy1 = (x_a, y) if eje == "x" else (x, y_a)
    gx2, gy2 = (x_b, y) if eje == "x" else (x, y_b)
    out.append(
        f'<line x1="{gx1:.1f}" y1="{gy1:.1f}" x2="{gx2:.1f}" y2="{gy2:.1f}" '
        f'stroke="#ffffff" stroke-width="11"/>'
    )
    # hoja de la puerta (de la bisagra hacia dentro)
    out.append(
        f'<line x1="{hinge_pt[0]:.1f}" y1="{hinge_pt[1]:.1f}" x2="{panel_x:.1f}" y2="{panel_y:.1f}" '
        f'stroke="{COLOR_MURO}" stroke-width="1.6"/>'
    )
    # arco de giro: cuadrante entre el extremo libre y el extremo de la hoja
    radio = ancho * SCALE
    v1 = (free_pt[0] - hinge_pt[0], free_pt[1] - hinge_pt[1])
    v2 = (panel_x - hinge_pt[0], panel_y - hinge_pt[1])
    cross = v1[0] * v2[1] - v1[1] * v2[0]
    sweep = 1 if cross > 0 else 0
    out.append(
        f'<path d="M {free_pt[0]:.1f} {free_pt[1]:.1f} A {radio:.1f} {radio:.1f} 0 0 {sweep} '
        f'{panel_x:.1f} {panel_y:.1f}" fill="none" stroke="{COLOR_MUEBLE}" stroke-width="0.9" '
        f'stroke-dasharray="3 3"/>'
    )
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Dibujo: módulos (mobiliario esquemático)
# ---------------------------------------------------------------------------
def dibujar_modulo(m: dict) -> str:
    forma = m["forma"]
    if forma == "circulo":
        cx, cy = px(m["x"], m["y"])
        r = m["radio"] * SCALE
        return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="none" stroke="{COLOR_MUEBLE}"/>'
    if forma == "elipse":
        cx, cy = px(m["x"], m["y"])
        rx, ry = m["ancho"] * SCALE / 2, m["profundidad"] * SCALE / 2
        return (
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
            f'fill="#ffffff" stroke="{COLOR_MUEBLE}" stroke-width="1.2"/>'
        )
    x, y = px(m["x"], m["y"])
    w, h = m["ancho"] * SCALE, m["profundidad"] * SCALE
    if forma == "ducha":
        return (
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="#ffffff" '
            f'stroke="{COLOR_MUEBLE}" stroke-width="1"/>\n'
            f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x+w:.1f}" y2="{y+h:.1f}" stroke="{COLOR_TEXTO_TENUE}" stroke-width="0.8"/>\n'
            f'<line x1="{x+w:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y+h:.1f}" stroke="{COLOR_TEXTO_TENUE}" stroke-width="0.8"/>'
        )
    if forma == "cama":
        banda = min(h * 0.18, 16)
        return (
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="2.4" fill="#ffffff" '
            f'stroke="{COLOR_MUEBLE}" stroke-width="1.2"/>\n'
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{banda:.1f}" fill="#f3ece0" '
            f'stroke="{COLOR_MUEBLE}" stroke-width="1"/>'
        )
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="2.4" fill="#ffffff" stroke="{COLOR_MUEBLE}" stroke-width="1"/>'


# ---------------------------------------------------------------------------
# Dibujo: elementos especiales (alero, escalinata) -- sin área, fuera de huella
# ---------------------------------------------------------------------------
def dibujar_especial(e: dict) -> str:
    x, y = px(e["x"], e["y"])
    w, h = e["ancho"] * SCALE, e["profundidad"] * SCALE
    out = []
    if e["tipo"] == "alero":
        out.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="none" '
            f'stroke="{COLOR_PUNTEADA}" stroke-width="1" stroke-dasharray="4 3"/>'
        )
        n = 5
        for i in range(n):
            x0 = x + 8 + i * (w - 16) / (n - 1)
            out.append(
                f'<line x1="{x0:.1f}" y1="{y+h:.1f}" x2="{x0+30:.1f}" y2="{y:.1f}" '
                f'stroke="#c6ccd1" stroke-width="1"/>'
            )
        out.append(
            f'<text x="{x+w/2:.1f}" y="{y+h/2+4:.1f}" font-size="9" text-anchor="middle" '
            f'fill="{COLOR_TEXTO_TENUE}">{esc(e["etiqueta"])}</text>'
        )
    elif e["tipo"] == "escalinata":
        for i in range(11):
            gy = y - 66 + i * 6
            out.append(f'<line x1="{x:.1f}" y1="{gy:.1f}" x2="{x+w:.1f}" y2="{gy:.1f}" stroke="#c9d8bd" stroke-width="0.8"/>')
        n_pel = 4
        for i in range(n_pel):
            sy = y + i * (h / n_pel)
            out.append(
                f'<rect x="{x:.1f}" y="{sy:.1f}" width="{w:.1f}" height="{h/n_pel:.1f}" '
                f'fill="#efefef" stroke="{COLOR_MURO}" stroke-width="1"/>'
            )
        out.append(
            f'<text x="{x+w/2:.1f}" y="{y+h+20:.1f}" font-size="11" text-anchor="middle" '
            f'fill="{COLOR_TEXTO_SEC}">{esc(e["etiqueta"])}</text>'
        )
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Cotas (dimensiones): se calculan a partir del bounding box de cada grupo,
# nunca se escriben a mano.
# ---------------------------------------------------------------------------
def bbox(zonas: list[dict], grupo: str | None = None) -> tuple[float, float, float, float]:
    sel = [z for z in zonas if grupo is None or z["grupo"] == grupo]
    x0 = min(z["x"] for z in sel)
    y0 = min(z["y"] for z in sel)
    x1 = max(z["x"] + z["ancho"] for z in sel)
    y1 = max(z["y"] + z["profundidad"] for z in sel)
    return x0, y0, x1, y1


def cota_horizontal(x0_m, x1_m, y_m, etiqueta, offset_px=0) -> str:
    x0, y = px(x0_m, y_m)
    x1, _ = px(x1_m, y_m)
    y += offset_px
    mid = (x0 + x1) / 2
    out = [
        f'<line x1="{x0:.1f}" y1="{y:.1f}" x2="{x1:.1f}" y2="{y:.1f}" stroke="{COLOR_COTA}"/>',
        f'<line x1="{x0:.1f}" y1="{y-5:.1f}" x2="{x0:.1f}" y2="{y+5:.1f}" stroke="{COLOR_COTA}"/>',
        f'<line x1="{x1:.1f}" y1="{y-5:.1f}" x2="{x1:.1f}" y2="{y+5:.1f}" stroke="{COLOR_COTA}"/>',
        f'<text x="{mid:.1f}" y="{y-6:.1f}" font-size="11" fill="{COLOR_COTA}" text-anchor="middle">{etiqueta}</text>',
    ]
    return "\n".join(out)


def cota_vertical(y0_m, y1_m, x_m, etiqueta, offset_px=0) -> str:
    x, y0 = px(x_m, y0_m)
    _, y1 = px(x_m, y1_m)
    x += offset_px
    mid = (y0 + y1) / 2
    out = [
        f'<line x1="{x:.1f}" y1="{y0:.1f}" x2="{x:.1f}" y2="{y1:.1f}" stroke="{COLOR_COTA}"/>',
        f'<line x1="{x-5:.1f}" y1="{y0:.1f}" x2="{x+5:.1f}" y2="{y0:.1f}" stroke="{COLOR_COTA}"/>',
        f'<line x1="{x-5:.1f}" y1="{y1:.1f}" x2="{x+5:.1f}" y2="{y1:.1f}" stroke="{COLOR_COTA}"/>',
        f'<text x="{x-8:.1f}" y="{mid:.1f}" font-size="11" fill="{COLOR_COTA}" text-anchor="middle" '
        f'transform="rotate(-90 {x-8:.1f} {mid:.1f})">{etiqueta}</text>',
    ]
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Cuadro de áreas (leyenda): calculado por grupo, no escrito a mano.
# ---------------------------------------------------------------------------
@dataclass
class Leyenda:
    svg: str
    alto_total_px: float


def construir_leyenda(zonas: list[dict], y0: float) -> Leyenda:
    fila_h = 20
    out: list[str] = []
    col_bottoms: dict[str, float] = {}

    por_grupo: dict[str, list[dict]] = {g: [] for g in GRUPO_ORDEN}
    for z in zonas:
        por_grupo[z["grupo"]].append(z)

    out.append(f'<line x1="40" y1="{y0:.1f}" x2="1060" y2="{y0:.1f}" stroke="#cbd2d9"/>')
    out.append(f'<text x="40" y="{y0+20:.1f}" font-size="16" font-weight="700" fill="#1f2933">Cuadro de áreas</text>')
    y_start = y0 + 48

    for grupo in GRUPO_ORDEN:
        x0 = GRUPO_COL_X[grupo]
        zs = sorted(por_grupo[grupo], key=lambda z: z["numero"])
        utiles = [z for z in zs if z["cuenta_area"]]
        no_utiles = [z for z in zs if not z["cuenta_area"]]
        area_util = sum(z["ancho"] * z["profundidad"] for z in utiles)
        area_no_util = sum(z["ancho"] * z["profundidad"] for z in no_utiles)

        titulo = GRUPO_TITULOS[grupo]
        if area_no_util:
            titulo += f" — {area_util:.1f} útiles + {area_no_util:.1f} zona techada (no útil)"
        else:
            titulo += f" {area_util:.1f} m²"
        out.append(f'<text x="{x0}" y="{y_start:.1f}" font-size="12.5" font-weight="700" fill="#52606d">{esc(titulo)}</text>')

        y = y_start + fila_h
        for z in utiles + no_utiles:
            es_util = z in utiles
            color = "#1f2933" if es_util else "#6b7682"
            dimcolor = COLOR_TEXTO_SEC if es_util else COLOR_PUNTEADA
            sufijo = ""
            out.append(f'<circle cx="{x0+9}" cy="{y-4:.1f}" r="9" fill="{color}"/>')
            out.append(f'<text x="{x0+9}" y="{y:.1f}" font-size="11" font-weight="700" text-anchor="middle" fill="#fff">{z["numero"]}</text>')
            out.append(f'<text x="{x0+26}" y="{y:.1f}" font-size="12.5" fill="{color}">{esc(z["nombre"])}{sufijo}</text>')
            out.append(f'<text x="{x0+205}" y="{y:.1f}" font-size="12.5" fill="{dimcolor}" text-anchor="end">{z["ancho"]:.2f} × {z["profundidad"]:.2f}</text>')
            out.append(f'<text x="{x0+270}" y="{y:.1f}" font-size="12.5" font-weight="700" fill="{color}" text-anchor="end">{z["ancho"]*z["profundidad"]:.1f}</text>')
            y += fila_h
            if es_util and z is utiles[-1] and no_utiles:
                out.append(f'<line x1="{x0}" y1="{y-10:.1f}" x2="{x0+270}" y2="{y-10:.1f}" stroke="#9aa5b1"/>')
                out.append(f'<text x="{x0+26}" y="{y+6:.1f}" font-size="12.5" font-weight="700" fill="#1f2933">Subtotal útil</text>')
                out.append(f'<text x="{x0+270}" y="{y+6:.1f}" font-size="12.5" font-weight="700" text-anchor="end" fill="#1f2933">{area_util:.1f}</text>')
                y += fila_h

        out.append(f'<line x1="{x0}" y1="{y-10:.1f}" x2="{x0+270}" y2="{y-10:.1f}" stroke="#9aa5b1"/>')
        etiqueta_sub = "Zona techada (sin útil)" if no_utiles and not utiles else "Subtotal" if utiles else "Zona techada (sin útil)"
        if utiles and no_utiles:
            etiqueta_sub = "Zona techada (sin útil)"
            valor_sub = area_no_util
        elif utiles:
            etiqueta_sub = "Subtotal"
            valor_sub = area_util
        else:
            valor_sub = area_no_util
        out.append(f'<text x="{x0+26}" y="{y+6:.1f}" font-size="12.5" font-weight="700" fill="#1f2933">{etiqueta_sub}</text>')
        out.append(f'<text x="{x0+270}" y="{y+6:.1f}" font-size="12.5" font-weight="700" text-anchor="end" fill="#1f2933">{valor_sub:.1f}</text>')
        col_bottoms[grupo] = y + fila_h

    alto = max(col_bottoms.values()) - y0 + 40
    return Leyenda("\n".join(out), alto)


# ---------------------------------------------------------------------------
# Ensamblado principal
# ---------------------------------------------------------------------------
def generar_svg(data: dict) -> str:
    zonas = data["zonas"]
    partes: list[str] = []

    # 1) rellenos de zonas (solo el fondo de color; las etiquetas se dibujan
    #    al final, paso 5, para que ningún mueble las tape)
    for z in zonas:
        partes.append(dibujar_zona_relleno(z))

    # 2) elementos especiales (alero) van detrás de los muros para que el
    #    marco de la casa quede siempre al frente
    for e in data["especiales"]:
        if e["tipo"] == "alero":
            partes.append(dibujar_especial(e))

    for e in data["especiales"]:
        if e["tipo"] == "escalinata":
            partes.append(dibujar_especial(e))

    # 3) muros
    for m in data["muros"]:
        partes.append(dibujar_muro(m))

    # 4) puertas (encima de los muros, para cortarlos visualmente)
    for p in data["puertas"]:
        partes.append(dibujar_puerta(p))

    # 5) mobiliario
    for mod in data["modulos"]:
        partes.append(dibujar_modulo(mod))

    # 5b) etiquetas de zona: AL FINAL, encima de todo lo anterior (con halo
    #     blanco) para que nunca queden tapadas por un mueble.
    for z in zonas:
        partes.append(dibujar_zona_etiqueta(z))

    # 6) cotas globales, calculadas del bounding box real de los datos
    x0_all, y0_all, x1_all, y1_all = bbox(zonas)
    x0_c, y0_c, x1_c, y1_c = bbox(zonas, "bloque_central")
    x0_i, y0_i, x1_i, y1_i = bbox(zonas, "ala_izquierda")
    x0_d, y0_d, x1_d, y1_d = bbox(zonas, "ala_derecha")

    y_cotas_h = y1_i + 1.3
    partes.append(cota_horizontal(x0_i, x1_i, y_cotas_h, f"{x1_i-x0_i:.2f}"))
    partes.append(cota_horizontal(x0_c, x1_c, y_cotas_h, f"{x1_c-x0_c:.2f}"))
    partes.append(cota_horizontal(x0_d, x1_d, y_cotas_h, f"{x1_d-x0_d:.2f}"))
    partes.append(cota_horizontal(x0_all, x1_all, y_cotas_h + 0.7, f"{x1_all-x0_all:.2f} m (largo total)"))

    partes.append(cota_vertical(y0_i, y1_i, x0_all - 0.8, f"{y1_i-y0_i:.2f}"))
    partes.append(cota_vertical(y0_d, y1_d, x1_all + 0.8, f"{y1_d-y0_d:.2f}"))
    partes.append(cota_vertical(y0_c, y1_c, x1_all + 1.5, f"{y1_c-y0_c:.2f}"))

    # 7) etiqueta de acceso (bajo la escalinata, si hay una definida)
    escalinatas = [e for e in data["especiales"] if e["tipo"] == "escalinata"]
    if escalinatas:
        e = escalinatas[0]
        cx, cy = px(e["x"] + e["ancho"] / 2, e["y"] + e["profundidad"] + 1.0)
        partes.append(
            f'<g transform="translate({cx:.1f},{cy:.1f})">'
            f'<path d="M0,12 L0,-8 M-6,-2 L0,-8 L6,-2" fill="none" stroke="{COLOR_MURO}" stroke-width="1.6"/>'
            f'<text x="12" y="6" font-size="12" fill="{COLOR_MURO}">FRENTE · ACCESO PRINCIPAL</text></g>'
        )
        escala_y = cy + 33.6
        for i in range(5):
            ex = x1_all * SCALE + ORIGIN_X + i * 48
            fill = COLOR_MURO if i % 2 == 0 else "#fff"
            partes.append(f'<rect x="{ex:.1f}" y="{escala_y:.1f}" width="48" height="7" fill="{fill}" stroke="{COLOR_MURO}" stroke-width="1"/>')
        partes.append(f'<text x="{x1_all*SCALE+ORIGIN_X:.1f}" y="{escala_y+21:.1f}" font-size="11" fill="{COLOR_MURO}">0</text>')
        partes.append(f'<text x="{x1_all*SCALE+ORIGIN_X+240:.1f}" y="{escala_y+21:.1f}" font-size="11" text-anchor="middle" fill="{COLOR_MURO}">5 m</text>')
        y_leyenda = escala_y + 50
    else:
        y_leyenda = y0_all * SCALE + ORIGIN_Y + 400

    # 8) cuadro de áreas (calculado), totales
    leyenda = construir_leyenda(zonas, y_leyenda)
    partes.append(leyenda.svg)

    area_util = sum(z["ancho"] * z["profundidad"] for z in zonas if z["cuenta_area"])
    area_techada = sum(z["ancho"] * z["profundidad"] for z in zonas if not z["cuenta_area"])
    y_total = y_leyenda + leyenda.alto_total_px
    partes.append(f'<line x1="40" y1="{y_total:.1f}" x2="1060" y2="{y_total:.1f}" stroke="#cbd2d9"/>')
    partes.append(
        f'<text x="1060" y="{y_total+20:.1f}" font-size="15" font-weight="700" text-anchor="end" fill="#1f2933">'
        f'TOTAL ÚTIL: {area_util:.1f} m² ({area_util+area_techada:.1f} m² techados)</text>'
    )
    partes.append(
        f'<text x="40" y="{y_total+20:.1f}" font-size="11" fill="{COLOR_TEXTO_TENUE}">'
        f'Elementos especiales (alero/escalinata) fuera de la huella, no suman. Mobiliario esquemático.</text>'
    )
    canvas_h = y_total + 50

    # 9) encabezado (al final para poder referenciar canvas_h ya calculado)
    header = [
        f'<rect width="{CANVAS_W}" height="{canvas_h:.0f}" fill="#ffffff"/>',
        '<text x="40" y="44" font-size="24" font-weight="700" fill="#1f2933">ARQUITECTURA TINY HOUSE · PROPUESTA 01</text>',
        f'<text x="40" y="70" font-size="15" fill="#52606d">Plano cenital · Bloque central + dos alas · '
        f'{area_util:.0f} m² útiles ({area_util+area_techada:.0f} m² techados)</text>',
        '<text x="40" y="92" font-size="12" fill="#7b8794">Generado automáticamente desde plano.db '
        '(herramientas/generate_svg.py). Medidas a caras interiores, sin espesor de muros.</text>',
    ]

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {canvas_h:.0f}" '
        f'width="{CANVAS_W}" height="{canvas_h:.0f}" font-family="Segoe UI, Arial, sans-serif">\n'
        + "\n".join(header) + "\n" + "\n".join(partes) + "\n</svg>\n"
    )
    return svg


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=str(Path(__file__).parent / "plano.db"))
    ap.add_argument("--out", default=str(Path(__file__).parent.parent / "planos" / "plano_cenital_propuesta_01.svg"))
    args = ap.parse_args()

    data = cargar(Path(args.db))
    svg = generar_svg(data)
    Path(args.out).write_text(svg, encoding="utf-8")
    print(f"OK: {len(data['zonas'])} zonas, {len(data['muros'])} muros, {len(data['puertas'])} puertas, "
          f"{len(data['modulos'])} módulos -> {args.out}")


if __name__ == "__main__":
    main()
