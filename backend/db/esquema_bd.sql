-- =====================================================================
-- ReportaYa — Esquema de base de datos (SQLite >= 3.31)
-- Fuente: diagrama_clases_equipo.puml + openapi_equipo.yaml + SRS_equipo.md v2.0
--
-- Convenciones de mapeo
--   * Identificadores UUID           -> TEXT (UUID en minúsculas, 36 caracteres).
--   * Fecha y hora (FechaHora)       -> TEXT ISO-8601 UTC "YYYY-MM-DDTHH:MM:SSZ"
--                                       (ordenan igual como texto que como tiempo).
--   * Fecha (garantiaVencimiento)    -> TEXT "YYYY-MM-DD".
--   * Boolean                        -> INTEGER 0/1 con CHECK.
--   * Decimal (monto, valor)         -> NUMERIC (pesos MXN; el API lo expone como number).
--   * Enumeraciones                  -> TEXT con CHECK (col IN (...)); los valores son
--                                       idénticos a los enum del openapi_equipo.yaml.
--   * Atributos derivados NO se persisten:
--     /etiqueta (vista v_ubicacion), /posibleDuplicado, /detenido, /montoCosto,
--     /pagador, /reaperturas, /anulada, /url, /mensajeAcceso, /requiereSubtipo.
--   * Herencia: tabla por subclase (la tabla hija comparte la PK de la madre).
--     La coherencia del tipo se obliga con una FK compuesta (id, discriminador):
--     la hija lleva una columna constante (DEFAULT + CHECK) que debe coincidir
--     con el discriminador de la madre.
--   * Composición (*--): FK sin ON DELETE CASCADE. En ReportaYa nada se borra
--     (RNF-07), por eso las FK son RESTRICT y las tablas de historial llevan
--     disparadores de solo inserción.
--   * Fuera del dominio (no están en el diagrama de clases y no se crean aquí):
--     sesiones JWT, llaves de idempotencia y outbox/worker.
-- =====================================================================

PRAGMA foreign_keys = ON;   -- por conexión; SQLite lo apaga por omisión
PRAGMA user_version = 1;

-- =====================================================================
-- 1. PADRÓN Y USUARIOS (RF-01, RF-02, RF-14, RF-21)
-- =====================================================================

-- Usuario (clase abstracta) --------------------------------------------
CREATE TABLE usuario (
    id                TEXT PRIMARY KEY,
    nombre            TEXT NOT NULL CHECK (length(trim(nombre)) >= 1),
    correo            TEXT NOT NULL COLLATE NOCASE UNIQUE
                      CHECK (correo LIKE '_%@_%._%'),
    rol               TEXT NOT NULL
                      CHECK (rol IN ('Residente','Vigilancia','Mantenimiento','Administracion')),
    estado_cuenta     TEXT NOT NULL DEFAULT 'PendienteActivacion'
                      CHECK (estado_cuenta IN ('PendienteActivacion','Activa','Desactivada')),
    contrasena_hash   TEXT,                                   -- {interno}; nula hasta activar la cuenta
    intentos_fallidos INTEGER NOT NULL DEFAULT 0 CHECK (intentos_fallidos >= 0),  -- {interno}
    bloqueado_hasta   TEXT,                                   -- {interno}
    CHECK (estado_cuenta <> 'Activa' OR contrasena_hash IS NOT NULL),
    UNIQUE (id, rol),  -- destino de las FK compuestas de las subclases
    CHECK (length(id) = 36),
    CHECK (bloqueado_hasta IS NULL OR (bloqueado_hasta GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(bloqueado_hasta) IS NOT NULL))
);

-- Subclases de Usuario. 'rol' es la columna constante que ata la hija a su discriminador.
CREATE TABLE residente (
    usuario_id TEXT PRIMARY KEY,
    rol        TEXT NOT NULL DEFAULT 'Residente' CHECK (rol = 'Residente'),
    FOREIGN KEY (usuario_id, rol) REFERENCES usuario (id, rol)
);

CREATE TABLE vigilante (
    usuario_id TEXT PRIMARY KEY,
    rol        TEXT NOT NULL DEFAULT 'Vigilancia' CHECK (rol = 'Vigilancia'),
    FOREIGN KEY (usuario_id, rol) REFERENCES usuario (id, rol)
);

CREATE TABLE usuario_mantenimiento (
    usuario_id   TEXT PRIMARY KEY,
    rol          TEXT NOT NULL DEFAULT 'Mantenimiento' CHECK (rol = 'Mantenimiento'),
    tipo         TEXT NOT NULL CHECK (tipo IN ('PersonalPropio','ProveedorExterno')),
    especialidad TEXT,
    telefono     TEXT,
    FOREIGN KEY (usuario_id, rol) REFERENCES usuario (id, rol)
);

CREATE TABLE usuario_administracion (
    usuario_id            TEXT PRIMARY KEY,
    rol                   TEXT NOT NULL DEFAULT 'Administracion' CHECK (rol = 'Administracion'),
    perfil_administracion TEXT NOT NULL CHECK (perfil_administracion IN ('Administrador','Auxiliar')),
    FOREIGN KEY (usuario_id, rol) REFERENCES usuario (id, rol),
    UNIQUE (usuario_id, perfil_administracion)               -- destino de FK de Delegacion (RF-21)
);

-- Enlaces de activación / recuperación de contraseña (TokenPassword) ------
CREATE TABLE enlace_acceso (
    hash_token TEXT PRIMARY KEY,                              -- sólo se guarda el hash del token
    usuario_id TEXT NOT NULL REFERENCES usuario (id),
    tipo       TEXT NOT NULL CHECK (tipo IN ('Activacion','Recuperacion')),
    emitido_en TEXT NOT NULL,
    vence_en   TEXT NOT NULL,
    usado_en   TEXT,
    CHECK (vence_en > emitido_en),
    CHECK (usado_en IS NULL OR usado_en >= emitido_en),
    CHECK (emitido_en GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(emitido_en) IS NOT NULL),
    CHECK (vence_en GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(vence_en) IS NOT NULL),
    CHECK (usado_en IS NULL OR (usado_en GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(usado_en) IS NOT NULL))
);

