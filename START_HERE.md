# Start WasteWise

WasteWise identifies candidate waste objects, draws labels around them, maps
them into household Organic/Inorganic streams, and retrieves conditional
reuse, recycling, composting or regrowing guidance.

## Windows: the easiest start

1. Install **64-bit Python 3.11 or 3.12** from https://www.python.org/downloads/.
   Enable **Add Python to PATH** during installation.
2. Download or clone the WasteWise repository into a folder such as
   `C:\WasteWise`. Do not launch from inside a ZIP viewer.
3. Open the extracted `wastewise` folder and double-click **START_WINDOWS.bat**.
4. The first start creates `.venv` and installs Python packages. Keep the
   terminal open. Internet is needed for dependency installation.
5. Open **http://localhost:8501** if the browser does not open automatically.
6. Upload your own image or take a camera snapshot, then press **Identify waste**.
   Select an object to see its guidance.

The GitHub source repository does not include large model weights, training
dataset archives, or optional example photographs. On first startup, the
launcher downloads the pinned model and verifies its SHA-256 checksum. You do
not need to train a model or download the dataset to try detection. Dataset
archives can be downloaded separately if you choose to train a YOLO model.
Optional local example photos appear in the app when placed in
`assets/examples/`; only use images you have permission to use.

If your launcher selects an unsupported Python version, open PowerShell in the
project folder and run `py -3.11 bootstrap.py` or `py -3.12 bootstrap.py`.
Python 3.13 is also supported by the dependency versions; 3.11/3.12 are recommended.

## What is included

- A Streamlit interface with uploads, camera snapshots and examples.
- Pretrained **Google OWLv2** inference with object-level boxes and labels.
- Rectangles or ellipses, Organic/Inorganic colors, and optional model scores.
- Object-specific conditional recovery guidance with source links.
- SQLite history, exported images, CSV/JSON, database backup, and corrections.
- **10,464** annotated detection images in downloadable COCO archives.
- Dataset conversion, checksums, grouped stratified splitting, audit, YOLO
  training/evaluation commands and a Colab notebook.
- An empty, seeded local SQLite database. It is ready to receive your scans.
- Real prediction exports from your reference photographs and a verification record.

## Important model scope

The ready-to-run detector is a **general pretrained open-vocabulary baseline**.
It has **not been fine-tuned on the supplied waste dataset**. Its selected text
queries include specific objects such as banana peel, eggshell and plastic
bottle. These are query targets, not independently verified supported classes
with guaranteed accuracy. Exact materials and obscured items may be confused.

The optional training dataset has six broader classes: biodegradable,
cardboard, glass, metal, paper and plastic. Training YOLO on that dataset alone
does not teach it specific organic names such as banana peel or eggshell.
To establish that capability, collect and annotate the desired finer classes.

Match scores are not calibrated accuracy. No claimed overall accuracy is
included. Check `docs/VERIFICATION.md` for what was actually tested.

## Routine use

- **Detect waste:** upload a photo or take a still camera snapshot, then run.
- **Detection settings:** adjust model-score threshold, query classes,
  duplicate-box suppression, shape, CPU/CUDA and detailed scanning.
- **Detailed scan:** adds four overlapping crops for OWLv2. It takes longer
  and can add false positives; inspect the results.
- **Explore an object:** match its number to the label on the image.
- **Correct a prediction:** save the scan first, then submit a correction.
  Corrections do not automatically retrain the model or replace original predictions.
- **Scan history:** revisit results and export the SQLite database or corrections.
- **Recovery guide:** browse the object catalogue without running a detector.

Green indicates Organic and blue indicates Inorganic. An unmapped custom-model
class is amber and needs review. All model predictions remain unverified until
you inspect them. Paper/cardboard are assigned to the Inorganic dry-recyclables
stream in this project's sorting convention, although they are plant-derived.
Battery/electronics handling is shown separately from the two broad streams.

## Database versus dataset versus model

| File or folder | Meaning |
|---|---|
| `runtime/wastewise.sqlite3` | Categories, guidance, scan history and corrections |
| `runtime/scans/` | Your saved original and annotated images |
| `models/owlv2/` | Model metadata and processor/tokenizer files; weights download on setup |
| `data/garbage/*.zip` | Downloaded annotated image archives for optional training |
| `data/garbage/yolo/` | YOLO dataset generated when you run preparation |
| `reports/reference_tests/` | Local qualitative checks; not ground truth or a benchmark |

