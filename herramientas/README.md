# Herramientas del plano (SQLite + Python)

Antes, cada cambio al plano ("mueve este muro", "este baño ya no cuenta como
área") significaba editar a mano cientos de coordenadas dentro de un SVG de
~350 líneas. Eso es lento y muy fácil de romper sin darse cuenta (así pasó:
un muro faltante, una puerta que no coincidía con el muro nuevo, etc.).

Ahora la geometría real (zonas, muros, puertas, muebles) vive en una base de
datos SQLite (`plano.db`), en **metros reales**, no en píxeles. Un script de
Python (`generate_svg.py`) traduce esa base de datos al SVG. Para cambiar el
plano: se edita la base de datos (con una consulta SQL) y se vuelve a correr
el script. El SVG nunca se edita a mano.

## Requisitos

Python 3.10+ (incluye `sqlite3` en la librería estándar, no hace falta
instalar nada más). Verifica con:

```bash
python --version
```

## Archivos

| Archivo | Qué es |
|---|---|
| `schema.sql` | Define las tablas (`zonas`, `muros`, `puertas`, `modulos`, `elementos_especiales`) y carga los datos actuales del plano de 120 m². |
| `plano.db` | La base de datos SQLite generada a partir de `schema.sql` (no se versiona el contenido a mano, se reconstruye con el comando de abajo). |
| `generate_svg.py` | Lee `plano.db` y escribe `../planos/plano_cenital_propuesta_01.svg`. |
| `queries_ejemplo.sql` | Recetario de consultas: ver muros de una zona, cambiar un muro de A a B, mover una puerta, resumen de áreas, chequeos de consistencia. |
| `check_md_sync.py` | Compara `documentos/propuesta_01_cuadro_de_areas_v2.md` contra `plano.db` y avisa si un número/área quedó desincronizado entre ambos documentos. |
| `init_db.py` | (Re)crea `plano.db` desde cero a partir de `schema.sql`. |
| `run_sql.py` | Corre un archivo `.sql` contra `plano.db` (para no pelear con comillas del shell). |

## Flujo de trabajo

### 1. Reconstruir la base de datos (solo la primera vez, o si editaste `schema.sql`)

```bash
cd herramientas
python init_db.py
```

### 2. Hacer un cambio puntual (sin tocar `schema.sql`)

Escribe la consulta en un archivo `.sql` (ver `queries_ejemplo.sql` para el
patrón) y aplícala:

```bash
python run_sql.py mi_cambio.sql
```

(o con cualquier cliente SQLite, como la extensión *SQLite Viewer* de VS Code,
que deja editar las tablas con una interfaz tipo Excel).

### 3. Regenerar el plano

```bash
python generate_svg.py
```

Esto reescribe `../planos/plano_cenital_propuesta_01.svg` completo en menos
de un segundo, con las cotas y el cuadro de áreas recalculados automáticamente
(nunca hay que corregir un subtotal a mano).

### 4. (Opcional) Verificar que el Markdown siga de acuerdo con la base de datos

```bash
python check_md_sync.py
```

## Cómo pensar los datos

- **Todo está en metros**, con origen (0,0) en la esquina de fondo del ala
  izquierda. El eje X crece hacia la derecha (ala izq. → central → ala der.);
  el eje Y crece hacia el frente (fondo de la casa → entrada).
- **`zonas`**: cada cuarto. `cuenta_area=0` marca una "zona techada" que no
  suma al área útil (como el baño de invitados y la bodega hoy).
- **`muros`**: `tipo='exterior'` (línea gruesa), `'interior'` (línea media,
  separación real entre dos zonas) o `'punteada'` (sin muro real: planta
  abierta o borde de una zona techada).
- **`puertas`**: un hueco sobre un muro, con bisagra y sentido de giro.
- **`modulos`**: mobiliario esquemático dentro de una zona.
- **`elementos_especiales`**: cosas sin área (el alero, la escalinata).

## Ejemplo: "cambia el muro de A a B"

> "Quiero que el muro entre el estudio y el comedor deje de ser abierto y
> tenga una puerta."

```sql
UPDATE muros SET tipo = 'interior'
WHERE zona_a = 'estudio' AND zona_b = 'comedor';

INSERT INTO puertas (eje, x, y, ancho, bisagra, hacia, zona_a, zona_b)
VALUES ('x', 6.5, 4.0, 0.9, 'izquierda', 'frente', 'estudio', 'comedor');
```

Guarda eso en, por ejemplo, `cambio.sql` y corre:

```bash
python run_sql.py cambio.sql
python generate_svg.py
```

Listo -- sin tocar una sola coordenada de píxel.
