Depende de qué versión de SQLite instalaste. Las tres más comunes se usan así. En todas abres el mismo archivo:

`E:\saoto\Documents\MuestrasGratis\refactorizado-reconstruible\herramientas\plano.db`

### Opción 1: DB Browser for SQLite (programa con ventanas)

1. Abre DB Browser y pulsa **Abrir base de datos** (Ctrl+O). Busca `plano.db` en la carpeta `herramientas`.
2. Ve a la pestaña **Ejecutar SQL** (_Execute SQL_).
3. Pega la consulta, por ejemplo:
    
    ```sql
    SELECT id, x1, y1, x2, y2, tipo, zona_a, zona_b, notasFROM murosWHERE (zona_a = 'estudio' AND zona_b = 'cocina')   OR (zona_a = 'cocina'  AND zona_b = 'estudio');
    ```
    
4. Pulsa el botón ▶ o **Ctrl+Enter**. Los resultados aparecen en una tabla debajo.
5. Si ejecutas un `DELETE` o un `UPDATE`, pulsa **Escribir cambios** (_Write Changes_, Ctrl+S). Si no lo haces, el cambio no se guarda en `plano.db` y `generate_svg.py` no lo verá.

En la pestaña **Hoja de datos** (_Browse Data_) puedes ver y editar las tablas `muros`, `puertas` y `zonas` como en Excel.

### Opción 2: la línea de comandos `sqlite3`

En PowerShell, ve a la carpeta de herramientas:

```bash
cd E:\saoto\Documents\MuestrasGratis\refactorizado-reconstruible\herramientas
```

Abre la base:

```bash
sqlite3 plano.db
```

Verás el indicador `sqlite>`. Escribe primero estas dos líneas para que los resultados salgan en columnas con encabezados:

```
.headers on
.mode column
```

Después pega cualquier consulta. Tiene que terminar en `;`. Para salir, escribe `.quit`.

Desde ese mismo indicador también puedes aplicar tu archivo, y hace lo mismo que `run_sql.py`:

```
.read cambio.sql
```

Si PowerShell responde _"sqlite3 no se reconoce como comando"_, la carpeta donde instalaste SQLite no está en el PATH. Dime dónde está `sqlite3.exe` y te ayudo.

### Opción 3: una extensión de VS Code

- **SQLite Viewer** solo sirve para ver las tablas. Haz clic en `plano.db` en el explorador de VS Code y se abre como una hoja de cálculo.
- **SQLite** (de alexcvzz) sí ejecuta consultas. Escribe la consulta en un archivo `.sql`, haz clic derecho y elige **Run Query**. La primera vez te pide qué base usar: elige `plano.db`.

### Orden recomendado

1. Ejecuta los dos `SELECT` (muros y puertas) para ver qué filas hay.
2. Escribe los `DELETE` y el `UPDATE` en `cambio.sql` y aplícalo, con `python run_sql.py cambio.sql` o con `.read cambio.sql`.
3. Vuelve a ejecutar los `SELECT`. Ahora no deberían devolver nada.
4. Regenera el plano:
    
    ```bash
    python generate_svg.py
    ```
    

Si ejecutas un cambio por error, no pasa nada: estás en tu rama y puedes recuperar el `plano.db` de antes con git.

¿Cuál de las tres instalaste? Así te guío solo con esa.