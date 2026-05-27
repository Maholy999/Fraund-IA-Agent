-- ============================================================
-- FraudIA Claims — Schema PostgreSQL
-- ============================================================

-- Extensiones
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================
-- TABLA: usuarios
-- ============================================================
CREATE TABLE IF NOT EXISTS usuarios (
    id            UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    username      VARCHAR(50)  UNIQUE NOT NULL,
    email         VARCHAR(120) UNIQUE NOT NULL,
    nombre        VARCHAR(100) NOT NULL,
    rol           VARCHAR(20)  NOT NULL DEFAULT 'analista'
                               CHECK (rol IN ('admin', 'analista', 'supervisor')),
    password_hash VARCHAR(255) NOT NULL,
    activo        BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLA: proveedores
-- ============================================================
CREATE TABLE IF NOT EXISTS proveedores (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(150) UNIQUE NOT NULL,
    ciudad          VARCHAR(80),
    tipo            VARCHAR(80),
    total_siniestros INT NOT NULL DEFAULT 0,
    alertas_activas  INT NOT NULL DEFAULT 0,
    score_riesgo     SMALLINT NOT NULL DEFAULT 0 CHECK (score_riesgo BETWEEN 0 AND 100),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLA: siniestros
-- ============================================================
CREATE TABLE IF NOT EXISTS siniestros (
    id                SERIAL PRIMARY KEY,
    id_siniestro      VARCHAR(30)  UNIQUE NOT NULL,
    cliente           VARCHAR(150) NOT NULL,
    tipo_siniestro    VARCHAR(80)  NOT NULL,
    monto_reclamado   NUMERIC(12, 2) NOT NULL CHECK (monto_reclamado >= 0),
    fecha_incidente   DATE         NOT NULL,
    fecha_poliza      DATE         NOT NULL,
    ciudad            VARCHAR(80),
    proveedor         VARCHAR(150),
    proveedor_id      INT REFERENCES proveedores(id) ON DELETE SET NULL,
    historial_reclamos SMALLINT    NOT NULL DEFAULT 0 CHECK (historial_reclamos >= 0),
    narrativa         TEXT,

    -- Resultados del análisis
    score_riesgo      SMALLINT     NOT NULL DEFAULT 0 CHECK (score_riesgo BETWEEN 0 AND 100),
    nivel_riesgo      VARCHAR(10)  NOT NULL DEFAULT 'Bajo'
                                   CHECK (nivel_riesgo IN ('Bajo', 'Medio', 'Alto')),
    alertas           JSONB        NOT NULL DEFAULT '[]',
    score_reglas      SMALLINT     DEFAULT 0,
    score_ml          SMALLINT     DEFAULT 0,
    score_nlp         SMALLINT     DEFAULT 0,
    similitud_max     NUMERIC(4,3) DEFAULT 0,
    es_anomalia       BOOLEAN      DEFAULT FALSE,
    explicacion_ia    TEXT,
    estado            VARCHAR(20)  NOT NULL DEFAULT 'pendiente'
                                   CHECK (estado IN ('pendiente', 'en_revision', 'cerrado', 'aprobado', 'rechazado')),

    -- Auditoría
    analista_id       UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    fecha_registro    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLA: historial_alertas
-- ============================================================
CREATE TABLE IF NOT EXISTS historial_alertas (
    id             SERIAL PRIMARY KEY,
    siniestro_id   INT NOT NULL REFERENCES siniestros(id) ON DELETE CASCADE,
    tipo_alerta    VARCHAR(60)  NOT NULL,
    descripcion    TEXT         NOT NULL,
    peso           SMALLINT     NOT NULL DEFAULT 0,
    activa         BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLA: conversaciones_ia
-- ============================================================
CREATE TABLE IF NOT EXISTS conversaciones_ia (
    id             SERIAL PRIMARY KEY,
    usuario_id     UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    titulo         VARCHAR(200),
    mensajes       JSONB NOT NULL DEFAULT '[]',
    siniestro_id   INT REFERENCES siniestros(id) ON DELETE SET NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLA: reportes
-- ============================================================
CREATE TABLE IF NOT EXISTS reportes (
    id             SERIAL PRIMARY KEY,
    titulo         VARCHAR(200) NOT NULL,
    tipo           VARCHAR(50)  NOT NULL CHECK (tipo IN ('individual', 'ejecutivo', 'alertas', 'proveedor')),
    siniestro_id   INT REFERENCES siniestros(id) ON DELETE SET NULL,
    generado_por   UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    ruta_archivo   VARCHAR(500),
    contenido_json JSONB,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- ÍNDICES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_siniestros_nivel_riesgo  ON siniestros(nivel_riesgo);
CREATE INDEX IF NOT EXISTS idx_siniestros_score         ON siniestros(score_riesgo DESC);
CREATE INDEX IF NOT EXISTS idx_siniestros_fecha         ON siniestros(fecha_registro DESC);
CREATE INDEX IF NOT EXISTS idx_siniestros_proveedor     ON siniestros(proveedor);
CREATE INDEX IF NOT EXISTS idx_siniestros_cliente       ON siniestros USING gin (to_tsvector('spanish', cliente));
CREATE INDEX IF NOT EXISTS idx_siniestros_narrativa     ON siniestros USING gin (to_tsvector('spanish', narrativa));
CREATE INDEX IF NOT EXISTS idx_alertas_siniestro        ON historial_alertas(siniestro_id);
CREATE INDEX IF NOT EXISTS idx_conv_usuario             ON conversaciones_ia(usuario_id);

-- ============================================================
-- TRIGGER: updated_at automático
-- ============================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_siniestros_updated
    BEFORE UPDATE ON siniestros
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_usuarios_updated
    BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ============================================================
-- DATOS INICIALES: usuario admin demo
-- ============================================================
INSERT INTO usuarios (username, email, nombre, rol, password_hash)
VALUES ('admin', 'admin@fraudia.com', 'Administrador FraudIA', 'admin',
        '$2b$12$demo_hash_replace_in_production')
ON CONFLICT (username) DO NOTHING;
