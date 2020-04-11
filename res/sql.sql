CREATE TABLE `buckets` (
    `id`    INTEGER PRIMARY KEY AUTOINCREMENT,
    `bucket`    TEXT NOT NULL UNIQUE,
    `host`  TEXT NOT NULL,
    `key`   TEXT NOT NULL,
    `secret`    TEXT NOT NULL
);