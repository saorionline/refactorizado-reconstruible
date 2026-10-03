`refactorizado-reconstruible` guarda el plano de la casa de 120 m² en una base de datos SQLite (`plano.db`). Un script de Python la convierte en el dibujo SVG, así que el SVG no se edita a mano. Los scripts solo usan la librería estándar, así que no hay que instalar nada en el `.venv`. Solo leí la base de datos y la carpeta git no tiene cambios pendientes.

**Qué hay:**

- `herramientas/` es donde vas a trabajar:
    - `schema.sql` define las tablas y los datos originales del plano.
    - `plano.db` es la base de datos. Ahora tiene 18 zonas, 33 muros, 7 puertas y 31 muebles.
    - `run_sql.py` aplica un archivo `.sql` a `plano.db`.
    - `generate_svg.py` vuelve a dibujar el plano.
    - `queries_ejemplo.sql` es un recetario de consultas para copiar.
    - `init_db.py` reconstruye la base desde cero.
    - `check_md_sync.py` comprueba que el documento Markdown coincida con la base.
- `planos/` contiene el SVG que se genera.
- `documentos/` contiene el cuadro de áreas en Markdown.

### Dónde empezar con `cambio.sql`

1. **Créalo aquí:** [herramientas/cambio.sql](https://claude.ai/epitaxy/refactorizado-reconstruible/herramientas/cambio.sql). Es la carpeta que el [README](https://claude.ai/epitaxy/refactorizado-reconstruible/herramientas/README.md) usa para este mismo ejemplo.
    
2. **Escribe tu cambio.** Copia el patrón que necesites de [queries_ejemplo.sql](https://claude.ai/epitaxy/refactorizado-reconstruible/herramientas/queries_ejemplo.sql). Este ejemplo del README pone un muro con puerta entre el estudio y el comedor:
    
    ```sql
    UPDATE muros SET tipo = 'interior'
    WHERE zona_a = 'estudio' AND zona_b = 'comedor';
    ```
    
    Los nombres de zona que puedes usar son: `cocina`, `comedor`, `sala`, `terraza`, `lavanderia`, `ciclas`, `rincon`, `alcoba_principal`, `banio_principal`, `closet_principal`, `vestier_principal`, `alcoba_auxiliar`, `banio_mixto`, `closet_auxiliar`, `vestier_auxiliar`, `estudio`, `banio_invitados` y `bodega`.
    
    Todas las medidas van en **metros**, no en píxeles.
    
3. **Aplica el cambio y regenera el plano.** Desde la carpeta `herramientas`, con el `.venv` activado, ejecuta primero:
    
    ```bash
    python run_sql.py cambio.sql
    ```
    
    y después:
    
    ```bash
    python generate_svg.py
    ```
    
    El resultado queda en `planos/plano_cenital_propuesta_01.svg`.
    

**Tres cosas a tener en cuenta:**

- No ejecutes `queries_ejemplo.sql` entero con `run_sql.py`. Contiene `UPDATE` de ejemplo que cambiarían el plano. Copia solo la consulta que necesites.
- `init_db.py` borra la base y la vuelve a crear desde `schema.sql`. Cualquier cambio que hayas aplicado con `cambio.sql` se pierde.
- Como la carpeta usa git, si un cambio sale mal puedes volver a la versión anterior de `plano.db` y del SVG.

Si me dices qué quieres cambiar en el plano, puedo escribir el `cambio.sql` contigo.


-----

Aquí tienes ejemplos para tu `cambio.sql`. Como me pediste parar, no ejecuté nada más: los escribí a partir del esquema y del README, y todavía no los he probado contra tu `plano.db`.

### 1. Primero, mira qué vas a borrar

Antes de borrar, comprueba qué filas toca cada consulta. Las zonas pueden estar guardadas en cualquier orden (`estudio`/`cocina` o `cocina`/`estudio`), por eso las consultas buscan las dos combinaciones. Puedes ejecutar estas consultas en un cliente SQLite, como _SQLite Viewer_ de VS Code. `run_sql.py` no muestra los resultados de un `SELECT`.

```sql
-- Muros entre estudio y cocina
SELECT id, x1, y1, x2, y2, tipo, zona_a, zona_b, notas
FROM muros
WHERE (zona_a = 'estudio' AND zona_b = 'cocina')
   OR (zona_a = 'cocina'  AND zona_b = 'estudio');

-- Puertas entre estudio y cocina
SELECT *
FROM puertas
WHERE (zona_a = 'estudio' AND zona_b = 'cocina')
   OR (zona_a = 'cocina'  AND zona_b = 'estudio');
```

### 2. Quitar la puerta

```sql
DELETE FROM puertas
WHERE (zona_a = 'estudio' AND zona_b = 'cocina')
   OR (zona_a = 'cocina'  AND zona_b = 'estudio');
```

### 3. Quitar el muro (elige una opción)

**Opción A: borrarlo del todo.** No queda ninguna línea entre las dos zonas.

```sql
DELETE FROM muros
WHERE (zona_a = 'estudio' AND zona_b = 'cocina')
   OR (zona_a = 'cocina'  AND zona_b = 'estudio');
```

**Opción B: dejarlo como planta abierta.** Queda una línea delgada punteada que marca el límite pero no es un muro real. Es la convención que usa el plano para los espacios abiertos.

```sql
UPDATE muros SET tipo = 'punteada'
WHERE (zona_a = 'estudio' AND zona_b = 'cocina')
   OR (zona_a = 'cocina'  AND zona_b = 'estudio');
```

Si el `SELECT` del paso 1 devuelve varios muros y solo quieres quitar uno, usa su `id`. Por ejemplo, si es el 12:

```sql
DELETE FROM muros WHERE id = 12;
```

### 4. Ocultar el texto "Estudio (2 personas)"

La tabla `zonas` tiene una columna `label_mode` que acepta `'texto'`, `'circulo'` o `'ninguno'`. Para que no se vea el nombre:

```sql
UPDATE zonas SET label_mode = 'ninguno' WHERE id = 'estudio';
```

Otra opción es mostrar solo el número del cuadro de áreas en un círculo:

```sql
UPDATE zonas SET label_mode = 'circulo' WHERE id = 'estudio';
```

### `cambio.sql` completo (con la opción A)

```sql
DELETE FROM puertas
WHERE (zona_a = 'estudio' AND zona_b = 'cocina')
   OR (zona_a = 'cocina'  AND zona_b = 'estudio');

DELETE FROM muros
WHERE (zona_a = 'estudio' AND zona_b = 'cocina')
   OR (zona_a = 'cocina'  AND zona_b = 'estudio');

UPDATE zonas SET label_mode = 'ninguno' WHERE id = 'estudio';
```

Luego, desde la carpeta `herramientas`, aplica el cambio:

```bash
python run_sql.py cambio.sql
```

y regenera el plano:

```bash
python generate_svg.py
```

**Antes de aplicarlo, ten en cuenta:**

- No he comprobado que `generate_svg.py` respete `label_mode = 'ninguno'`. Si el nombre sigue apareciendo en el SVG, dímelo y lo reviso.
- Si el muro no tiene `zona_a`/`zona_b` rellenos, los `WHERE` no lo encontrarán. En ese caso, búscalo por sus coordenadas y bórralo por su `id`.
- Si borras un muro y una puerta sigue apuntando a él, `queries_ejemplo.sql` tiene unas consultas de consistencia que avisan de esos casos.
- No hace falta que ejecutes `check_md_sync.py`: estos cambios no modifican áreas.

¿Quieres que ejecute los `SELECT` del paso 1 para ver exactamente qué muros y puertas hay entre el estudio y la cocina?