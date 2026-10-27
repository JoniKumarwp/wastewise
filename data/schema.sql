
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS categories(name TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS classes(key TEXT PRIMARY KEY, name TEXT NOT NULL,
    category TEXT NOT NULL REFERENCES categories(name), prompt TEXT NOT NULL, handling TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS recommendations(id INTEGER PRIMARY KEY, class_key TEXT NOT NULL REFERENCES classes(key),
    content_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS scans(id TEXT PRIMARY KEY, created_at TEXT NOT NULL, source_name TEXT NOT NULL,
    model_id TEXT NOT NULL, elapsed_seconds REAL NOT NULL, settings_json TEXT NOT NULL, image_path TEXT NOT NULL,
    annotated_path TEXT NOT NULL, width INTEGER NOT NULL, height INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS detections(id INTEGER PRIMARY KEY, scan_id TEXT NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    number INTEGER NOT NULL, class_key TEXT NOT NULL, name TEXT NOT NULL, category TEXT NOT NULL, score REAL NOT NULL,
    box_json TEXT NOT NULL, UNIQUE(scan_id,number));
CREATE TABLE IF NOT EXISTS feedback(id INTEGER PRIMARY KEY, detection_id INTEGER NOT NULL REFERENCES detections(id) ON DELETE CASCADE,
    corrected_key TEXT, comment TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS scan_detection_index ON detections(scan_id);
