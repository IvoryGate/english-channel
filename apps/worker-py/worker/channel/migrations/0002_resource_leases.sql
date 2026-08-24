CREATE TABLE resource_leases (
    lease_id TEXT PRIMARY KEY,
    resource_id TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    owner_pid INTEGER NOT NULL,
    parent_pid INTEGER NOT NULL,
    label TEXT NOT NULL,
    intent_hash TEXT NOT NULL,
    priority INTEGER NOT NULL,
    acquired_at TEXT NOT NULL,
    heartbeat_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    released_at TEXT,
    release_reason TEXT
);

CREATE UNIQUE INDEX idx_resource_one_active
ON resource_leases(resource_id) WHERE released_at IS NULL;

CREATE INDEX idx_resource_lease_history
ON resource_leases(resource_id, acquired_at);

