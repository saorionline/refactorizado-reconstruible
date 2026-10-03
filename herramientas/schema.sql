-- ============================================================================
-- Modelo de datos del plano "arquitectura_tiny_house_120m2".
-- Todas las coordenadas están en METROS, no en píxeles.
-- Origen (0,0) = esquina superior izquierda del ala izquierda = muro de fondo.
--   eje X crece hacia la derecha (ala izquierda -> bloque central -> ala derecha)
--   eje Y crece hacia el frente  (fondo de la casa -> terraza/sala/entrada)
-- El script generate_svg.py convierte metros -> píxeles al dibujar (escala
-- configurable), así que para mover/redimensionar algo aquí SIEMPRE se piensa
-- en metros reales, nunca en píxeles.
-- ============================================================================

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS modulos;
DROP TABLE IF EXISTS puertas;
DROP TABLE IF EXISTS muros;
DROP TABLE IF EXISTS elementos_especiales;
DROP TABLE IF EXISTS zonas;

-- ----------------------------------------------------------------------------
-- ZONAS: cada espacio/cuarto del plano (cuente o no como área útil).
-- ----------------------------------------------------------------------------
CREATE TABLE zonas (
    id              TEXT PRIMARY KEY,       -- slug, ej. 'cocina', 'banio_invitados'
    numero          INTEGER,                -- número del cuadro de áreas (1..18)
    nombre          TEXT NOT NULL,
    grupo           TEXT NOT NULL,          -- 'bloque_central' | 'ala_izquierda' | 'ala_derecha'
    x               REAL NOT NULL,          -- metros, borde izquierdo
    y               REAL NOT NULL,          -- metros, borde de fondo (arriba)
    ancho           REAL NOT NULL,          -- metros, eje X ("Largo" en el cuadro de áreas)
    profundidad     REAL NOT NULL,          -- metros, eje Y ("Ancho" en el cuadro de áreas)
    cuenta_area     INTEGER NOT NULL DEFAULT 1 CHECK (cuenta_area IN (0,1)),
    fill_color      TEXT NOT NULL,
    label_mode      TEXT NOT NULL DEFAULT 'texto' CHECK (label_mode IN ('texto','circulo','ninguno')),
    numero_color    TEXT NOT NULL DEFAULT '#1f2933',  -- color del círculo numerado (si label_mode='circulo')
    descripcion     TEXT,
    notas           TEXT
);

-- ----------------------------------------------------------------------------
-- MUROS: cada segmento de muro del plano. 'tipo' decide el grosor/estilo:
--   exterior  -> línea gruesa sólida (perímetro de la casa)
--   interior  -> línea media sólida (separación real entre dos zonas)
--   punteada  -> línea delgada punteada (zona techada / planta abierta, SIN muro real)
-- ----------------------------------------------------------------------------
CREATE TABLE muros (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    x1 REAL NOT NULL, y1 REAL NOT NULL,
    x2 REAL NOT NULL, y2 REAL NOT NULL,
    tipo        TEXT NOT NULL CHECK (tipo IN ('exterior','interior','punteada')),
    zona_a      TEXT REFERENCES zonas(id),
    zona_b      TEXT REFERENCES zonas(id),
    notas       TEXT
);

-- ----------------------------------------------------------------------------
-- PUERTAS: un hueco + arco de giro dibujado sobre un muro horizontal o vertical.
--   eje='x'  -> el hueco está sobre un muro HORIZONTAL (x1 varía); bisagra/hacia
--               usan 'izquierda'|'derecha' (bisagra) y 'fondo'|'frente' (hacia).
--   eje='y'  -> el hueco está sobre un muro VERTICAL (y1 varía); bisagra usa
--               'fondo'|'frente' y hacia usa 'izquierda'|'derecha'.
-- ----------------------------------------------------------------------------
CREATE TABLE puertas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    eje         TEXT NOT NULL CHECK (eje IN ('x','y')),
    x REAL NOT NULL, y REAL NOT NULL,     -- centro del hueco, metros
    ancho       REAL NOT NULL DEFAULT 0.9,
    bisagra     TEXT NOT NULL,
    hacia       TEXT NOT NULL,
    zona_a      TEXT REFERENCES zonas(id),
    zona_b      TEXT REFERENCES zonas(id),
    notas       TEXT
);

