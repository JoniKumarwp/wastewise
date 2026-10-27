"""Download pinned, public model files without an API key. Existing valid files are reused."""
from pathlib import Path
import hashlib
import json
import sys
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from wastewise.config import MODEL_ID, MODEL_REVISION, MODEL_PATH

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        while chunk:=f.read(1024*1024):
            h.update(chunk)
    return h.hexdigest()

def download(url, destination, expected_sha=None):
    destination=Path(destination)
    if destination.is_file() and (not expected_sha or digest(destination)==expected_sha):
        print(f"Available: {destination.name}",flush=True)
        return
    destination.parent.mkdir(parents=True,exist_ok=True)
    partial=destination.with_name(destination.name+".part")
    req=urllib.request.Request(url,headers={"User-Agent":"WasteWise/1.0 educational-research"})
    try:
        with urllib.request.urlopen(req,timeout=120) as r, partial.open("wb") as f:
            total=int(r.headers.get("Content-Length",0));received=0;last=0
            while chunk:=r.read(1024*1024):
                f.write(chunk);received+=len(chunk)
                if received-last>=25*1024*1024:
                    print(f"{destination.name}: {received//1048576} MB"+(f" / {total//1048576} MB" if total else ""),flush=True)
                    last=received
        if expected_sha and digest(partial)!=expected_sha:
            raise ValueError(f"Checksum mismatch: {destination.name}. The partial file was not installed.")
        partial.replace(destination)
    except Exception:
        partial.unlink(missing_ok=True)
        raise

def main():
    manifest=json.loads((ROOT/"models"/"download_manifest.json").read_text())
    for file in manifest["files"]:
        url=f'https://huggingface.co/{MODEL_ID}/resolve/{MODEL_REVISION}/{file["name"]}'
        download(url,MODEL_PATH/file["name"],file["sha256"])
    print("Pretrained detector is ready.")

if __name__=="__main__":
    main()
