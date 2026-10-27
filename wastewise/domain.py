from dataclasses import asdict, dataclass
import math
from .catalog import lookup

@dataclass
class Detection:
    key: str
    score: float
    box: list[float]

    def to_dict(self):
        info = lookup(self.key)
        return {**asdict(self), "name": info["name"], "category": info["category"],
                "handling": info["handling"], "needs_review": True}

def iou(a, b):
    intersection = max(0, min(a[2], b[2])-max(a[0], b[0])) * max(0, min(a[3], b[3])-max(a[1], b[1]))
    area_a = max(0, a[2]-a[0]) * max(0, a[3]-a[1])
    area_b = max(0, b[2]-b[0]) * max(0, b[3]-b[1])
    return intersection / max(area_a + area_b - intersection, 1e-9)

def clean_detections(detections, width, height, threshold=0.18, nms_iou=0.45, max_objects=80):
    """Clamp coordinates and remove near-duplicate proposals across class labels."""
    valid = []
    for d in detections:
        if len(d.box) != 4 or not all(math.isfinite(float(v)) for v in [d.score, *d.box]):
            continue
        x1, y1, x2, y2 = d.box
        box = [max(0., min(float(width), x1)), max(0., min(float(height), y1)),
               max(0., min(float(width), x2)), max(0., min(float(height), y2))]
        if d.score < threshold or box[2]-box[0] < 3 or box[3]-box[1] < 3:
            continue
        valid.append(Detection(d.key, float(d.score), box))
    kept = []
    for d in sorted(valid, key=lambda x: x.score, reverse=True):
        if all(iou(d.box, k.box) <= nms_iou for k in kept):
            kept.append(d)
        if len(kept) >= max_objects:
            break
    return kept