-- ----------------------------------------------------------------------------
-- MODULOS: mobiliario / artefactos esquemáticos dentro de una zona.
--   forma: 'rect' | 'circulo' | 'elipse' | 'ducha' (rect + aspas) | 'cama' (rect + cabecera)
-- ----------------------------------------------------------------------------
CREATE TABLE modulos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    zona_id         TEXT NOT NULL REFERENCES zonas(id),
    tipo            TEXT NOT NULL,          -- nombre libre: 'mesón','ducha','sanitario','cama',...
    forma           TEXT NOT NULL DEFAULT 'rect' CHECK (forma IN ('rect','circulo','elipse','ducha','cama')),
    x REAL NOT NULL, y REAL NOT NULL,       -- metros, esquina sup-izq (rect/ducha/cama) o centro (circulo/elipse)
    ancho REAL, profundidad REAL, radio REAL,
    notas           TEXT
);

-- ----------------------------------------------------------------------------
-- ELEMENTOS ESPECIALES: anotaciones sin área (alero, escalinata, etc.)
-- ----------------------------------------------------------------------------
CREATE TABLE elementos_especiales (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo        TEXT NOT NULL,              -- 'alero' | 'escalinata'
    x REAL NOT NULL, y REAL NOT NULL,
    ancho REAL NOT NULL, profundidad REAL NOT NULL,
    etiqueta    TEXT,
    notas       TEXT
);

-- ============================================================================
-- DATOS: estado actual del plano de 120 m² (110 m² útiles + 10 m² zona techada)
-- ============================================================================

INSERT INTO zonas (id, numero, nombre, grupo, x, y, ancho, profundidad, cuenta_area, fill_color, label_mode, numero_color, descripcion) VALUES
('cocina',            1, 'Cocina',               'bloque_central', 4.0, 0.0, 6.0, 2.0, 1, '#f3ece0', 'texto',   '#1f2933', 'Mesón lineal contra el muro de fondo. Puerta hacia el estudio.'),
('lavanderia',        5, 'Lavandería',           'bloque_central', 10.0,0.0, 2.0, 2.0, 1, '#e9e5f0', 'circulo', '#1f2933', 'Puerta plegable hacia ciclas.'),
('ciclas',            6, 'Ciclas',               'bloque_central', 12.0,0.0, 2.0, 1.0, 1, '#e9e5f0', 'circulo', '#1f2933', 'Sin puerta, abierto a rincón.'),
('rincon',            7, 'Rincón',               'bloque_central', 12.0,1.0, 2.0, 1.0, 1, '#e9e5f0', 'circulo', '#1f2933', 'Sin puerta, abierto a ciclas.'),
('estudio',          16, 'Estudio (2 personas)', 'bloque_central', 4.0, 2.0, 5.0, 2.0, 1, '#d7e8e0', 'texto',   '#1f2933', 'Puesto de trabajo doble. Puerta hacia cocina; abierto hacia comedor.'),
('banio_invitados',  17, 'Baño de invitados',    'bloque_central', 9.0, 2.0, 3.0, 2.0, 0, '#e4e4e0', 'circulo', '#6b7682', 'Zona techada: sin muro formal, no cuenta como área útil.'),
('bodega',           18, 'Mini bodega',          'bloque_central', 12.0,2.0, 2.0, 2.0, 0, '#e4e4e0', 'circulo', '#6b7682', 'Zona techada: sin muro formal, no cuenta como área útil.'),
('comedor',           2, 'Comedor',              'bloque_central', 4.0, 4.0, 6.0, 2.5, 1, '#f3ece0', 'texto',   '#1f2933', 'Abierto al estudio (fondo) y a la sala.'),
('sala',              3, 'Sala',                 'bloque_central', 10.0,4.0, 4.0, 4.0, 1, '#f3ece0', 'texto',   '#1f2933', 'Espacio diáfano. Alero de 0.80 m hacia el frente (sin área).'),
('terraza',           4, 'Terraza',              'bloque_central', 4.0, 6.5, 6.0, 1.5, 1, '#e2ecd9', 'texto',   '#1f2933', 'Frente; vidrios corredizos al comedor.'),
('alcoba_principal',  8, 'Alcoba principal',     'ala_izquierda',  0.0, 6.0, 4.0, 3.0, 1, '#e6edf4', 'texto',   '#1f2933', 'Puerta de acceso por la terraza.'),
('banio_principal',   9, 'Baño principal',       'ala_izquierda',  0.0, 4.0, 2.4, 2.0, 1, '#cfe3ea', 'circulo', '#1f2933', 'Sanitario, lavamanos y ducha.'),
('closet_principal', 10, 'Clóset principal',     'ala_izquierda',  2.4, 4.0, 1.0, 2.0, 1, '#e6edf4', 'circulo', '#1f2933', 'Abierto a la alcoba.'),
('vestier_principal',11, 'Vestier principal',    'ala_izquierda',  3.4, 4.0, 0.6, 2.0, 1, '#e6edf4', 'circulo', '#1f2933', 'Abierto a la alcoba.'),
('alcoba_auxiliar',  12, 'Alcoba auxiliar',      'ala_derecha',   14.0, 5.5, 4.0, 2.5, 1, '#e6edf4', 'texto',   '#1f2933', 'Puerta a la sala.'),
('banio_mixto',      13, 'Baño mixto',           'ala_derecha',   14.0, 3.0, 2.4, 2.5, 1, '#cfe3ea', 'circulo', '#1f2933', 'Doble acceso: sala y alcoba auxiliar.'),
('vestier_auxiliar', 15, 'Vestier auxiliar',     'ala_derecha',   16.4, 3.0, 1.0, 2.5, 1, '#e6edf4', 'circulo', '#1f2933', 'Abierto a la alcoba.'),
('closet_auxiliar',  14, 'Clóset auxiliar',      'ala_derecha',   17.4, 3.0, 0.6, 2.5, 1, '#e6edf4', 'circulo', '#1f2933', 'Abierto a la alcoba.');