-- Delegación del Administrador a la Auxiliar (RF-21) -----------------------
CREATE TABLE delegacion (
    id                   TEXT PRIMARY KEY,
    otorgada_por         TEXT NOT NULL,                       -- otorgadaPor: Administrador
    otorgada_por_perfil  TEXT NOT NULL DEFAULT 'Administrador' CHECK (otorgada_por_perfil = 'Administrador'),
    auxiliar_id          TEXT NOT NULL,                       -- auxiliar: Auxiliar
    auxiliar_perfil      TEXT NOT NULL DEFAULT 'Auxiliar'     CHECK (auxiliar_perfil = 'Auxiliar'),
    habilitada           INTEGER NOT NULL DEFAULT 1 CHECK (habilitada IN (0,1)),
    fecha_inicio         TEXT NOT NULL,
    fecha_fin            TEXT,
    CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio),
    FOREIGN KEY (otorgada_por, otorgada_por_perfil) REFERENCES usuario_administracion (usuario_id, perfil_administracion),
    FOREIGN KEY (auxiliar_id,  auxiliar_perfil)     REFERENCES usuario_administracion (usuario_id, perfil_administracion),
    CHECK (length(id) = 36),
    CHECK (fecha_inicio GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(fecha_inicio) IS NOT NULL),
    CHECK (fecha_fin IS NULL OR (fecha_fin GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(fecha_fin) IS NOT NULL))
);

-- Ubicacion (clase abstracta) -> Unidad | AreaComun -------------------------
CREATE TABLE ubicacion (
    id     TEXT PRIMARY KEY,
    tipo   TEXT NOT NULL CHECK (tipo IN ('Unidad','AreaComun')),
    activa INTEGER NOT NULL DEFAULT 1 CHECK (activa IN (0,1)),
    UNIQUE (id, tipo),
    CHECK (length(id) = 36)
);

CREATE TABLE unidad (
    ubicacion_id       TEXT PRIMARY KEY,
    tipo               TEXT NOT NULL DEFAULT 'Unidad' CHECK (tipo = 'Unidad'),
    torre              TEXT NOT NULL CHECK (length(trim(torre)) >= 1),
    piso               INTEGER NOT NULL,
    numero             TEXT NOT NULL CHECK (length(trim(numero)) >= 1),
    -- Propietario (objeto de valor 1..1 dentro de Unidad)
    propietario_nombre            TEXT NOT NULL,
    propietario_correo            TEXT NOT NULL COLLATE NOCASE CHECK (propietario_correo LIKE '_%@_%._%'),
    propietario_vive_en_condominio INTEGER NOT NULL CHECK (propietario_vive_en_condominio IN (0,1)),
    FOREIGN KEY (ubicacion_id, tipo) REFERENCES ubicacion (id, tipo),
    UNIQUE (torre, numero),  -- etiqueta "B-502" única
    CHECK (length(trim(propietario_nombre)) >= 1)
);

CREATE TABLE area_comun (
    ubicacion_id TEXT PRIMARY KEY,
    tipo         TEXT NOT NULL DEFAULT 'AreaComun' CHECK (tipo = 'AreaComun'),
    nombre       TEXT NOT NULL COLLATE NOCASE UNIQUE CHECK (length(trim(nombre)) >= 1),
    FOREIGN KEY (ubicacion_id, tipo) REFERENCES ubicacion (id, tipo)
);

-- Vinculación residente <-> unidad (D1) ------------------------------------
CREATE TABLE vinculacion_unidad (
    id           TEXT PRIMARY KEY,
    residente_id TEXT NOT NULL REFERENCES residente (usuario_id),
    unidad_id    TEXT NOT NULL REFERENCES unidad (ubicacion_id),
    ocupacion    TEXT NOT NULL CHECK (ocupacion IN ('Propietario','Inquilino')),
    fecha_inicio TEXT NOT NULL,
    fecha_fin    TEXT,
    CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio),
    CHECK (length(id) = 36),
    CHECK (fecha_inicio GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(fecha_inicio) IS NOT NULL),
    CHECK (fecha_fin IS NULL OR (fecha_fin GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(fecha_fin) IS NOT NULL))
);

-- Proveedor sin acceso al sistema (realiza Responsable) --------------------
CREATE TABLE proveedor_sin_acceso (
    id           TEXT PRIMARY KEY,
    nombre       TEXT NOT NULL CHECK (length(trim(nombre)) >= 1),
    especialidad TEXT NOT NULL,
    telefono     TEXT NOT NULL,
    activo       INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0,1)),
    CHECK (length(id) = 36),
    CHECK (length(trim(especialidad)) >= 1),
    CHECK (length(trim(telefono)) >= 1)
);

-- =====================================================================
-- 2. CATÁLOGO Y CONFIGURACIÓN (RD-01, RF-27)
-- =====================================================================

CREATE TABLE categoria (
    id                TEXT PRIMARY KEY,
    nombre            TEXT NOT NULL COLLATE NOCASE UNIQUE CHECK (length(trim(nombre)) >= 1),
    prioridad_sugerida TEXT CHECK (prioridad_sugerida IN ('Urgente','Normal','Menor'))
,  -- NULL => la categoría exige subtipo (/requiereSubtipo)
    CHECK (length(id) = 36)
);

CREATE TABLE subtipo (
    categoria_id       TEXT NOT NULL REFERENCES categoria (id),
    nombre             TEXT NOT NULL COLLATE NOCASE CHECK (length(trim(nombre)) >= 1),
    prioridad_sugerida TEXT NOT NULL CHECK (prioridad_sugerida IN ('Urgente','Normal','Menor')),
    PRIMARY KEY (categoria_id, nombre)
);

