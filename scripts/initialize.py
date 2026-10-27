from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from wastewise.database import init_db
from wastewise.config import DB_PATH
if __name__=="__main__":
    init_db();print("Local category, recommendation and history database is ready:",DB_PATH)
