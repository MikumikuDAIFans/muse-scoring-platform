-- Schema bootstrap and compatibility migration for Muse Scoring Platform.

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
    r2_url TEXT,
    object_key TEXT,
    public_url TEXT,
    status VARCHAR(16) DEFAULT 'pending',
    score_count INTEGER DEFAULT 0,
    deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE images ADD COLUMN IF NOT EXISTS r2_url TEXT;
ALTER TABLE images ADD COLUMN IF NOT EXISTS object_key TEXT;
ALTER TABLE images ADD COLUMN IF NOT EXISTS public_url TEXT;
ALTER TABLE images ADD COLUMN IF NOT EXISTS status VARCHAR(16) DEFAULT 'pending';

CREATE TABLE IF NOT EXISTS scores (
    id BIGSERIAL PRIMARY KEY,
    image_id BIGINT REFERENCES images(id),
    user_id BIGINT REFERENCES users(id),
    task_id BIGINT,
    aesthetic_score INTEGER CHECK (aesthetic_score BETWEEN 1 AND 10),
    completeness_score INTEGER CHECK (completeness_score BETWEEN 1 AND 10),
    submitted_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE scores ADD COLUMN IF NOT EXISTS task_id BIGINT;

CREATE TABLE IF NOT EXISTS annotation_tasks (
    id BIGSERIAL PRIMARY KEY,
    image_id BIGINT NOT NULL REFERENCES images(id),
    user_id BIGINT NOT NULL REFERENCES users(id),
    status VARCHAR(16) NOT NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    submitted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_scores_unique ON scores (user_id, image_id);

CREATE TABLE IF NOT EXISTS audit_exports (
    id BIGSERIAL PRIMARY KEY,
    admin_id BIGINT REFERENCES users(id),
    export_type VARCHAR(16),
    filters JSONB,
    record_count INTEGER,
    exported_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scores_user ON scores (user_id);
CREATE INDEX IF NOT EXISTS idx_scores_submitted ON scores (submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_images_score_count ON images (score_count ASC) WHERE deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_images_status ON images (status) WHERE deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON annotation_tasks (user_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_image_status ON annotation_tasks (image_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_expires_at ON annotation_tasks (expires_at);