INSERT INTO muros (x1,y1,x2,y2,tipo,zona_a,zona_b,notas) VALUES
-- Exteriores: ala izquierda
(0,4, 4,4,  'exterior','alcoba_principal',NULL,'ala izq. - muro de fondo'),
(0,4, 0,9,  'exterior','alcoba_principal',NULL,'ala izq. - muro izquierdo'),
(0,9, 4,9,  'exterior','alcoba_principal',NULL,'ala izq. - muro frente'),
(4,9, 4,8,  'exterior','alcoba_principal','terraza','conector ala izq./terraza'),
-- Exteriores: bloque central
(4,0, 14,0, 'exterior','cocina',NULL,'muro de fondo (cocina + servicios)'),
(4,0, 4,8,  'exterior',NULL,NULL,'muro izquierdo del bloque central'),
(14,0,14,2, 'exterior','lavanderia',NULL,'muro derecho (servicios), antes de la zona techada'),
(4,8, 10,8, 'exterior','terraza',NULL,'frente de la terraza'),
(14,8,14,8.8,'exterior',NULL,NULL,'jog: frente ala derecha -> frente sala (alero)'),
(10,8.8,14,8.8,'exterior','sala',NULL,'frente de la sala (con alero de 0.80 m)'),
(10,6.5,10,8,'exterior','terraza','sala','muro terraza/sala'),
-- Exteriores: ala derecha
(14,3, 18,3, 'exterior','banio_mixto',NULL,'ala der. - muro de fondo'),
(18,3, 18,8, 'exterior','alcoba_auxiliar',NULL,'ala der. - muro derecho'),
(18,8, 14,8, 'exterior','alcoba_auxiliar',NULL,'ala der. - muro frente'),
-- Interiores
(0,6, 4,6,   'interior','banio_principal','alcoba_principal','ala izq. separación baños/alcoba'),
(2.4,4,2.4,6,'interior','banio_principal','closet_principal','ala izq. baño/clóset'),
(3.4,4,3.4,6,'interior','closet_principal','vestier_principal','ala izq. clóset/vestier'),
(14,5.5,18,5.5,'interior','banio_mixto','alcoba_auxiliar','ala der. separación baño/alcoba'),
(16.4,3,16.4,5.5,'interior','banio_mixto','vestier_auxiliar','ala der. baño/vestier'),
(17.4,3,17.4,5.5,'interior','vestier_auxiliar','closet_auxiliar','ala der. vestier/clóset'),
(4,6.5,10,6.5,'interior','comedor','terraza','separación comedor/terraza'),
(10,0,10,2,  'interior','cocina','lavanderia','separación cocina/servicios'),
(4,2, 9,2,   'interior','cocina','estudio','muro con puerta cocina<->estudio (ver puertas)'),
(12,0,12,2,  'interior','lavanderia','ciclas','muro con puerta plegable (ver puertas)'),
(14,3,14,8,  'interior','sala','banio_mixto','muro ala derecha/central (puertas D3,D5 incluidas)'),
-- Punteadas: planta abierta o zona techada sin muro formal
(9,2, 14,2,  'punteada','estudio','banio_invitados','borde superior zona techada (17+18)'),
(9,4, 14,4,  'punteada','comedor','banio_invitados','borde inferior zona techada (17+18)'),
(9,2, 9,4,   'punteada','estudio','banio_invitados','borde izquierdo zona techada'),
(12,2,12,4,  'punteada','banio_invitados','bodega','divisor interno zona techada (17/18)'),
(14,2,14,3,  'punteada','bodega',NULL,'borde derecho zona techada (sin oposición aún)'),
(4,4, 9,4,   'punteada','estudio','comedor','planta abierta estudio/comedor'),
(10,4,10,6.5,'punteada','comedor','sala','planta abierta comedor/sala'),
(12,1,14,1,  'punteada','ciclas','rincon','planta abierta ciclas/rincón');

