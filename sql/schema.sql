-- ==========================================
-- ServiceMonitor: структура базы данных
-- ==========================================
-- Таблицы предметной области:
--   groups   - группы сервисов;
--   services - сервисы (основная сущность);
--   checks   - результаты проверок сервисов.
--
-- Связи:
--   services.group_id -> groups.id   (N:1);
--   checks.service_id -> services.id (N:1).

CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    url TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    group_id INTEGER,
    FOREIGN KEY (group_id) REFERENCES groups(id)
);

CREATE TABLE IF NOT EXISTS checks (
    id INTEGER PRIMARY KEY,
    service_id INTEGER NOT NULL,
    available INTEGER NOT NULL,
    code INTEGER NOT NULL,
    checked_at TEXT NOT NULL,
    FOREIGN KEY (service_id) REFERENCES services(id)
);
