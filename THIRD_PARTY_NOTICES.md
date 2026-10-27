# Third-party attribution

## Default pretrained detector

- Publisher: Google; OWLv2 authors Matthias Minderer, Alexey Gritsenko,
  Neil Houlsby. Transformer implementation: Hugging Face contributors.
- Model: https://huggingface.co/google/owlv2-base-patch16-ensemble
- Revision: `cfd3195ba4ea9592eec887ded089f4c08eff231d`.
- License advertised by the original model card: **Apache-2.0**.
  The original model card and Apache license are in `models/owlv2/`. Model
  weights are downloaded from the pinned public revision during setup and are
  not tracked in this repository.
- Paper: https://arxiv.org/abs/2306.09683, *Scaling Open-Vocabulary Object Detection*.
- These pretrained weights are not represented as newly trained or validated
  waste-specific weights. Query/category mappings are authored by this application.

## Detection dataset

- Dataset: **GARBAGE CLASSIFICATION 3**, Material Identification, Roboflow.
- Original: https://universe.roboflow.com/material-identification/garbage-classification-3/dataset/2
- Public mirror: https://huggingface.co/datasets/keremberke/garbage-object-detection
- Mirror revision: `d8ad1490da2686d7af5c6a7f3d8844f0f9542b0f`.
- License stated in the source dataset card: **CC BY 4.0**.
  Source card and license are in `data/`.
- Credit the original dataset and the mirror when using it. The source card
  includes the original BibTeX citation. Existing source-image attribution and
  metadata are retained inside the unmodified COCO archives.
- Preparation converts boxes to YOLO format, skips invalid/crowd boxes,
  groups by original filename prefix, and stratifies approximately 70/15/15 by
  dominant class. Changes and upstream split provenance are recorded.
- Six broad classes are retained. No automatic fine-grained organic labels
  are inferred as ground truth.

## Optional example photographs

Example photographs are not distributed in this repository. Local images in
`assets/examples/` are excluded from Git; only use images you have permission
to use and distribute.

## Fonts and dependencies

- DejaVu Sans: upstream copyright/license is in `assets/DejaVu_LICENSE.txt`.
- PyTorch/torchvision: BSD-style licenses; https://pytorch.org/.
- Transformers: Apache-2.0; https://github.com/huggingface/transformers.
- Streamlit: Apache-2.0; https://github.com/streamlit/streamlit.
- Optional Ultralytics training/inference: AGPL-3.0 or an applicable enterprise
  license; https://github.com/ultralytics/ultralytics.
  This dependency is optional and is not bundled as application source.
- Remaining installed dependencies retain their own package licenses.

## Recovery content

Conditional recommendations are original application wording informed by
the linked EPA and university extension guidance. Craft ideas are authored
suggestions and require inspection; those sources are not represented as
certifying a particular craft design. Local collection rules must be checked.
