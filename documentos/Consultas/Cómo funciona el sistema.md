# Cómo funciona el sistema

Los planos **no se editan a mano**. Los datos viven en una base de datos (o
dentro de un script) y un programa en Python dibuja el SVG a partir de ellos.

> En este computador el comando es **`py`**, no `python`.

## Qué plano sale de dónde

Todos los scripts están en `herramientas/` y los planos en `planos/`.

| Plano | Datos | Se dibuja con |
| --- | --- | --- |
| `plano_cenital_propuesta_01.svg` · casa original | `plano.db` | `py generate_svg.py` |
| `lote22_implantacion.svg` · bloques sobre el lote | `lote.db` | `py generate_lote_svg.py` |
| `lote22_implantacion_interiores.svg` · lote con las zonas de la casa | `lote.db` + `plano.db` | `py generate_implantacion_svg.py` |
| `propuestas_bloque_central.svg` · boceto del Central nuevo con las alas | listas dentro del script | `py generate_bloque_central_svg.py` |

## Ciclo para cambiar algo

1. Escribir el cambio en un archivo `.sql` (recetas en `queries_lote.sql` y
   `queries_ejemplo.sql`).
2. Aplicarlo:
   - casa: `py run_sql.py cambio.sql`
   - lote: `py run_sql.py --db lote.db cambio.sql`
3. Regenerar el plano con su script (tabla de arriba).
4. Commit y subir a GitHub.

El boceto del bloque central no usa base de datos: sus zonas, muros,
ventanas, entradas y alas se editan en las listas al inicio de
`generate_bloque_central_svg.py`.

## Otros archivos

- `plano_nuevo/implantacion_lote22.html` · página interactiva para mover y
  girar los bloques sobre el lote.
- `planos/cuestionario_espacios_internos.md` · donde se decide qué se queda,
  qué cambia y qué se va en cada zona.

## Ramas

| Rama | Qué tiene |
| --- | --- |
| `main` | versión de trabajo: implantación, interiores y boceto del Central con las alas |
| `implantacion-lote22` | bloques ya redimensionados sobre el lote (Central 7.80 × 9.75, alas 3 × 4) |
| `casa-modelo-original` | copia de `main` (se pone al día a mano después de subir cambios a `main`) |
| `implantacion-interiores` | respaldo (igual a una versión anterior de `main`) |

Para ver en qué rama estás: `git branch --show-current`.
Para volver a la principal: `git switch main`.

## Cuidado

- **No correr `init_db.py` para el lote**: `lote.sql` está desactualizado y se
  perderían las distribuciones guardadas en `lote.db`.
- Para volver a una distribución guardada del lote, usar la receta 9 de
  `queries_lote.sql`.
