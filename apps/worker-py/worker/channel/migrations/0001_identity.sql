CREATE TABLE channels (
    channel_id TEXT PRIMARY KEY,
    public_name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE product_lines (
    product_line_id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL REFERENCES channels(channel_id),
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE series (
    series_id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL REFERENCES channels(channel_id),
    product_line_id TEXT NOT NULL REFERENCES product_lines(product_line_id),
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE content_items (
    content_id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL REFERENCES channels(channel_id),
    product_line_id TEXT NOT NULL REFERENCES product_lines(product_line_id),
    series_id TEXT NOT NULL REFERENCES series(series_id),
    local_item_id TEXT NOT NULL,
    title TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(series_id, local_item_id)
);

CREATE TABLE source_aliases (
    source_system TEXT NOT NULL,
    source_item_id TEXT NOT NULL,
    content_id TEXT NOT NULL REFERENCES content_items(content_id),
    source_locator TEXT NOT NULL,
    last_source_state TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    PRIMARY KEY(source_system, source_item_id)
);

CREATE TABLE artifacts (
    artifact_id TEXT PRIMARY KEY,
    content_id TEXT NOT NULL REFERENCES content_items(content_id),
    kind TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    source_locator TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(content_id, kind, sha256),
    UNIQUE(sha256)
);

CREATE TABLE publications (
    publication_id TEXT PRIMARY KEY,
    content_id TEXT NOT NULL REFERENCES content_items(content_id),
    provider TEXT NOT NULL,
    remote_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(provider, remote_id)
);

CREATE TABLE import_runs (
    import_run_id TEXT PRIMARY KEY,
    source_system TEXT NOT NULL,
    source_locator TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    collected_at TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    total_count INTEGER NOT NULL DEFAULT 0,
    inserted_count INTEGER NOT NULL DEFAULT 0,
    updated_count INTEGER NOT NULL DEFAULT 0,
    unchanged_count INTEGER NOT NULL DEFAULT 0,
    collided_count INTEGER NOT NULL DEFAULT 0,
    collision_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE import_records (
    import_record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_run_id TEXT NOT NULL REFERENCES import_runs(import_run_id),
    source_item_id TEXT NOT NULL,
    source_locator TEXT NOT NULL,
    incoming_content_id TEXT NOT NULL,
    normalized_payload TEXT NOT NULL,
    raw_payload TEXT NOT NULL,
    raw_payload_sha256 TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK(outcome IN ('inserted', 'updated', 'unchanged', 'collision')),
    created_at TEXT NOT NULL,
    UNIQUE(import_run_id, source_item_id)
);

CREATE TABLE identity_collisions (
    collision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_run_id TEXT NOT NULL REFERENCES import_runs(import_run_id),
    import_record_id INTEGER NOT NULL REFERENCES import_records(import_record_id),
    source_system TEXT NOT NULL,
    source_item_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    identity_key TEXT NOT NULL,
    existing_content_id TEXT,
    incoming_content_id TEXT NOT NULL,
    detail TEXT NOT NULL,
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    resolution_note TEXT
);

CREATE INDEX idx_content_product_line ON content_items(product_line_id);
CREATE INDEX idx_alias_content ON source_aliases(content_id);
CREATE INDEX idx_artifact_content ON artifacts(content_id);
CREATE INDEX idx_publication_content ON publications(content_id);
CREATE INDEX idx_collision_unresolved ON identity_collisions(resolved_at, collision_id);

