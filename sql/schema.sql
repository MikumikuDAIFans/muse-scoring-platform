-- 建表DDL
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    role VARCHAR(16) DEFAULT 'user',
    failed_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMPTZ,
    last_login TIMESTAMPTZ,
    banned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS images (
    id BIGSERIAL PRIMARY KEY,
    r2_url TEXT NOT NULL,
    score_count INTEGER DEFAULT 0,
    deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scores (
    id BIGSERIAL PRIMARY KEY,
    image_id BIGINT REFERENCES images(id),
    user_id BIGINT REFERENCES users(id),
    aesthetic_score INTEGER CHECK (aesthetic_score BETWEEN 1 AND 10),
    completeness_score INTEGER CHECK (completeness_score BETWEEN 1 AND 10),
    submitted_at TIMESTAMPTZ DEFAULT NOW()
);

-- 唯一约束：同一用户对同一图片只能打分一次
CREATE UNIQUE INDEX IF NOT EXISTS idx_scores_unique ON scores (user_id, image_id);

-- 审计导出记录表
CREATE TABLE IF NOT EXISTS audit_exports (
    id BIGSERIAL PRIMARY KEY,
    admin_id BIGINT REFERENCES users(id),
    export_type VARCHAR(16),
    filters JSONB,
    record_count INTEGER,
    exported_at TIMESTAMPTZ DEFAULT NOW()
);

-- 性能索引
CREATE INDEX IF NOT EXISTS idx_scores_user ON scores (user_id);
CREATE INDEX IF NOT EXISTS idx_scores_submitted ON scores (submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_images_score_count ON images (score_count ASC) WHERE deleted = FALSE;