INSERT INTO puertas (eje,x,y,ancho,bisagra,hacia,zona_a,zona_b,notas) VALUES
('x', 0.95, 6.00, 0.90, 'izquierda', 'fondo',    'banio_principal','alcoba_principal', NULL),
('y', 4.00, 7.45, 0.90, 'frente',    'izquierda','terraza','alcoba_principal', NULL),
('y', 14.00,4.75, 0.90, 'frente',    'derecha',  'banio_mixto','sala', NULL),
('x', 14.85,5.50, 0.90, 'izquierda', 'fondo',    'banio_mixto','alcoba_auxiliar', NULL),
('y', 14.00,7.05, 0.90, 'frente',    'derecha',  'sala','alcoba_auxiliar', NULL),
('x', 6.58, 2.00, 0.90, 'izquierda', 'fondo',    'cocina','estudio', NULL),
('y', 12.00,1.00, 0.90, 'fondo',     'derecha',  'lavanderia','ciclas', 'puerta plegable');

INSERT INTO modulos (zona_id,tipo,forma,x,y,ancho,profundidad,radio,notas) VALUES
('cocina','mesón','rect', 4.15,0.15,5.70,0.60, NULL, NULL),
('cocina','hornilla','circulo', 8.60,0.45, NULL,NULL,0.104, NULL),
('cocina','hornilla','circulo', 9.10,0.45, NULL,NULL,0.104, NULL),
('cocina','mesón bajo','rect', 6.00,0.22,0.70,0.46, NULL, NULL),
('lavanderia','lavadora','rect', 10.15,0.15,0.70,0.70, NULL, NULL),
('lavanderia','secadora','rect', 10.95,0.15,0.70,0.70, NULL, NULL),
('ciclas','rueda','circulo', 12.50,0.50, NULL,NULL,0.18, NULL),
('ciclas','rueda','circulo', 13.00,0.50, NULL,NULL,0.18, NULL),
('ciclas','rueda','circulo', 13.50,0.50, NULL,NULL,0.18, NULL),
('estudio','escritorio','rect', 5.05,2.375,3.33,0.54, NULL, NULL),
('estudio','silla','rect', 5.51,3.04,0.40,0.28, NULL, NULL),
('estudio','silla','rect', 7.18,3.04,0.40,0.28, NULL, NULL),
('banio_invitados','sanitario','rect', 9.21,2.83,0.40,0.55, NULL, NULL),
('banio_invitados','ducha','ducha', 10.63,2.73,0.83,0.83, NULL, NULL),
('comedor','mesa','elipse', 6.00,5.25, 2.00,1.00, NULL, 'ancho/profundidad = diámetros de la elipse'),
('comedor','silla','rect', 5.15,4.50,0.40,0.28, NULL, NULL),
('comedor','silla','rect', 5.15,5.72,0.40,0.28, NULL, NULL),
('comedor','silla','rect', 5.80,4.50,0.40,0.28, NULL, NULL),
('comedor','silla','rect', 5.80,5.72,0.40,0.28, NULL, NULL),
('comedor','silla','rect', 6.45,4.50,0.40,0.28, NULL, NULL),
('comedor','silla','rect', 6.45,5.72,0.40,0.28, NULL, NULL),
('sala','sofá','rect', 11.00,7.00,2.50,0.80, NULL, NULL),
('sala','mesa centro','rect', 11.60,5.90,1.30,0.60, NULL, NULL),
('alcoba_principal','cama','cama', 0.70,6.30,1.60,1.90, NULL, NULL),
('banio_principal','sanitario','rect', 0.10,4.10,0.40,0.55, NULL, NULL),
('banio_principal','lavamanos','rect', 1.65,5.35,0.65,0.55, NULL, NULL),
('banio_principal','ducha','ducha', 1.55,4.05,0.80,0.80, NULL, NULL),
('alcoba_auxiliar','cama','cama', 16.40,5.90,1.50,2.00, NULL, NULL),
('banio_mixto','sanitario','rect', 14.10,3.10,0.40,0.55, NULL, NULL),
('banio_mixto','lavamanos','rect', 15.65,4.85,0.65,0.55, NULL, NULL),
('banio_mixto','ducha','ducha', 15.55,3.05,0.80,0.80, NULL, NULL);

INSERT INTO elementos_especiales (tipo,x,y,ancho,profundidad,etiqueta,notas) VALUES
('alero', 10.0, 8.0, 4.0, 0.8, 'ALERO 0.80 m (sin área)', 'Voladizo de cubierta frente a la sala; no cuenta área.'),
('escalinata', 10.0, 8.8, 4.0, 0.6, 'ESCALINATA 4.00 × 0.60', 'Centrada en el ancho de la sala, fuera de la huella.');
