from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ.get("WASTEWISE_DATA_DIR", str(ROOT / "runtime"))).resolve()
DB_PATH = RUNTIME / "wastewise.sqlite3"
MODEL_PATH = ROOT / "models" / "owlv2"
MODEL_ID = "google/owlv2-base-patch16-ensemble"
MODEL_REVISION = "cfd3195ba4ea9592eec887ded089f4c08eff231d"
DATASET_ID = "keremberke/garbage-object-detection"
DATASET_REVISION = "d8ad1490da2686d7af5c6a7f3d8844f0f9542b0f"
COLORS = {"Organic": "#16834b", "Inorganic": "#2563eb", "Needs review": "#d97706"}
MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_PIXELS = 24_000_000
