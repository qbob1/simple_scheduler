CREATE TABLE IF NOT EXISTS job (
    id INTEGER PRIMARY KEY NOT NULL,
    name TEXT,
    description TEXT,
    status TEXT,
    created_at DATETIME default (datetime('now','localtime')) NOT NULL,
    updated_at DATETIME default (datetime('now','localtime')) NOT NULL,
    source text NOT NULL,
    bytes BLOB,
    hash text,
    cron text
);

CREATE TABLE IF NOT EXISTS job_audit_log (
    id INTEGER PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES job(id),
    status TEXT,
    created_at DATETIME default (datetime('now','localtime')) NOT NULL
);

Create trigger if not exists update_active_jobs_update AFTER UPDATE on job begin INSERT INTO job_audit_log (job_id, status) VALUES (new.id, 'UPDATE'); end;
Create trigger if not exists update_active_jobs_insert AFTER INSERT on job begin INSERT INTO job_audit_log (job_id, status) VALUES (new.id, 'INSERT'); end;
Create trigger if not exists update_active_jobs_delete AFTER DELETE on job begin INSERT INTO job_audit_log (job_id, status) VALUES (old.id, 'DELETE'); end;

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY NOT NULL,
    job_id INTEGER REFERENCES job(id) NOT NULL,
    result TEXT,
    created_at DATETIME default (datetime('now','localtime')) NOT NULL,
    misc blob,
    status text
    );

