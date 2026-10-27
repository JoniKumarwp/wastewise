"""Public dataset download; no Kaggle/Roboflow account or token is required."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.download_model import download
from wastewise.config import DATASET_ID, DATASET_REVISION

def main():
    p=argparse.ArgumentParser();p.add_argument("--split",choices=["all","train","valid","test"],default="all");args=p.parse_args()
    manifest=json.loads((ROOT/"data"/"download_manifest.json").read_text())
    for item in manifest["files"]:
        if args.split!="all" and item["name"]!=args.split+".zip":
            continue
        url=f'https://huggingface.co/datasets/{DATASET_ID}/resolve/{DATASET_REVISION}/data/{item["name"]}'
        download(url,ROOT/"data"/"garbage"/item["name"],item["sha256"])
    print("Archives are available. Next: python scripts/prepare_dataset.py")

if __name__=="__main__":main()
