"""Create an isolated local environment and launch; no administrator privileges needed."""
import argparse
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import venv
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parent

def run(args):
    subprocess.run([str(x) for x in args],cwd=ROOT,check=True)

def assemble_bundled_model(root=ROOT):
    """Reassemble byte-identical weights from locally available split files."""
    destination=root/"models/owlv2/model.safetensors"
    if destination.exists():
        return
    parts=[destination.with_name(destination.name+f".{i:03d}") for i in (1,2)]
    if not all(p.exists() for p in parts):
        return
    manifest=json.loads((root/"models/download_manifest.json").read_text())
    expected=next(x["sha256"] for x in manifest["files"] if x["name"]=="model.safetensors")
    temporary=destination.with_name(destination.name+".assembling")
    h=hashlib.sha256()
    print("Joining the local model files and checking their checksum…",flush=True)
    try:
        with temporary.open("wb") as output:
            for p in parts:
                with p.open("rb") as source:
                    while chunk:=source.read(1024*1024):
                        output.write(chunk);h.update(chunk)
        if h.hexdigest()!=expected:
            raise ValueError("The model parts do not match. Restore the split files or run scripts/download_model.py.")
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--install-only",action="store_true")
    args=parser.parse_args()
    if not ((3,11)<=sys.version_info[:2]<=(3,13)):
        raise SystemExit("Please install 64-bit Python 3.11, 3.12 or 3.13. Python 3.11 or 3.12 is recommended.")
    env=ROOT/".venv"
    python=env/("Scripts/python.exe" if os.name=="nt" else "bin/python")
    if not python.exists():
        print("Creating your local Python environment…",flush=True)
        venv.EnvBuilder(with_pip=True).create(env)
    marker=env/"wastewise-installed.txt"
    expected=(ROOT/"requirements.txt").read_text()+"torch==2.9.0 torchvision==0.24.0"
    if not marker.exists() or marker.read_text()!=expected:
        print("Installing dependencies. Internet is required for this first setup.",flush=True)
        run([python,"-m","pip","install","--upgrade","pip"])
        if sys.platform=="darwin":
            run([python,"-m","pip","install","torch==2.9.0","torchvision==0.24.0"])
        else:
            run([python,"-m","pip","install","torch==2.9.0","torchvision==0.24.0","--index-url","https://download.pytorch.org/whl/cpu"])
        run([python,"-m","pip","install","-r","requirements.txt"])
        marker.write_text(expected)
    if not (ROOT/"models/owlv2/model.safetensors").exists():
        assemble_bundled_model()
    if not (ROOT/"models/owlv2/model.safetensors").exists():
        run([python,"scripts/download_model.py"])
    run([python,"scripts/initialize.py"])
    if not args.install_only:
        print("Opening WasteWise at http://localhost:8501 . Keep this window open.",flush=True)
        run([python,"-m","streamlit","run","app.py"])

if __name__=="__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"A setup command failed ({exc.returncode}). Check your internet connection and read START_HERE.md.")