The application database cannot recognize images by itself. The detector
uses its model weights. Downloading more training images does not update it.

Keep the **whole runtime folder** when moving scan history to another computer.
Image paths are relative to that folder. A SQLite export alone contains the
records, not the image bytes. Set `WASTEWISE_DATA_DIR` before startup if you
want your runtime stored elsewhere.

## macOS/Linux

```bash
cd wastewise
bash START_MAC_LINUX.sh
```

Allow roughly 6 GB free disk space for installation and unpacking; leave more
space for training runs. **8 GB RAM or more is recommended** for local OWLv2
use. CPU is supported; inference speed depends on your hardware. There is no
paid AI API key or cloud inference requirement for the default detector.
After packages and weights are present, inference can run offline.

## Manual installation

Run inside the project folder. On Windows, `python` can be replaced with `py -3.11`
for creation of the virtual environment.

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\python.exe -m pip install torch==2.9.0 torchvision==0.24.0 --index-url https://download.pytorch.org/whl/cpu
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe scripts\initialize.py
.venv\Scripts\python.exe -m streamlit run app.py
```

For Linux use `.venv/bin/python`. For macOS install the same Torch versions
from PyPI without the CPU index option. The bootstrap script handles these
platform differences automatically. To finish installation without launching,
run `python bootstrap.py --install-only`.

## Optional: prepare and train on the dataset

Use the virtual-environment Python for every command. Commands below use
`python` for brevity; activate `.venv` or substitute its executable path.

```bash
python scripts/download_dataset.py
python scripts/prepare_dataset.py
python scripts/audit_dataset.py
python -m pip install -r requirements-training.txt
python scripts/train.py --epochs 50 --batch 8 --device cpu
python scripts/evaluate.py --weights models/custom/best.pt --device cpu
```

Downloading reuses archives with matching checksums. Preparation checks annotations, skips invalid boxes,
creates a source-filename grouped split stratified by dominant class, and writes
a machine-specific `data.yaml`. It records upstream split provenance.
The original upstream test split has no glass labels, so it is not used unchanged.
The prepared split includes all six classes in every partition.
Filename grouping does not rule out visually similar photographs or repeated
physical objects; inspect the data before making research claims.

CPU training on the full dataset can be very slow. For GPU training use
`notebooks/Train_in_Colab.ipynb`; request a Colab GPU and install the appropriate
CUDA-enabled PyTorch version. CUDA is optional and may not be available on a
free Colab session. The initial YOLO base weights download automatically.

After training, choose **Custom YOLO** in the application and select your own
`models/custom/best.pt` path. This optional model uses its own label names.
Restart the app after overwriting a weight file that has already been loaded.
Only load `.pt` weights you created or trust; the default uses downloaded Safetensors.

## Troubleshooting

- **Window closes immediately:** open PowerShell in the folder and run
  `py -3.11 bootstrap.py` so you can read the error.
- **`ModuleNotFoundError`:** use the `.venv` Python, or rerun the launcher.
- **Missing model:** run `python scripts/download_model.py` with internet access.
  Model/processor downloads are pinned and checksum checked.
- **No detections:** try a clearer photo, choose the relevant query classes,
  or lower the score threshold a little. No detections does not establish that
  the image contains no waste.
- **Wrong labels or extra boxes:** record corrections; try a higher threshold
  or different duplicate-box overlap. Fine-tune and evaluate a model for your
  intended capture conditions before relying on its outputs.
- **Out of memory:** choose CPU, disable detailed scan, close other large apps,
  and use a machine with more available RAM.
- **Port 8501 in use:** run `python -m streamlit run app.py --server.port 8502`
  and open http://localhost:8502.
- **Camera unavailable:** allow camera permission in the browser or use Upload.
  Camera mode captures a snapshot; it is not live video processing.
- **CUDA unavailable:** keep CPU selected unless you installed compatible
  CUDA-enabled Torch and have a supported NVIDIA GPU.
- **Diagnostics:** run `python scripts/doctor.py`.

Composting, regrowing and reuse suggestions require confirmation of item type,
condition and local handling rules. The app cannot verify these from a photo.