CREATE TABLE parametro (
    clave       TEXT PRIMARY KEY
                CHECK (clave IN ('objetivoPrimeraAtencionUrgenteHoras','objetivoResolucionUrgenteHoras',
                                 'objetivoResolucionNormalHoras','objetivoResolucionMenorHoras',
                                 'umbralEstancamientoUrgenteHoras','umbralEstancamientoNormalHoras',
                                 'umbralEstancamientoMenorHoras','plazoConfirmacionHoras',
                                 'plazoReaperturaDias','ventanaRecurrenciaDias','minimoRecurrencia')),
    descripcion TEXT NOT NULL,
    valor       NUMERIC NOT NULL CHECK (valor > 0),
    unidad      TEXT NOT NULL CHECK (unidad IN ('horas','dias','reportes')),
    CHECK ((clave LIKE '%Horas' AND unidad = 'horas') OR (clave LIKE '%Dias' AND unidad = 'dias')
           OR (clave = 'minimoRecurrencia' AND unidad = 'reportes'))  -- la unidad corresponde a la clave
);

CREATE TABLE cambio_parametro (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    clave          TEXT NOT NULL REFERENCES parametro (clave),
    valor_anterior NUMERIC NOT NULL,
    valor_nuevo    NUMERIC NOT NULL CHECK (valor_nuevo > 0),
    fecha          TEXT NOT NULL,
    modificado_por TEXT NOT NULL,
    modificado_por_perfil TEXT NOT NULL DEFAULT 'Administrador' CHECK (modificado_por_perfil = 'Administrador'),
    FOREIGN KEY (modificado_por, modificado_por_perfil)
        REFERENCES usuario_administracion (usuario_id, perfil_administracion),  -- RF-27: sólo el Administrador
    CHECK (fecha GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(fecha) IS NOT NULL),
    CHECK (valor_anterior > 0)
);

-- Valores iniciales (SRS RF-27)
INSERT INTO parametro (clave, descripcion, valor, unidad) VALUES
 ('objetivoPrimeraAtencionUrgenteHoras','Objetivo de primera atención «Urgente»',1,'horas'),
 ('objetivoResolucionUrgenteHoras','Objetivo de resolución «Urgente»',24,'horas'),
 ('objetivoResolucionNormalHoras','Objetivo de resolución «Normal»',72,'horas'),
 ('objetivoResolucionMenorHoras','Objetivo de resolución «Menor»',168,'horas'),
 ('umbralEstancamientoUrgenteHoras','Umbral de estancamiento «Urgente»',2,'horas'),
 ('umbralEstancamientoNormalHoras','Umbral de estancamiento «Normal»',24,'horas'),
 ('umbralEstancamientoMenorHoras','Umbral de estancamiento «Menor»',72,'horas'),
 ('plazoConfirmacionHoras','Plazo de confirmación del residente',72,'horas'),
 ('plazoReaperturaDias','Plazo para reabrir un reporte cerrado',30,'dias'),
 ('ventanaRecurrenciaDias','Ventana de recurrencia',90,'dias'),
 ('minimoRecurrencia','Mínimo de reportes para incidencia recurrente',3,'reportes');

-- =====================================================================
-- 3. REPORTE Y SEGUIMIENTO (RF-03 a RF-26)
-- =====================================================================

CREATE TABLE reporte (
    folio                  TEXT PRIMARY KEY CHECK (folio GLOB 'RY-[0-9][0-9][0-9][0-9][0-9][0-9]'),
    fecha_aviso            TEXT NOT NULL,
    fecha_captura          TEXT NOT NULL,
    medio_origen           TEXT NOT NULL
                           CHECK (medio_origen IN ('Sistema','WhatsApp','Llamada','Caseta','Correo','Presencial')),
    descripcion            TEXT NOT NULL CHECK (length(descripcion) BETWEEN 10 AND 1000),
    parte_afectada         TEXT CHECK (parte_afectada IS NULL OR length(parte_afectada) <= 200),
    referencia             TEXT CHECK (referencia IS NULL OR length(referencia) <= 200),
    es_peligroso           INTEGER NOT NULL DEFAULT 0 CHECK (es_peligroso IN (0,1)),
    autoriza_acceso        INTEGER CHECK (autoriza_acceso IN (0,1)),
    horarios_acceso        TEXT,
    desde_cuando           TEXT,
    habia_pasado_antes     INTEGER CHECK (habia_pasado_antes IN (0,1)),
    estado                 TEXT NOT NULL DEFAULT 'Reportado'
                           CHECK (estado IN ('Reportado','Asignado','EnProceso','Terminado','Cerrado','Cancelado','Unido')),
    prioridad_sugerida     TEXT NOT NULL CHECK (prioridad_sugerida IN ('Urgente','Normal','Menor')),
    prioridad              TEXT CHECK (prioridad IN ('Urgente','Normal','Menor')),
    responsabilidad        TEXT NOT NULL DEFAULT 'PorDeterminar'
                           CHECK (responsabilidad IN ('Comun','Privada','PorDeterminar')),
    responsable_costo      TEXT CHECK (responsable_costo IN ('Condominio','Condomino')),
    fecha_visita           TEXT,
    nombre_referencia      TEXT,
    contacto_referencia    TEXT,

    -- Asociaciones
    ubicacion_id           TEXT NOT NULL REFERENCES ubicacion (id),
    ubicacion_origen_id    TEXT REFERENCES ubicacion (id),
    reportante_id          TEXT REFERENCES residente (usuario_id),
    capturado_por          TEXT NOT NULL REFERENCES usuario (id),
    responsable_usuario_id   TEXT REFERENCES usuario_mantenimiento (usuario_id),   -- Responsable (1 de 2)
    responsable_proveedor_id TEXT REFERENCES proveedor_sin_acceso (id),            -- Responsable (2 de 2)
    categoria_id           TEXT NOT NULL REFERENCES categoria (id),
    subtipo_nombre         TEXT,
    posible_duplicado_de   TEXT REFERENCES reporte (folio),
    reporte_principal      TEXT REFERENCES reporte (folio),

    FOREIGN KEY (categoria_id, subtipo_nombre) REFERENCES subtipo (categoria_id, nombre), -- RD-01: el subtipo pertenece a la categoría
    CHECK (reportante_id IS NOT NULL OR nombre_referencia IS NOT NULL),                 -- RF-04
    CHECK (responsable_usuario_id IS NULL OR responsable_proveedor_id IS NULL),         -- a lo más un responsable (RF-06)
    CHECK ((estado = 'Unido') = (reporte_principal IS NOT NULL)),                       -- D: Unido <=> tiene principal
    CHECK (reporte_principal IS NULL OR reporte_principal <> folio),
    CHECK (posible_duplicado_de IS NULL OR posible_duplicado_de <> folio),
    CHECK (autoriza_acceso IS NOT NULL OR horarios_acceso IS NULL),
    CHECK (fecha_aviso GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(fecha_aviso) IS NOT NULL),
    CHECK (fecha_captura GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(fecha_captura) IS NOT NULL),
    CHECK (fecha_visita IS NULL OR (fecha_visita GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(fecha_visita) IS NOT NULL)),
    CHECK (fecha_captura >= fecha_aviso),  -- RF-03/RF-04: la captura es posterior (o igual) al aviso
    CHECK (nombre_referencia IS NULL OR length(trim(nombre_referencia)) > 0),
    CHECK (estado NOT IN ('Asignado','EnProceso','Terminado','Cerrado')
           OR (prioridad IS NOT NULL AND (responsable_usuario_id IS NOT NULL OR responsable_proveedor_id IS NOT NULL)))  -- RF-06: prioridad y responsable obligatorios al asignar
);

