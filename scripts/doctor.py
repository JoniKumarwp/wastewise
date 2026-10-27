"""Report missing dependencies, artifacts and device availability."""
from pathlib import Path
import importlib.util
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

def main():
    print("Python:",sys.version.split()[0]);missing=[]
    for name in ["torch","torchvision","transformers","streamlit","PIL","yaml"]:
        present=importlib.util.find_spec(name) is not None
        print(name, "OK" if present else "MISSING")
        if not present:missing.append(name)
    if "torch" not in missing:
        import torch
        print("CUDA available:",torch.cuda.is_available())
    for file in ["models/owlv2/model.safetensors","models/owlv2/config.json","data/garbage/train.zip","data/garbage/valid.zip","data/garbage/test.zip"]:
        p=ROOT/file;print(file,"OK" if p.exists() else "MISSING")
    if missing:raise SystemExit(1)

if __name__=="__main__":main()
