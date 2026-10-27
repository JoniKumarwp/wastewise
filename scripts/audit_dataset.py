"""Audit actual bytes, labels and upstream source-name groups across splits."""
import argparse
from collections import defaultdict, Counter
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PIL import Image

def audit(folder):
    exact=defaultdict(set);groups=defaultdict(set);invalid=[];counts={};class_counts={}
    for split in ["train","valid","test"]:
        images=sorted((folder/split/"images").glob("*"));counts[split]=len(images);classes=Counter()
        for p in images:
            data=p.read_bytes();exact[hashlib.sha256(data).hexdigest()].add(split)
            groups[p.stem.split(".rf.")[0]].add(split)
            try:
                with Image.open(p) as im:im.verify()
            except Exception:invalid.append(str(p));continue
            label=folder/split/"labels"/(p.stem+".txt")
            if not label.exists():invalid.append(str(label));continue
            for line in label.read_text().splitlines():
                parts=line.split()
                try:
                    c=int(parts[0]);v=list(map(float,parts[1:]))
                    import math
                    if c not in range(6) or len(v)!=4 or not all(math.isfinite(x) and 0<=x<=1 for x in v) or min(v[2:])<=0:raise ValueError()
                    classes[c]+=1
                except Exception:invalid.append(str(label)+": "+line)
        class_counts[split]=dict(classes)
    result=dict(images=counts,boxes_by_class=class_counts,invalid_files_or_labels=invalid,
        cross_split_exact_duplicate_groups=sum(len(s)>1 for s in exact.values()),
        cross_split_source_name_groups=sum(len(s)>1 for s in groups.values()),
        source_group_check="Uses the filename before .rf.; this heuristic cannot establish capture-session independence or rule out other near-duplicates.")
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument("--dataset",type=Path,default=ROOT/"data"/"garbage"/"yolo");a=p.parse_args()
    if not (a.dataset/"data.yaml").is_file():raise SystemExit("Run scripts/prepare_dataset.py first.")
    result=audit(a.dataset);out=ROOT/"data"/"audit_report.json";out.write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    if result["invalid_files_or_labels"]:raise SystemExit(1)

if __name__=="__main__":main()
