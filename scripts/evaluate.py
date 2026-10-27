"""Evaluate actual detector weights on held-out YOLO test data; never invent metrics."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

def main():
    p=argparse.ArgumentParser();p.add_argument("--weights",type=Path,required=True)
    p.add_argument("--data",type=Path,default=ROOT/"data/garbage/yolo/data.yaml");p.add_argument("--device",default="cpu")
    p.add_argument("--output",type=Path,default=ROOT/"reports")
    a=p.parse_args()
    if not a.weights.is_file():raise SystemExit("The supplied trained weights do not exist.")
    from ultralytics import YOLO
    metrics=YOLO(str(a.weights)).val(data=str(a.data.resolve()),split="test",device=a.device,workers=0,
        project=str(ROOT/"runs"),name="wastewise_test",plots=True)
    report={"weights":str(a.weights),"data":str(a.data),"split":"test","metrics":metrics.results_dict,
            "note":"This run measures this detector on this dataset split. Assess duplicate and pretraining overlap before making generalization claims."}
    output=a.output;output.mkdir(parents=True,exist_ok=True)
    (output/"test_metrics.json").write_text(json.dumps(report,indent=2,default=float))
    print(json.dumps(report,indent=2,default=float))

if __name__=="__main__":main()