-- EntradaHistorial (abstracta; solo inserción) ------------------------------
-- 'tipo' persiste el discriminador. Sólo se persisten los 6 tipos con subclase;
-- Detencion, Reanudacion, Confirmacion, AvisoEnviado, Delegacion, UnionDuplicado y
-- MarcaDuplicado son proyecciones de otras tablas (nota N3 del diagrama).
CREATE TABLE entrada_historial (
    id             TEXT PRIMARY KEY,
    reporte_folio  TEXT NOT NULL REFERENCES reporte (folio),
    fecha          TEXT NOT NULL,
    tipo           TEXT NOT NULL
                   CHECK (tipo IN ('CambioEstado','Reclasificacion','Nota','Correccion','Costo','PersistenciaIndicada')),
    campo          TEXT,
    valor_anterior TEXT,
    valor_nuevo    TEXT,
    comentario     TEXT,
    autor_id       TEXT NOT NULL REFERENCES usuario (id),
    UNIQUE (id, tipo),
    CHECK (length(id) = 36),
    CHECK (fecha GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(fecha) IS NOT NULL),
    CHECK (comentario IS NULL OR length(comentario) <= 1000),
    CHECK (tipo NOT IN ('Reclasificacion','Correccion') OR (campo IS NOT NULL AND valor_nuevo IS NOT NULL))  -- deben decir qué cambió
);

CREATE TABLE cambio_estado (
    entrada_id              TEXT PRIMARY KEY,
    tipo                    TEXT NOT NULL DEFAULT 'CambioEstado' CHECK (tipo = 'CambioEstado'),
    estado_anterior         TEXT CHECK (estado_anterior IN ('Reportado','Asignado','EnProceso','Terminado','Cerrado','Cancelado','Unido')),
                            -- NULL sólo en la entrada de alta del reporte
    estado_nuevo            TEXT NOT NULL CHECK (estado_nuevo IN ('Reportado','Asignado','EnProceso','Terminado','Cerrado','Cancelado','Unido')),
    actua_en_nombre_de_id   TEXT REFERENCES proveedor_sin_acceso (id),
    FOREIGN KEY (entrada_id, tipo) REFERENCES entrada_historial (id, tipo),
    CHECK (estado_anterior IS NULL OR estado_anterior <> estado_nuevo)
);

CREATE TABLE reclasificacion (
    entrada_id TEXT PRIMARY KEY,
    tipo       TEXT NOT NULL DEFAULT 'Reclasificacion' CHECK (tipo = 'Reclasificacion'),
    FOREIGN KEY (entrada_id, tipo) REFERENCES entrada_historial (id, tipo)
);

CREATE TABLE version_correccion (
    entrada_id TEXT PRIMARY KEY,
    tipo       TEXT NOT NULL DEFAULT 'Correccion' CHECK (tipo = 'Correccion'),
    FOREIGN KEY (entrada_id, tipo) REFERENCES entrada_historial (id, tipo)
);

CREATE TABLE nota_avance (
    entrada_id TEXT PRIMARY KEY,
    tipo       TEXT NOT NULL DEFAULT 'Nota' CHECK (tipo = 'Nota'),
    texto      TEXT NOT NULL CHECK (length(texto) BETWEEN 1 AND 500),
    FOREIGN KEY (entrada_id, tipo) REFERENCES entrada_historial (id, tipo)
);

CREATE TABLE costo (
    entrada_id     TEXT PRIMARY KEY,
    tipo           TEXT NOT NULL DEFAULT 'Costo' CHECK (tipo = 'Costo'),
    monto          NUMERIC CHECK (monto IS NULL OR monto >= 0),      -- opcional (RF-20)
    pagador        TEXT NOT NULL CHECK (pagador IN ('Condominio','Condomino')),
    anula_costo_id TEXT UNIQUE REFERENCES costo (entrada_id),        -- 0..1 <-> 0..1: una corrección anula una sola entrada, una sola vez
    CHECK (anula_costo_id IS NULL OR anula_costo_id <> entrada_id),
    FOREIGN KEY (entrada_id, tipo) REFERENCES entrada_historial (id, tipo)
);

