# WasteWise

A downloadable local application for waste object detection, two-stream
household sorting, and conditional material-recovery guidance.

**Start with [START_HERE.md](START_HERE.md).** On Windows install 64-bit
Python 3.11/3.12, extract the folder, and run `START_WINDOWS.bat`.

The default engine is pretrained Google OWLv2. The supplied six-class waste
dataset is for optional training of a separate YOLO detector. These are
different artifacts; no waste-specific OWLv2 fine-tuning or universal accuracy
claim is made. Real packaging checks are recorded in `docs/VERIFICATION.md`.

## Components

- `app.py`: Streamlit interface.
- `wastewise/detector.py`: OWLv2 and optional YOLO inference.
- `wastewise/domain.py`: coordinate filtering and duplicate suppression.
- `wastewise/imaging.py`: validated image loading and labeled overlays.
- `wastewise/catalog.py`: object taxonomy and conditional authored guidance.
- `wastewise/database.py`: SQLite history, recommendations and feedback.
- `scripts/`: reproducible download, prepare, audit, training and evaluation workflows.
- `notebooks/`: Colab training guide.
- `tests/`: behavior checks for persistence, image handling and dataset conversion.

## CLI prediction

```bash
python scripts/predict.py path/to/your_image.jpg
```

Outputs include a labeled PNG and CSV/JSON with original-image pixel coordinates.

## Development

Install the CPU Torch pair from `START_HERE.md`, then:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Application source is MIT licensed. Downloaded models and datasets, and
bundled fonts, retain
their separate terms; see `THIRD_PARTY_NOTICES.md`. Large model weights and
training archives are downloaded on demand and are not tracked in this
repository. Optional local example photos are also excluded.
