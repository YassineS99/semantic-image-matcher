CREATE TABLE api_calls (
    id SERIAL PRIMARY KEY,
    call_type VARCHAR(20) NOT NULL,
    reference_id INTEGER,
    model VARCHAR(100) NOT NULL,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    estimated_cost_usd NUMERIC(10, 6) NOT NULL DEFAULT 0,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_api_calls_call_type ON api_calls(call_type);