CREATE TABLE indicacion_persistencia (
    entrada_id   TEXT PRIMARY KEY,
    tipo         TEXT NOT NULL DEFAULT 'PersistenciaIndicada' CHECK (tipo = 'PersistenciaIndicada'),
    residente_id TEXT NOT NULL REFERENCES residente (usuario_id),
    FOREIGN KEY (entrada_id, tipo) REFERENCES entrada_historial (id, tipo)
);

-- CicloAtencion: PK natural (reporte, numero) -------------------------------
CREATE TABLE ciclo_atencion (
    reporte_folio              TEXT NOT NULL REFERENCES reporte (folio),
    numero                     INTEGER NOT NULL CHECK (numero >= 1),
    inicio                     TEXT NOT NULL,
    fin                        TEXT,
    nota_trabajo               TEXT CHECK (nota_trabajo IS NULL OR length(nota_trabajo) <= 1000),
    pendientes                 TEXT CHECK (pendientes IS NULL OR length(pendientes) <= 1000),
    sin_evidencia_fotografica  INTEGER NOT NULL DEFAULT 0 CHECK (sin_evidencia_fotografica IN (0,1)),
    justificacion_sin_evidencia TEXT,
    garantia_vencimiento       TEXT,                                  -- fecha YYYY-MM-DD
    plazo_confirmacion_hasta   TEXT,
    PRIMARY KEY (reporte_folio, numero),
    CHECK (fin IS NULL OR fin >= inicio),
    CHECK (sin_evidencia_fotografica = 0 OR justificacion_sin_evidencia IS NOT NULL),  -- RD-09
    CHECK (inicio GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(inicio) IS NOT NULL),
    CHECK (fin IS NULL OR (fin GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(fin) IS NOT NULL)),
    CHECK (plazo_confirmacion_hasta IS NULL OR (plazo_confirmacion_hasta GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(plazo_confirmacion_hasta) IS NOT NULL)),
    CHECK (garantia_vencimiento IS NULL OR date(garantia_vencimiento) = garantia_vencimiento)
);

CREATE TABLE confirmacion_residente (
    reporte_folio TEXT NOT NULL,
    ciclo_numero  INTEGER NOT NULL,
    respuesta     TEXT NOT NULL CHECK (respuesta IN ('YaQuedo','SigueFallando')),
    comentario    TEXT CHECK (comentario IS NULL OR length(comentario) <= 1000),
    fecha         TEXT NOT NULL,
    respondida_por TEXT NOT NULL REFERENCES residente (usuario_id),
    PRIMARY KEY (reporte_folio, ciclo_numero),                         -- 0..1 por ciclo
    FOREIGN KEY (reporte_folio, ciclo_numero) REFERENCES ciclo_atencion (reporte_folio, numero),
    CHECK (respuesta <> 'SigueFallando' OR (comentario IS NOT NULL AND length(trim(comentario)) > 0)),  -- RF-09
    CHECK (fecha GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(fecha) IS NOT NULL)
);

CREATE TABLE detencion (
    id            TEXT PRIMARY KEY,
    reporte_folio TEXT NOT NULL REFERENCES reporte (folio),
    motivo        TEXT NOT NULL
                  CHECK (motivo IN ('AccesoAlDepartamento','EsperaDeProveedor','EsperaDePieza','EsperaDeAutorizacionDeGasto','Otro')),
    texto_otro    TEXT,
    fecha_inicio  TEXT NOT NULL,
    fecha_fin     TEXT,
    autor_id      TEXT NOT NULL REFERENCES usuario (id),
    CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio),
    CHECK (motivo <> 'Otro' OR (texto_otro IS NOT NULL AND length(trim(texto_otro)) > 0)),
    CHECK (length(id) = 36),
    CHECK (fecha_inicio GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(fecha_inicio) IS NOT NULL),
    CHECK (fecha_fin IS NULL OR (fecha_fin GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(fecha_fin) IS NOT NULL))
);

-- Adjunto: pertenece al Reporte (etapa Alta) o a un CicloAtencion (etapa Evidencia) ---
CREATE TABLE adjunto (
    id            TEXT PRIMARY KEY,
    reporte_folio TEXT NOT NULL,
    ciclo_numero  INTEGER,                                            -- NULL <=> etapa Alta
    tipo          TEXT NOT NULL CHECK (tipo IN ('Foto','Video')),
    etapa         TEXT NOT NULL CHECK (etapa IN ('Alta','Evidencia')),
    nombre        TEXT NOT NULL,
    fecha         TEXT NOT NULL,
    formato       TEXT NOT NULL,                                      -- {interno}
    tamano_bytes  INTEGER NOT NULL CHECK (tamano_bytes > 0),          -- {interno}
    clave         TEXT NOT NULL UNIQUE,                               -- {interno} clave en AlmacenArchivos
    subido_por    TEXT NOT NULL REFERENCES usuario (id),
    FOREIGN KEY (reporte_folio) REFERENCES reporte (folio),
    FOREIGN KEY (reporte_folio, ciclo_numero) REFERENCES ciclo_atencion (reporte_folio, numero),  -- se omite si ciclo_numero es NULL
    CHECK ((etapa = 'Alta' AND ciclo_numero IS NULL) OR (etapa = 'Evidencia' AND ciclo_numero IS NOT NULL)),  -- {xor}
    CHECK (etapa = 'Alta' OR tipo = 'Foto'),  -- la evidencia de ciclo son sólo fotos
    CHECK (length(id) = 36),
    CHECK (fecha GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(fecha) IS NOT NULL),
    CHECK (length(trim(nombre)) >= 1)
);

