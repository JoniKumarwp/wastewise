"""SQLite persistence. Predictions remain immutable; corrections are separate feedback."""
from contextlib import closing
from contextlib import contextmanager
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
import csv
import json
import sqlite3
import uuid
from .config import DB_PATH, RUNTIME
from .catalog import CATALOG, lookup
from .imaging import png_bytes

SCHEMA = """
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
"""

@contextmanager
def connect(path=DB_PATH):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def init_db(path=DB_PATH):
    with connect(path) as con:
        con.executescript(SCHEMA)
        con.executemany("INSERT OR IGNORE INTO categories VALUES (?)", [(c,) for c in ["Organic","Inorganic","Needs review"]])
        for c in CATALOG:
            con.execute("INSERT INTO classes VALUES (?,?,?,?,?) ON CONFLICT(key) DO UPDATE SET name=excluded.name, category=excluded.category, prompt=excluded.prompt, handling=excluded.handling",
                (c["key"],c["name"],c["category"],c["prompt"],c["handling"]))
            con.execute("DELETE FROM recommendations WHERE class_key=?",(c["key"],))
            con.executemany("INSERT INTO recommendations(class_key,content_json) VALUES (?,?)",
                [(c["key"],json.dumps(r)) for r in c["recommendations"]])

def get_recommendations(key, path=DB_PATH):
    with connect(path) as con:
        return [json.loads(r[0]) for r in con.execute("SELECT content_json FROM recommendations WHERE class_key=? ORDER BY id",(key,))]

def save_scan(image, annotated, rows, source_name, model_id, elapsed, settings, path=DB_PATH, runtime=RUNTIME):
    sid = uuid.uuid4().hex
    folder = Path(runtime)/"scans"/sid
    folder.mkdir(parents=True, exist_ok=False)
    (folder/"original.png").write_bytes(png_bytes(image))
    (folder/"annotated.png").write_bytes(png_bytes(annotated))
    try:
        with connect(path) as con:
            con.execute("INSERT INTO scans VALUES (?,?,?,?,?,?,?,?,?,?)",(sid,datetime.now(timezone.utc).isoformat(),
                Path(source_name).name,model_id,float(elapsed),json.dumps(settings),
                str(Path("scans")/sid/"original.png"),str(Path("scans")/sid/"annotated.png"),image.width,image.height))
            for n,r in enumerate(rows,1):
                con.execute("INSERT INTO detections(scan_id,number,class_key,name,category,score,box_json) VALUES (?,?,?,?,?,?,?)",
                    (sid,n,r["key"],r["name"],r["category"],r["score"],json.dumps(r["box"])))
    except Exception:
        import shutil
        shutil.rmtree(folder)
        raise
    return sid

def list_scans(path=DB_PATH):
    with connect(path) as con:
        return [dict(r) for r in con.execute("SELECT s.*,count(d.id) object_count FROM scans s LEFT JOIN detections d ON d.scan_id=s.id GROUP BY s.id ORDER BY s.created_at DESC")]

def scan_rows(sid, path=DB_PATH):
    with connect(path) as con:
        rows = []
        for r in con.execute("SELECT * FROM detections WHERE scan_id=? ORDER BY number",(sid,)):
            r=dict(r);r["key"]=r.pop("class_key");r["box"]=json.loads(r.pop("box_json"));r["needs_review"]=True
            r["handling"]=lookup(r["key"])["handling"];rows.append(r)
        return rows

def add_feedback(detection_id, corrected_key, comment, path=DB_PATH):
    if corrected_key != "false_positive" and corrected_key not in {c["key"] for c in CATALOG}:
        raise ValueError("Choose a known class or mark a false positive.")
    with connect(path) as con:
        con.execute("INSERT INTO feedback(detection_id,corrected_key,comment,created_at) VALUES (?,?,?,?)",
            (detection_id,corrected_key,comment.strip(),datetime.now(timezone.utc).isoformat()))

def export_feedback(path=DB_PATH):
    with connect(path) as con:
        return [dict(r) for r in con.execute("SELECT f.*,d.scan_id,d.number,d.class_key predicted_class,d.box_json FROM feedback f JOIN detections d ON f.detection_id=d.id ORDER BY f.id")]

def csv_bytes(rows):
    if not rows:
        return b"number,name,category,score,x1,y1,x2,y2\n"
    output=StringIO(newline="")
    fields=["number","name","category","score","x1","y1","x2","y2"]
    writer=csv.DictWriter(output,fieldnames=fields);writer.writeheader()
    for n,r in enumerate(rows,1):
        writer.writerow(dict(number=n,name=r["name"],category=r["category"],score=round(r["score"],5),**dict(zip(fields[4:],r["box"]))))
    return output.getvalue().encode("utf-8-sig")

def database_bytes(path=DB_PATH):
    """Create a consistent SQLite backup and close it before cleanup."""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        backup = Path(td) / "backup.sqlite3"

        with connect(path) as src:
            with closing(sqlite3.connect(backup)) as dst:
                src.backup(dst)

        return backup.read_bytes()