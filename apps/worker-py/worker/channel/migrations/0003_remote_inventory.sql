CREATE TABLE remote_captures (
    capture_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    scope TEXT NOT NULL,
    source_locator TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    collected_at TEXT NOT NULL,
    item_count INTEGER NOT NULL,
    UNIQUE(provider, channel_id, scope, source_sha256)
);

CREATE TABLE remote_inventory_items (
    capture_id TEXT NOT NULL REFERENCES remote_captures(capture_id),
    remote_id TEXT NOT NULL,
    title TEXT NOT NULL,
    published_at TEXT,
    updated_at TEXT,
    url TEXT NOT NULL,
    media_kind TEXT NOT NULL,
    raw_payload TEXT NOT NULL,
    PRIMARY KEY(capture_id, remote_id)
);

CREATE INDEX idx_remote_capture_time
ON remote_captures(provider, channel_id, collected_at);

CREATE INDEX idx_remote_inventory_id
ON remote_inventory_items(remote_id);