CREATE TABLE registro_comparticion (
    id                        TEXT PRIMARY KEY,
    archivo_id                TEXT NOT NULL REFERENCES adjunto (id),
    proveedor_id              TEXT NOT NULL REFERENCES proveedor_sin_acceso (id),
    registrada_por            TEXT NOT NULL REFERENCES usuario_administracion (usuario_id),
    fecha                     TEXT NOT NULL,
    consentimiento_residente  INTEGER CHECK (consentimiento_residente IN (0,1)),
    CHECK (length(id) = 36),
    CHECK (fecha GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(fecha) IS NOT NULL)
);

-- Aviso (abstracta) -> AvisoSistema | EnvioCorreo ---------------------------
CREATE TABLE aviso (
    id            TEXT PRIMARY KEY,
    tipo          TEXT NOT NULL CHECK (tipo IN ('Sistema','Correo')),
    reporte_folio TEXT NOT NULL REFERENCES reporte (folio),
    evento        TEXT NOT NULL,
    fecha         TEXT NOT NULL,
    UNIQUE (id, tipo),
    CHECK (length(id) = 36),
    CHECK (fecha GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(fecha) IS NOT NULL)
);

CREATE TABLE aviso_sistema (
    aviso_id               TEXT PRIMARY KEY,
    tipo                   TEXT NOT NULL DEFAULT 'Sistema' CHECK (tipo = 'Sistema'),
    destinatario_usuario_id TEXT NOT NULL REFERENCES usuario (id),
    mensaje                TEXT NOT NULL,
    leido                  INTEGER NOT NULL DEFAULT 0 CHECK (leido IN (0,1)),
    FOREIGN KEY (aviso_id, tipo) REFERENCES aviso (id, tipo)
);

