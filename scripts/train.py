"""Fine-tune a separate YOLO detector on broad material classes."""
import argparse
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

def main():
    p=argparse.ArgumentParser();p.add_argument("--data",type=Path,default=ROOT/"data/garbage/yolo/data.yaml")
    p.add_argument("--model",default="yolov8n.pt");p.add_argument("--epochs",type=int,default=50)
    p.add_argument("--batch",type=int,default=8);p.add_argument("--device",default="cpu");p.add_argument("--imgsz",type=int,default=640)
    p.add_argument("--output",type=Path,default=ROOT/"models/custom/best.pt")
    a=p.parse_args()
    if not a.data.is_file():raise SystemExit("Run scripts/prepare_dataset.py first.")
    from ultralytics import YOLO
    m=YOLO(a.model)
    m.train(data=str(a.data.resolve()),epochs=a.epochs,batch=a.batch,device=a.device,imgsz=a.imgsz,
        project=str(ROOT/"runs"),name="wastewise_train",seed=234,workers=0,patience=15)
    source=Path(m.trainer.best)
    destination=a.output;destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,destination)
    print("Saved trained weights:",destination)

if __name__=="__main__":main()
