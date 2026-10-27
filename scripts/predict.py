"""Predict on any local photograph without opening the browser interface."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from wastewise.catalog import DEFAULT_KEYS
from wastewise.detector import Owlv2Detector
from wastewise.imaging import load_image,annotate
from wastewise.database import csv_bytes

def main():
    p=argparse.ArgumentParser();p.add_argument("image",type=Path);p.add_argument("--output",type=Path,default=ROOT/"reports/predictions")
    p.add_argument("--threshold",type=float,default=.20);p.add_argument("--detailed",action="store_true");p.add_argument("--device",default="cpu")
    a=p.parse_args();im=load_image(a.image.read_bytes());detector=Owlv2Detector(device=a.device)
    rows,elapsed=detector.predict(im,DEFAULT_KEYS,a.threshold,detailed=a.detailed)
    a.output.mkdir(parents=True,exist_ok=True);stem=a.image.stem
    annotate(im,rows).save(a.output/(stem+"_labeled.png"))
    (a.output/(stem+".csv")).write_bytes(csv_bytes(rows))
    (a.output/(stem+".json")).write_text(json.dumps(dict(model=detector.model_id,seconds=elapsed,detections=rows),indent=2))
    print(f"{len(rows)} detections in {elapsed:.1f} seconds. Outputs: {a.output}")

if __name__=="__main__":main()