CREATE TABLE envio_correo (
    aviso_id             TEXT PRIMARY KEY,
    tipo                 TEXT NOT NULL DEFAULT 'Correo' CHECK (tipo = 'Correo'),
    destinatario         TEXT NOT NULL COLLATE NOCASE CHECK (destinatario LIKE '_%@_%._%'),
    estado               TEXT NOT NULL DEFAULT 'Pendiente' CHECK (estado IN ('Pendiente','Enviado','Fallido')),
    intentos             INTEGER NOT NULL DEFAULT 0 CHECK (intentos BETWEEN 0 AND 3),
    fecha_ultimo_intento TEXT,                                        -- {interno}
    FOREIGN KEY (aviso_id, tipo) REFERENCES aviso (id, tipo),
    CHECK (fecha_ultimo_intento IS NULL OR (fecha_ultimo_intento GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z' AND julianday(fecha_ultimo_intento) IS NOT NULL)),
    CHECK (estado <> 'Enviado' OR (intentos >= 1 AND fecha_ultimo_intento IS NOT NULL))
);

-- =====================================================================
-- 4. ÍNDICES
--    (las PK y las columnas UNIQUE ya crean su propio índice: usuario.correo,
--     reporte.folio, categoria.nombre, area_comun.nombre, unidad(torre,numero),
--     adjunto.clave, ...)
-- =====================================================================

-- Usuarios: búsqueda por nombre, listados por rol/estado, login por correo (UNIQUE)
CREATE INDEX ix_usuario_nombre        ON usuario (nombre COLLATE NOCASE);
CREATE INDEX ix_usuario_rol_estado    ON usuario (rol, estado_cuenta);
CREATE INDEX ix_enlace_usuario        ON enlace_acceso (usuario_id, tipo);
CREATE INDEX ix_enlace_vence          ON enlace_acceso (vence_en) WHERE usado_en IS NULL;
CREATE INDEX ix_delegacion_auxiliar   ON delegacion (auxiliar_id, habilitada);
CREATE INDEX ix_delegacion_otorgada   ON delegacion (otorgada_por);
CREATE UNIQUE INDEX ux_delegacion_vigente ON delegacion (auxiliar_id) WHERE habilitada = 1 AND fecha_fin IS NULL;  -- una delegación abierta por Auxiliar

-- Padrón: búsqueda de unidades, vinculaciones y proveedores
CREATE INDEX ix_unidad_busqueda       ON unidad (torre, piso, numero);
CREATE INDEX ix_unidad_prop_correo    ON unidad (propietario_correo);
CREATE UNIQUE INDEX ux_vinculacion_activa ON vinculacion_unidad (residente_id) WHERE fecha_fin IS NULL;  -- D1: a lo más una activa
CREATE INDEX ix_vinculacion_unidad    ON vinculacion_unidad (unidad_id, fecha_fin);
CREATE INDEX ix_vinculacion_residente ON vinculacion_unidad (residente_id, fecha_inicio);   -- historial de un residente
CREATE INDEX ix_ubicacion_activa      ON ubicacion (tipo, activa);
CREATE INDEX ix_proveedor_nombre      ON proveedor_sin_acceso (nombre COLLATE NOCASE);
CREATE INDEX ix_proveedor_activo      ON proveedor_sin_acceso (activo, especialidad);
CREATE INDEX ix_mant_tipo             ON usuario_mantenimiento (tipo, especialidad);

-- Reportes: tableros, bandejas y filtros de RF-12/13/22
CREATE INDEX ix_reporte_estado_prio   ON reporte (estado, prioridad, fecha_aviso);
CREATE INDEX ix_reporte_fecha_aviso   ON reporte (fecha_aviso);
CREATE INDEX ix_reporte_ubicacion     ON reporte (ubicacion_id, estado);
CREATE INDEX ix_reporte_recurrencia   ON reporte (categoria_id, ubicacion_origen_id, fecha_aviso);   -- RD-02 incidencia recurrente
CREATE INDEX ix_reporte_reportante    ON reporte (reportante_id, fecha_aviso);
CREATE INDEX ix_reporte_resp_usuario  ON reporte (responsable_usuario_id, estado)   WHERE responsable_usuario_id IS NOT NULL;
CREATE INDEX ix_reporte_resp_prov     ON reporte (responsable_proveedor_id, estado) WHERE responsable_proveedor_id IS NOT NULL;
CREATE INDEX ix_reporte_capturado     ON reporte (capturado_por);
CREATE INDEX ix_reporte_origen        ON reporte (ubicacion_origen_id) WHERE ubicacion_origen_id IS NOT NULL;
CREATE INDEX ix_reporte_principal     ON reporte (reporte_principal)     WHERE reporte_principal IS NOT NULL;
CREATE INDEX ix_reporte_duplicado     ON reporte (posible_duplicado_de)  WHERE posible_duplicado_de IS NOT NULL;
CREATE INDEX ix_reporte_categoria     ON reporte (categoria_id, subtipo_nombre);

-- Seguimiento
CREATE INDEX ix_historial_reporte     ON entrada_historial (reporte_folio, fecha);
CREATE INDEX ix_historial_autor       ON entrada_historial (autor_id, fecha);
CREATE INDEX ix_persist_residente     ON indicacion_persistencia (residente_id);
CREATE INDEX ix_cambio_estado_prov    ON cambio_estado (actua_en_nombre_de_id) WHERE actua_en_nombre_de_id IS NOT NULL;
CREATE INDEX ix_confirm_residente     ON confirmacion_residente (respondida_por);
CREATE INDEX ix_costo_anula           ON costo (anula_costo_id) WHERE anula_costo_id IS NOT NULL;
CREATE UNIQUE INDEX ux_ciclo_abierto  ON ciclo_atencion (reporte_folio) WHERE fin IS NULL;           -- un ciclo abierto por reporte
CREATE INDEX ix_ciclo_plazo           ON ciclo_atencion (plazo_confirmacion_hasta) WHERE plazo_confirmacion_hasta IS NOT NULL;
CREATE UNIQUE INDEX ux_detencion_abierta ON detencion (reporte_folio) WHERE fecha_fin IS NULL;       -- una detención abierta por reporte
CREATE INDEX ix_detencion_reporte     ON detencion (reporte_folio, fecha_inicio);
CREATE INDEX ix_adjunto_reporte       ON adjunto (reporte_folio, etapa, ciclo_numero);
CREATE UNIQUE INDEX ux_adjunto_video  ON adjunto (reporte_folio) WHERE tipo = 'Video';               -- 0..1 video por reporte
CREATE INDEX ix_compartir_archivo     ON registro_comparticion (archivo_id);
CREATE INDEX ix_compartir_proveedor   ON registro_comparticion (proveedor_id, fecha);

-- Avisos
CREATE INDEX ix_aviso_reporte         ON aviso (reporte_folio, fecha);
CREATE INDEX ix_aviso_sist_bandeja    ON aviso_sistema (destinatario_usuario_id, leido);
CREATE INDEX ix_correo_pendientes     ON envio_correo (estado, fecha_ultimo_intento) WHERE estado = 'Pendiente';

-- Catálogo y parámetros
CREATE INDEX ix_cambio_param          ON cambio_parametro (clave, fecha);

-- =====================================================================
-- 5. VISTAS (atributos derivados del diagrama)
-- =====================================================================
CREATE VIEW v_ubicacion AS
SELECT u.id, u.tipo, u.activa,
       CASE u.tipo WHEN 'Unidad' THEN un.torre || '-' || un.numero ELSE ac.nombre END AS etiqueta
FROM ubicacion u
LEFT JOIN unidad    un ON un.ubicacion_id = u.id
LEFT JOIN area_comun ac ON ac.ubicacion_id = u.id;

CREATE VIEW v_reporte_derivados AS
SELECT r.folio,
       (r.posible_duplicado_de IS NOT NULL)                                   AS posibleDuplicado,
       EXISTS (SELECT 1 FROM detencion d WHERE d.reporte_folio = r.folio AND d.fecha_fin IS NULL) AS detenido,
       MAX((SELECT count(*) FROM ciclo_atencion c WHERE c.reporte_folio = r.folio) - 1, 0) AS reaperturas
FROM reporte r;

-- =====================================================================
-- 6. DISPARADORES
-- =====================================================================

-- 6.1 Solo inserción (RNF-07): historial, costos, evidencias y registros no se editan ni se borran
CREATE TRIGGER trg_historial_no_upd BEFORE UPDATE ON entrada_historial BEGIN SELECT RAISE(ABORT,'entrada_historial es de solo inserción (RNF-07)'); END;
CREATE TRIGGER trg_historial_no_del BEFORE DELETE ON entrada_historial BEGIN SELECT RAISE(ABORT,'entrada_historial es de solo inserción (RNF-07)'); END;
CREATE TRIGGER trg_cambio_estado_no_upd BEFORE UPDATE ON cambio_estado BEGIN SELECT RAISE(ABORT,'cambio_estado es de solo inserción (RNF-07)'); END;
CREATE TRIGGER trg_cambio_estado_no_del BEFORE DELETE ON cambio_estado BEGIN SELECT RAISE(ABORT,'cambio_estado es de solo inserción (RNF-07)'); END;
CREATE TRIGGER trg_nota_no_upd BEFORE UPDATE ON nota_avance BEGIN SELECT RAISE(ABORT,'nota_avance es de solo inserción (RNF-07)'); END;
CREATE TRIGGER trg_nota_no_del BEFORE DELETE ON nota_avance BEGIN SELECT RAISE(ABORT,'nota_avance es de solo inserción (RNF-07)'); END;
CREATE TRIGGER trg_costo_no_upd BEFORE UPDATE ON costo BEGIN SELECT RAISE(ABORT,'costo es de solo inserción (RNF-07)'); END;
CREATE TRIGGER trg_costo_no_del BEFORE DELETE ON costo BEGIN SELECT RAISE(ABORT,'costo es de solo inserción (RNF-07)'); END;
CREATE TRIGGER trg_persist_no_upd BEFORE UPDATE ON indicacion_persistencia BEGIN SELECT RAISE(ABORT,'indicacion_persistencia es de solo inserción (RNF-07)'); END;
CREATE TRIGGER trg_persist_no_del BEFORE DELETE ON indicacion_persistencia BEGIN SELECT RAISE(ABORT,'indicacion_persistencia es de solo inserción (RNF-07)'); END;
CREATE TRIGGER trg_reclas_no_del BEFORE DELETE ON reclasificacion BEGIN SELECT RAISE(ABORT,'reclasificacion es de solo inserción (RNF-07)'); END;
CREATE TRIGGER trg_correccion_no_del BEFORE DELETE ON version_correccion BEGIN SELECT RAISE(ABORT,'version_correccion es de solo inserción (RNF-07)'); END;
CREATE TRIGGER trg_adjunto_no_upd BEFORE UPDATE ON adjunto BEGIN SELECT RAISE(ABORT,'adjunto es de solo inserción (RNF-07)'); END;
CREATE TRIGGER trg_adjunto_no_del BEFORE DELETE ON adjunto BEGIN SELECT RAISE(ABORT,'adjunto es de solo inserción (RNF-07)'); END;
CREATE TRIGGER trg_compartir_no_upd BEFORE UPDATE ON registro_comparticion BEGIN SELECT RAISE(ABORT,'registro_comparticion es de solo inserción (RNF-07)'); END;
CREATE TRIGGER trg_compartir_no_del BEFORE DELETE ON registro_comparticion BEGIN SELECT RAISE(ABORT,'registro_comparticion es de solo inserción (RNF-07)'); END;
CREATE TRIGGER trg_cambio_param_no_upd BEFORE UPDATE ON cambio_parametro BEGIN SELECT RAISE(ABORT,'cambio_parametro es de solo inserción (RF-27)'); END;
CREATE TRIGGER trg_cambio_param_no_del BEFORE DELETE ON cambio_parametro BEGIN SELECT RAISE(ABORT,'cambio_parametro es de solo inserción (RF-27)'); END;
CREATE TRIGGER trg_reporte_no_del BEFORE DELETE ON reporte BEGIN SELECT RAISE(ABORT,'los reportes no se eliminan (RNF-07)'); END;
CREATE TRIGGER trg_detencion_no_del BEFORE DELETE ON detencion BEGIN SELECT RAISE(ABORT,'detencion no se elimina (RNF-07)'); END;
-- La detención sólo puede cambiar para cerrarse (fecha_fin) una vez.
CREATE TRIGGER trg_detencion_upd BEFORE UPDATE ON detencion
WHEN NEW.id <> OLD.id OR NEW.reporte_folio <> OLD.reporte_folio OR NEW.motivo <> OLD.motivo
  OR IFNULL(NEW.texto_otro,'') <> IFNULL(OLD.texto_otro,'') OR NEW.fecha_inicio <> OLD.fecha_inicio
  OR NEW.autor_id <> OLD.autor_id OR OLD.fecha_fin IS NOT NULL
BEGIN SELECT RAISE(ABORT,'una detención sólo puede cerrarse una vez (RF-18)'); END;

-- 6.2 Límite de fotos (RF-03, RF-08): 0..5 por reporte (Alta) y 0..5 por ciclo (Evidencia)
CREATE TRIGGER trg_adjunto_max_fotos BEFORE INSERT ON adjunto
WHEN NEW.tipo = 'Foto' AND (
     SELECT count(*) FROM adjunto a
     WHERE a.reporte_folio = NEW.reporte_folio AND a.tipo = 'Foto' AND a.etapa = NEW.etapa
       AND IFNULL(a.ciclo_numero,-1) = IFNULL(NEW.ciclo_numero,-1)) >= 5
BEGIN SELECT RAISE(ABORT,'máximo 5 fotos por reporte o por ciclo'); END;

-- 6.4 RD-13: parte_afectada sólo en unidades; referencia sólo en áreas comunes
CREATE TRIGGER trg_reporte_rd13_ins BEFORE INSERT ON reporte
WHEN (NEW.parte_afectada IS NOT NULL AND (SELECT tipo FROM ubicacion WHERE id = NEW.ubicacion_id) <> 'Unidad')
  OR (NEW.referencia     IS NOT NULL AND (SELECT tipo FROM ubicacion WHERE id = NEW.ubicacion_id) <> 'AreaComun')
BEGIN SELECT RAISE(ABORT,'parte_afectada aplica a unidades y referencia a áreas comunes (RD-13)'); END;
CREATE TRIGGER trg_reporte_rd13_upd BEFORE UPDATE OF parte_afectada, referencia, ubicacion_id ON reporte
WHEN (NEW.parte_afectada IS NOT NULL AND (SELECT tipo FROM ubicacion WHERE id = NEW.ubicacion_id) <> 'Unidad')
  OR (NEW.referencia     IS NOT NULL AND (SELECT tipo FROM ubicacion WHERE id = NEW.ubicacion_id) <> 'AreaComun')
BEGIN SELECT RAISE(ABORT,'parte_afectada aplica a unidades y referencia a áreas comunes (RD-13)'); END;

-- 6.5 RD-01 / RF-03: el subtipo es obligatorio en las categorías que definen subtipos
CREATE TRIGGER trg_reporte_subtipo_ins BEFORE INSERT ON reporte
WHEN NEW.subtipo_nombre IS NULL AND EXISTS (SELECT 1 FROM subtipo WHERE categoria_id = NEW.categoria_id)
BEGIN SELECT RAISE(ABORT,'la categoría exige subtipo (RD-01)'); END;
CREATE TRIGGER trg_reporte_subtipo_upd BEFORE UPDATE OF categoria_id, subtipo_nombre ON reporte
WHEN NEW.subtipo_nombre IS NULL AND EXISTS (SELECT 1 FROM subtipo WHERE categoria_id = NEW.categoria_id)
BEGIN SELECT RAISE(ABORT,'la categoría exige subtipo (RD-01)'); END;
