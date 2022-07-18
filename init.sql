CREATE TABLE IF NOT EXISTS job (
    id INTEGER PRIMARY KEY NOT NULL,
    name TEXT,
    description TEXT,
    status TEXT,
    created_at DATETIME default current_timestamp NOT NULL,
    updated_at DATETIME default current_timestamp NOT NULL,
    source text,
    bytes BLOB,
    hash text,
    cron text
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY NOT NULL,
    job_id INTEGER REFERENCES job(id) NOT NULL,
    result TEXT,
    created_at DATETIME default current_timestamp NOT NULL, 
    misc blob, status text);

CREATE TRIGGER job_insert_trigger after insert on job begin select update_active_jobs(new.Id, 'INSERT') as 'update'; end;
CREATE TRIGGER job_update_trigger after update on job begin select update_active_jobs(new.Id, 'UPDATE') as 'update'; end;
CREATE TRIGGER job_delete_trigger after delete on job begin select update_active_jobs(old.Id, 'DELETE') as 'update'; end;