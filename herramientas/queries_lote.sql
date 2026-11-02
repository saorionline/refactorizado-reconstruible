-- ============================================================================
-- Recetario de consultas para lote.db (implantación de la casa en el Lote 22).
-- Cómo aplicar una: copia el bloque que necesites a un archivo .sql (ej.
-- cambio_lote.sql), ajusta los números y corre:
--   py run_sql.py --db lote.db cambio_lote.sql
--   py generate_lote_svg.py
--
-- Recuerda: X crece hacia la derecha (vía -> Lote 23), Y crece hacia abajo
-- (Lote 20 -> Lote 24). x, y de un bloque = esquina superior izquierda de su
-- huella en el plano. Ids de bloque: 'central', 'ala_der', 'ala_izq'.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 1) Ver dónde está cada bloque
-- ----------------------------------------------------------------------------
SELECT id, nombre, x, y, giro, ancho, fondo FROM bloques;


-- ----------------------------------------------------------------------------
-- 2) Mover un bloque (ej. el Ala izq. 1 m a la derecha y 0.5 m hacia arriba)
-- ----------------------------------------------------------------------------
UPDATE bloques SET x = x + 1.0, y = y - 0.5 WHERE id = 'ala_izq';


-- ----------------------------------------------------------------------------
-- 3) Mover TODA la casa junta (ej. 2 m hacia la vía)
-- ----------------------------------------------------------------------------
UPDATE bloques SET x = x - 2.0;


-- ----------------------------------------------------------------------------
-- 4) Girar un bloque (sentido reloj). 0 = frente hacia abajo (Lote 24),
--    90 = frente hacia la vía, 180 = frente hacia arriba (Lote 20),
--    270 = frente hacia el Lote 23.
--    OJO: al pasar de 0/180 a 90/270 la huella cambia de ancho x fondo a
--    fondo x ancho; revisa x, y después de girar.
-- ----------------------------------------------------------------------------
UPDATE bloques SET giro = 0 WHERE id = 'central';


-- ----------------------------------------------------------------------------
-- 5) Separar las alas (ej. dejar 2 m entre Ala der. y Ala izq.).
--    Con giro 90 el Ala der. mide 5 m de ancho en el plano.
-- ----------------------------------------------------------------------------
UPDATE bloques SET x = (SELECT x FROM bloques WHERE id = 'ala_der') + 5.0 + 2.0
WHERE id = 'ala_izq';


-- ----------------------------------------------------------------------------
-- 6) Cambiar el tamaño de un bloque (ej. Central de 10 x 8 a 11 x 8)
-- ----------------------------------------------------------------------------
UPDATE bloques SET ancho = 11.0 WHERE id = 'central';


-- ----------------------------------------------------------------------------
-- 7) Dibujar un retiro desde los linderos (ej. 3 m). 0 = no se dibuja.
-- ----------------------------------------------------------------------------
UPDATE configuracion SET valor = 3.0 WHERE clave = 'retiro';


-- ----------------------------------------------------------------------------
-- 8) GUARDAR la distribución actual con un nombre (para volver luego)
-- ----------------------------------------------------------------------------
INSERT OR REPLACE INTO composiciones (nombre, bloque_id, x, y, giro)
SELECT 'mi_opcion_1', id, x, y, giro FROM bloques;


-- ----------------------------------------------------------------------------
-- 9) VOLVER a una distribución guardada
-- ----------------------------------------------------------------------------
UPDATE bloques SET x = c.x, y = c.y, giro = c.giro
FROM composiciones c
WHERE c.bloque_id = bloques.id AND c.nombre = 'central_a_la_via';


-- ----------------------------------------------------------------------------
-- 10) Ver las distribuciones guardadas
-- ----------------------------------------------------------------------------
SELECT nombre, GROUP_CONCAT(bloque_id || ' (' || x || ', ' || y || ', ' || giro || '°)', ' | ')
FROM composiciones GROUP BY nombre;


-- ----------------------------------------------------------------------------
-- 11) Poner el valor real de una curva de nivel cuando lo tengas
-- ----------------------------------------------------------------------------
UPDATE curvas_nivel SET cota = 1250.0 WHERE curva = 3;
