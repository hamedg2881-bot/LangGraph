CREATE TABLE IF NOT EXISTS model_registry_models (
    id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    provider TEXT NOT NULL DEFAULT 'nvidia-dynamo',
    architecture TEXT,
    quantization TEXT,
    context_length INTEGER,
    approval_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (approval_status IN ('pending', 'approved', 'rejected')),
    is_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE TABLE IF NOT EXISTS model_registry_capabilities (
    model_id TEXT NOT NULL REFERENCES model_registry_models(id) ON DELETE CASCADE,
    capability TEXT NOT NULL
        CHECK (capability IN ('chat', 'vision', 'reasoning', 'coding', 'tool_calling')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (model_id, capability)
);

CREATE TABLE IF NOT EXISTS model_registry_approvals (
    id BIGSERIAL PRIMARY KEY,
    model_id TEXT NOT NULL REFERENCES model_registry_models(id) ON DELETE CASCADE,
    action TEXT NOT NULL
        CHECK (action IN ('approved', 'rejected', 'enabled', 'disabled', 'updated')),
    actor TEXT NOT NULL DEFAULT 'admin',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_model_registry_models_approval
    ON model_registry_models (approval_status, is_enabled);

CREATE INDEX IF NOT EXISTS idx_model_registry_approvals_model
    ON model_registry_approvals (model_id, created_at DESC);
