# Verification record

Checks performed on the packaged implementation in Linux with Python 3.12.14,
Torch 2.9.0+cpu, torchvision 0.24.0+cpu, Transformers 4.57.1 and Streamlit 1.50.0.

## Completed

- Twelve automated behavior checks passed: image rejection, annotation,
  coordinate clipping, duplicate suppression, SQLite writes and backup,
  immutable predictions with separate corrections, empty scans, COCO box
  conversion, unsafe archive-path rejection and unmapped classes. Lossless model-part assembly and corrupted-part rejection were also checked.
- Streamlit AppTest exercised a real OWLv2 scan, ellipse rendering, correction
  submission, scan history and all navigation pages without app exceptions.
- Streamlit started and returned HTTP 200 with `ok` from its health endpoint.
- Actual offline inference ran on two local-only example photographs, using
  the downloaded pretrained Safetensors file. Those photographs and their
  qualitative results are not part of this source distribution.
- All three public dataset archives downloaded and were converted. Preparation
  skipped 17 invalid/crowd boxes. All 10,464 images and 74,073 retained labels
  passed the prepared-file/label audit.
- Prepared split counts: 7,326 training, 1,569 validation, 1,569 test images.
  All six classes occur in every split. Exact cross-split byte duplicate groups
  and source-filename group overlaps found by this audit: zero.
- Original upstream test labels contained no glass examples. Preparation
  therefore repartitions filename groups, stratified by dominant class, with
  seed 234. Original split provenance and the resulting assignment are retained.
- Optional YOLO training, checkpoint copying, evaluation and metric export were
  exercised for one epoch on a deliberately tiny six-image training fixture
  with a random-initialized model. This verifies the workflow only. Those test
  weights and their zero-valued metrics are not distributed as a usable model.
- Python source compilation, notebook code-cell parsing, artifact diagnostics,
  seeded SQLite integrity and download checksum reuse were checked.

## Limits and work still needed

The ready-to-run engine is general pretrained Google OWLv2, downloaded during
setup. It has not been fine-tuned on the waste dataset. No full-dataset training
or independent accuracy benchmark was completed for that engine.

Similar materials can be confused. Local images used for qualitative
development checks are not an untouched or reproducible final benchmark.

Filename-based grouping does not establish independence of capture sessions,
physical objects, near-duplicates or a pretrained model's training corpus.
Public annotation quality and class imbalance require further review. The
biodegradable dataset label does not give specific organic object identities.

Functional interface tests used Streamlit's test harness. A full browser visual
check could not run because this environment blocked browser process sockets.
Camera capture was not tested with a physical camera. CUDA, macOS and the
Windows launcher were not executed on those platforms here. Their supplied
setup paths still require testing on the user's computer.

The Colab notebook was syntax-checked; a hosted Colab GPU run was not performed.
The application binds locally and does not provide a deployed multi-user site.
