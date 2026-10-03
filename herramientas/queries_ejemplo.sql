-- ============================================================================
-- Recetario de consultas para plano.db.
-- Cómo correr una de estas consultas:
--   python -c "import sqlite3; con=sqlite3.connect('plano.db'); [print(r) for r in con.execute('''<pega aquí la consulta>''')]"
-- o con cualquier cliente SQLite (DB Browser for SQLite, extensión de VS Code, etc.)
--
-- Después de CUALQUIER cambio (INSERT/UPDATE/DELETE), vuelve a correr:
--   python generate_svg.py
-- para que el plano.svg quede al día. Eso reemplaza por completo tener que
-- editar coordenadas de SVG a mano.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 1) Ver el estado completo de una zona (p. ej. la cocina)
-- ----------------------------------------------------------------------------
SELECT * FROM zonas WHERE id = 'cocina';


-- ----------------------------------------------------------------------------
-- 2) Ver TODOS los muros que tocan una zona (como zona_a o zona_b)
-- ----------------------------------------------------------------------------
SELECT id, x1, y1, x2, y2, tipo, zona_a, zona_b, notas
FROM muros
WHERE zona_a = 'cocina' OR zona_b = 'cocina';


-- ----------------------------------------------------------------------------
-- 3) "Cambia el muro entre cocina y estudio" -- patrón general:
--    primero lo ubicas por sus zonas, luego haces el UPDATE con los
--    nuevos extremos (x1,y1)-(x2,y2) o el nuevo tipo.
-- ----------------------------------------------------------------------------
-- 3a) Mover un extremo del muro (ejemplo: alargarlo 1 m hacia la derecha)
UPDATE muros
SET x2 = 10.0
WHERE zona_a = 'cocina' AND zona_b = 'estudio';

-- 3b) Convertir un muro sólido en punteado (p. ej. abrir cocina/estudio
--     en vez de tener puerta)
UPDATE muros SET tipo = 'punteada'
WHERE zona_a = 'cocina' AND zona_b = 'estudio';

-- 3c) Volverlo muro interior normal de nuevo
UPDATE muros SET tipo = 'interior'
WHERE zona_a = 'cocina' AND zona_b = 'estudio';


-- ----------------------------------------------------------------------------
-- 4) Listar todas las zonas "punteadas" / de planta abierta o zona techada
-- ----------------------------------------------------------------------------
SELECT m.id, m.x1, m.y1, m.x2, m.y2, m.zona_a, m.zona_b, m.notas
FROM muros m
WHERE m.tipo = 'punteada';

-- 4b) Listar solo las zonas que NO cuentan como área útil (zona techada)
SELECT id, numero, nombre, ancho, profundidad, ancho*profundidad AS area
FROM zonas
WHERE cuenta_area = 0;


-- ----------------------------------------------------------------------------
-- 5) Listar los módulos (mobiliario) de una zona
-- ----------------------------------------------------------------------------
SELECT tipo, forma, x, y, ancho, profundidad, radio
FROM modulos
WHERE zona_id = 'estudio';


-- ----------------------------------------------------------------------------
-- 6) Resumen de área por grupo (bloque_central / ala_izquierda / ala_derecha),
--    separando lo que cuenta como útil de lo que no.
-- ----------------------------------------------------------------------------
SELECT
    grupo,
    SUM(CASE WHEN cuenta_area = 1 THEN ancho*profundidad ELSE 0 END) AS area_util,
    SUM(CASE WHEN cuenta_area = 0 THEN ancho*profundidad ELSE 0 END) AS area_no_util
FROM zonas
GROUP BY grupo;

-- 6b) Total general de la casa
SELECT
    SUM(CASE WHEN cuenta_area = 1 THEN ancho*profundidad ELSE 0 END) AS total_util,
    SUM(ancho*profundidad) AS total_techado
FROM zonas;


-- ----------------------------------------------------------------------------
-- 7) Mover una zona completa (ej. correr la bodega 0.5 m hacia la derecha)
--    Recuerda: esto NO mueve sus muros ni sus módulos automáticamente --
--    ajústalos aparte con los UPDATE de las secciones 3 y 8.
-- ----------------------------------------------------------------------------
UPDATE zonas SET x = x + 0.5 WHERE id = 'bodega';


-- ----------------------------------------------------------------------------
-- 8) Mover una puerta (ej. la puerta cocina<->estudio 0.3 m hacia la derecha)
-- ----------------------------------------------------------------------------
UPDATE puertas SET x = x + 0.3
WHERE zona_a = 'cocina' AND zona_b = 'estudio';


-- ----------------------------------------------------------------------------
-- 9) Insertar una zona nueva + su módulo (plantilla para agregar un espacio)
-- ----------------------------------------------------------------------------
-- INSERT INTO zonas (id, numero, nombre, grupo, x, y, ancho, profundidad,
--                     cuenta_area, fill_color, label_mode, numero_color, descripcion)
-- VALUES ('nuevo_closet', 19, 'Clóset nuevo', 'bloque_central',
--         9.0, 2.0, 1.0, 2.0, 1, '#e6edf4', 'circulo', '#1f2933', 'Descripción aquí');


-- ----------------------------------------------------------------------------
-- 10) Chequeo de consistencia: ¿alguna "fila" (mismo y, mismo grupo) no suma
--     el ancho total de 10 m del bloque central? Útil para detectar que una
--     zona quedó mal dimensionada después de un cambio.
-- ----------------------------------------------------------------------------
SELECT y, grupo, SUM(ancho) AS ancho_total, GROUP_CONCAT(nombre, ', ') AS zonas
FROM zonas
WHERE grupo = 'bloque_central'
GROUP BY y, grupo
HAVING ancho_total NOT IN (10.0, 6.0, 4.0, 5.0, 3.0, 2.0);
-- (ajusta la lista de anchos "válidos" según el diseño vigente)


-- ----------------------------------------------------------------------------
-- 11) Chequeo de consistencia: ¿alguna zona se sale del ancho total de 18 m
--     o se superpone en X con otra de su misma fila?
-- ----------------------------------------------------------------------------
SELECT a.id AS zona_a, b.id AS zona_b, a.x, a.ancho, b.x, b.ancho
FROM zonas a
JOIN zonas b ON a.grupo = b.grupo AND a.y = b.y AND a.id < b.id
WHERE a.x < b.x + b.ancho AND b.x < a.x + a.ancho;  -- rangos en X que se cruzan
