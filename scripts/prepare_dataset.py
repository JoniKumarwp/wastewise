"""Convert the supplied COCO archives to YOLO labels; do not execute dataset scripts."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile
import random
import shutil

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
NAMES=["biodegradable","cardboard","glass","metal","paper","plastic"]

def convert_box(bbox,width,height):
    if len(bbox)!=4 or width<=0 or height<=0:return None
    import math
    if not all(math.isfinite(float(x)) for x in bbox):return None
    x,y,w,h=map(float,bbox)
    if w<=0 or h<=0:return None
    x1,y1=max(0,x),max(0,y)
    x2,y2=min(width,x+w),min(height,y+h)
    if x2<=x1 or y2<=y1:return None
    return [(x1+x2)/(2*width),(y1+y2)/(2*height),(x2-x1)/width,(y2-y1)/height]

def safe_name(name):
    p=PurePosixPath(name.replace("\\","/"))
    if p.is_absolute() or ".." in p.parts or not p.name or any(":" in part for part in p.parts):
        raise ValueError("Unsafe archive filename")
    return p.name

def repartition(output):
    """Stratify groups by dominant object class, retaining upstream provenance.

    This improves coverage; filenames cannot prove that physical objects or
    capture sessions are independent. Near-duplicate review is still required.
    """
    groups=defaultdict(list)
    for split in ["train","valid","test"]:
        for image in sorted((output/split/"images").glob("*")):
            label=output/split/"labels"/(image.stem+".txt")
            counts=Counter(int(line.split()[0]) for line in label.read_text().splitlines() if line.strip())
            group=image.stem.split(".rf.")[0]
            groups[group].append(dict(image=image,label=label,upstream_split=split,counts=counts))
    strata=defaultdict(list)
    for group,records in groups.items():
        counts=Counter()
        for r in records:counts.update(r["counts"])
        primary=max(sorted(counts),key=counts.get) if counts else -1
        strata[primary].append(group)
    assignment={}
    for cls,gids in sorted(strata.items()):
        gids=sorted(gids);random.Random(234+cls).shuffle(gids)
        n=len(gids);nv=max(1,round(n*.15)) if n>=3 else 0;nt=nv
        for i,gid in enumerate(gids):
            assignment[gid]="valid" if i<nv else "test" if i<nv+nt else "train"
    staging=output/"_repartition"
    if staging.exists():raise ValueError("Remove the incomplete _repartition folder before preparing again.")
    staging.mkdir();manifest=[];used=set()
    for group,records in groups.items():
        for r in records:
            image=r["image"];label=r["label"]
            if image.name in used:raise ValueError("Duplicate filenames require manual dataset review.")
            used.add(image.name)
            shutil.move(str(image),str(staging/image.name));shutil.move(str(label),str(staging/label.name))
            manifest.append(dict(file=image.name,source_group=group,upstream_split=r["upstream_split"],split=assignment[group]))
    for row in manifest:
        imdir=output/row["split"]/"images";ldir=output/row["split"]/"labels"
        imdir.mkdir(parents=True,exist_ok=True);ldir.mkdir(parents=True,exist_ok=True)
        name=row["file"];label=Path(name).stem+".txt"
        shutil.move(str(staging/name),str(imdir/name));shutil.move(str(staging/label),str(ldir/label))
    staging.rmdir()
    (output/"split_manifest.json").write_text(json.dumps(manifest,indent=2))
    summaries=[]
    for split in ["train","valid","test"]:
        counts=Counter();images=list((output/split/"images").glob("*"))
        for image in images:
            for line in (output/split/"labels"/(image.stem+".txt")).read_text().splitlines():
                if line.strip():counts[NAMES[int(line.split()[0])]]+=1
        summaries.append(dict(split=split,images=len(images),boxes=sum(counts.values()),classes=dict(counts)))
    return summaries

def prepare(archives,output):
    output=Path(output);summary=[]
    if (output/"split_manifest.json").exists():
        print("Dataset already prepared. Existing audited split is kept; choose a new --output directory to regenerate.")
        return json.loads((ROOT/"data"/"dataset_report.json").read_text())
    for split in ["train","valid","test"]:
        archive=Path(archives)/(split+".zip")
        if not archive.exists():raise FileNotFoundError(f"Missing {archive}. Run scripts/download_dataset.py first.")
        with zipfile.ZipFile(archive) as z:
            if sum(i.file_size for i in z.infolist())>3_000_000_000:
                raise ValueError("Dataset archive is unexpectedly large.")
            anns=[n for n in z.namelist() if n.endswith("_annotations.coco.json")]
            if len(anns)!=1:raise ValueError("Expected one COCO annotation file per split")
            coco=json.loads(z.read(anns[0]));category={c["id"]:c["name"] for c in coco["categories"]}
            if not set(category.values()).issubset(NAMES):raise ValueError("Unexpected dataset class names")
            by_image=defaultdict(list)
            for a in coco["annotations"]:by_image[a["image_id"]].append(a)
            members={safe_name(n):n for n in z.namelist() if not n.endswith("/")}
            counts=Counter();skipped=0;boxes=0
            for image in coco["images"]:
                filename=safe_name(image["file_name"])
                if filename not in members:raise FileNotFoundError(filename)
                imdir=output/split/"images";labeldir=output/split/"labels"
                imdir.mkdir(parents=True,exist_ok=True);labeldir.mkdir(parents=True,exist_ok=True)
                (imdir/filename).write_bytes(z.read(members[filename]))
                lines=[]
                for a in by_image[image["id"]]:
                    b=convert_box(a["bbox"],image["width"],image["height"])
                    if b is None or a.get("iscrowd",0):skipped+=1;continue
                    name=category[a["category_id"]];idx=NAMES.index(name)
                    lines.append(str(idx)+" "+" ".join(f"{x:.8f}" for x in b));counts[name]+=1;boxes+=1
                (labeldir/(Path(filename).stem+".txt")).write_text("\n".join(lines)+("\n" if lines else ""))
            summary.append(dict(split=split,images=len(coco["images"]),boxes=boxes,skipped_boxes=skipped,classes=dict(counts)))
            print(f"Prepared {split}: {len(coco['images'])} images, {boxes} boxes; skipped {skipped}",flush=True)
    original=summary
    summary=repartition(output)
    import yaml
    (output/"data.yaml").write_text(yaml.safe_dump(dict(path=str(output.resolve()),train="train/images",val="valid/images",test="test/images",names=dict(enumerate(NAMES))),sort_keys=False))
    report={"splits":summary,"upstream_splits":original,"seed":234,
        "note":"Split by filename source groups, stratified by dominant class (approximately 70/15/15). Original split provenance is in split_manifest.json. Review near-duplicates and capture sessions before research use."}
    (ROOT/"data"/"dataset_report.json").write_text(json.dumps(report,indent=2))
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument("--archives",type=Path,default=ROOT/"data"/"garbage");p.add_argument("--output",type=Path,default=ROOT/"data"/"garbage"/"yolo");a=p.parse_args()
    prepare(a.archives,a.output)

if __name__=="__main__":main()
