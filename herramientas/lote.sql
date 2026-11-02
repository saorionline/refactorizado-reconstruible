-- ============================================================================
-- Modelo de datos de la implantación de la casa en el LOTE 22.
-- Todas las coordenadas están en METROS, no en píxeles.
-- Origen (0,0) = esquina Lote 20 / Vía vehicular principal (arriba a la izq.).
--   eje X crece hacia la derecha (vía -> Lote 23)
--   eje Y crece hacia abajo     (Lote 20 -> Lote 24)
-- Es el lote del plano topográfico girado 180°: arriba queda la parte alta
-- de la montaña (esquina Lote 20 / Lote 23).
-- generate_lote_svg.py convierte metros -> píxeles al dibujar.
-- ============================================================================

DROP TABLE IF EXISTS composiciones;
DROP TABLE IF EXISTS bloques;
DROP TABLE IF EXISTS curvas_nivel;
DROP TABLE IF EXISTS lote_vertices;
DROP TABLE IF EXISTS configuracion;

-- ----------------------------------------------------------------------------
-- CONFIGURACION: valores sueltos del dibujo y del lote.
-- ----------------------------------------------------------------------------
CREATE TABLE configuracion (
    clave   TEXT PRIMARY KEY,
    valor   REAL NOT NULL,
    notas   TEXT
);

-- ----------------------------------------------------------------------------
-- LOTE_VERTICES: esquinas del lote en orden. El lado 'lindero' va desde este
-- vértice hasta el siguiente (el último cierra contra el primero).
-- ----------------------------------------------------------------------------
CREATE TABLE lote_vertices (
    orden           INTEGER PRIMARY KEY,
    x               REAL NOT NULL,
    y               REAL NOT NULL,
    lindero         TEXT NOT NULL,          -- con qué colinda el lado que sale de este vértice
    longitud_plano  REAL                    -- medida escrita en el plano topográfico (m)
);

-- ----------------------------------------------------------------------------
-- CURVAS_NIVEL: cada curva es una polilínea (puntos en 'orden').
-- Calcadas de la imagen; 'cota' queda vacía hasta tener los valores reales.
-- ----------------------------------------------------------------------------
CREATE TABLE curvas_nivel (
    curva   INTEGER NOT NULL,
    orden   INTEGER NOT NULL,
    x       REAL NOT NULL,
    y       REAL NOT NULL,
    cota    REAL,
    PRIMARY KEY (curva, orden)
);

-- ----------------------------------------------------------------------------
-- BLOQUES: la masa de la casa.
--   ancho x fondo = medidas del bloque sin girar (el frente es el lado 'fondo'
--   de abajo, como en el plano de la casa).
--   x, y = esquina superior izquierda de la HUELLA ya girada (lo que se ve en
--   el plano). Con giro 90/270 la huella mide fondo x ancho.
--   giro = grados en sentido de las manecillas del reloj (0, 90, 180, 270 u
--   otro valor; con ángulos no rectos el bloque gira sobre su centro).
-- ----------------------------------------------------------------------------
CREATE TABLE bloques (
    id          TEXT PRIMARY KEY,
    nombre      TEXT NOT NULL,
    ancho       REAL NOT NULL,
    fondo       REAL NOT NULL,
    x           REAL NOT NULL,
    y           REAL NOT NULL,
    giro        REAL NOT NULL DEFAULT 0,
    color       TEXT NOT NULL,
    marca_frente INTEGER NOT NULL DEFAULT 0 CHECK (marca_frente IN (0,1)),
    notas       TEXT,
    grupo_plano TEXT                        -- grupo de zonas de plano.db que va dentro
                                            -- ('bloque_central' | 'ala_izquierda' | 'ala_derecha')
);

-- ----------------------------------------------------------------------------
-- COMPOSICIONES: distribuciones guardadas con nombre, para volver a ellas.
-- (ver queries_lote.sql: "guardar" y "aplicar" una composición)
-- ----------------------------------------------------------------------------
CREATE TABLE composiciones (
    nombre      TEXT NOT NULL,
    bloque_id   TEXT NOT NULL REFERENCES bloques(id),
    x           REAL NOT NULL,
    y           REAL NOT NULL,
    giro        REAL NOT NULL,
    PRIMARY KEY (nombre, bloque_id)
);

-- ============================================================================
-- DATOS
-- ============================================================================

INSERT INTO configuracion (clave, valor, notas) VALUES
('norte_azimut',      155.1, 'grados, sentido reloj, desde "arriba" de la pantalla hacia el norte real'),
('retiro',              0.0, 'metros libres desde todos los linderos (0 = no se dibuja)'),
('area_plano',        725.55,'área escrita en el plano topográfico (m²)'),
('esquina_alta_x',     39.43,'parte alta de la montaña: esquina Lote 20 / Lote 23'),
('esquina_alta_y',      0.0,  NULL);

INSERT INTO lote_vertices (orden, x, y, lindero, longitud_plano) VALUES
(1,  0.00,  0.00, 'Lote 20',                 39.43),
(2, 39.43,  0.00, 'Lote 23',                 19.00),
(3, 39.66, 19.00, 'hacia Lote 24',           36.00),
(4,  3.71, 17.21, 'Vía vehicular principal', 17.60);

INSERT INTO curvas_nivel (curva, orden, x, y) VALUES
(1,1,39.29,6.87),(1,2,35.37,5.63),(1,3,32.69,4.64),(1,4,28.66,3.17),(1,5,22.82,-0.03),
(2,1,39.29,14.68),(2,2,37.69,15.42),(2,3,35.35,14.00),(2,4,31.78,12.31),(2,5,28.90,10.30),(2,6,26.04,7.73),(2,7,22.73,4.81),(2,8,17.10,-0.11),
(3,1,35.62,18.78),(3,2,30.59,14.54),(3,3,26.20,9.88),(3,4,21.14,4.99),(3,5,15.38,0.97),(3,6,11.33,0.06),
(4,1,27.40,19.08),(4,2,23.10,15.22),(4,3,16.73,8.70),(4,4,10.58,2.64),(4,5,5.79,0.13),
(5,1,21.12,18.76),(5,2,16.11,14.57),(5,3,11.05,9.67),(5,4,6.45,4.56),(5,5,2.95,0.61),
(6,1,14.64,18.60),(6,2,11.10,15.78),(6,3,6.50,10.67),(6,4,3.73,4.71),(6,5,2.72,0.72),
(7,1,8.40,18.98),(7,2,5.27,14.02),(7,3,4.06,9.01),(7,4,2.76,3.21),(7,5,1.09,3.81);

-- Distribución acordada: Central con el frente hacia la vía; Ala der. a 2.75 m
-- del Central y Ala izq. pegada a ella; alas 5.25 m más abajo que el borde
-- superior del Central (quedan 0.75 m por encima de su borde inferior).
INSERT INTO bloques (id, nombre, ancho, fondo, x, y, giro, color, marca_frente, notas, grupo_plano) VALUES
('central', 'Central',   10.0, 8.0, 15.25, 4.00, 90, '#d9b77e', 1, 'Frente mirando a la vía (izquierda).', 'bloque_central'),
('ala_der', 'Ala der.',   4.0, 5.0, 26.00, 9.25, 90, '#8fbf9a', 0, NULL, 'ala_derecha'),
('ala_izq', 'Ala izq.',   4.0, 5.0, 31.00, 9.25, 90, '#7fa7c9', 0, NULL, 'ala_izquierda');

INSERT INTO composiciones (nombre, bloque_id, x, y, giro)
SELECT 'central_a_la_via', id, x, y, giro FROM bloques;
