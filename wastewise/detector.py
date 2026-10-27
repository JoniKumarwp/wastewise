"""Real pretrained inference. No image-specific or precomputed detections."""
import os
from pathlib import Path
import threading
import time
from .catalog import BY_KEY
from .config import MODEL_PATH, MODEL_REVISION
from .domain import Detection, clean_detections

class Owlv2Detector:
    def __init__(self, model_dir=MODEL_PATH, device="cpu"):
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        import torch
        from transformers import Owlv2Processor, Owlv2ForObjectDetection
        self.torch = torch
        if not (Path(model_dir)/"model.safetensors").is_file():
            raise FileNotFoundError("Model weights are missing. Run: python scripts/download_model.py")
        if device == "cuda" and not torch.cuda.is_available():
            raise ValueError("CUDA is not available. Choose CPU.")
        torch.set_num_threads(min(4, os.cpu_count() or 2))
        self.device = device
        self.processor = Owlv2Processor.from_pretrained(model_dir, local_files_only=True, use_fast=False)
        self.model = Owlv2ForObjectDetection.from_pretrained(model_dir, local_files_only=True).to(device).eval()
        self.model_id = f"OWLv2 / {MODEL_REVISION[:12]}"
        self.lock = threading.Lock()

    def predict(self, image, keys, threshold=0.18, nms_iou=0.45, detailed=False):
        if not keys:
            raise ValueError("Select at least one object class.")
        if any(k not in BY_KEY for k in keys):
            raise ValueError("An unsupported class was selected.")
        prompts = [[BY_KEY[k]["prompt"] for k in keys]]
        views = [(image, 0, 0)]
        if detailed:
            # Full image plus four overlapping crops. All boxes return to original coordinates.
            cw, ch = round(image.width*.62), round(image.height*.62)
            for x,y in [(0,0),(image.width-cw,0),(0,image.height-ch),(image.width-cw,image.height-ch)]:
                views.append((image.crop((x,y,x+cw,y+ch)), x, y))
        start = time.perf_counter()
        detections = []
        with self.lock, self.torch.inference_mode():
            for view, ox, oy in views:
                inputs = self.processor(text=prompts, images=view, return_tensors="pt").to(self.device)
                outputs = self.model(**inputs)
                target_sizes = self.torch.tensor([[view.height,view.width]], device=self.device)
                result = self.processor.post_process_grounded_object_detection(
                    outputs, threshold=threshold, target_sizes=target_sizes)[0]
                for label, score, box in zip(result["labels"],result["scores"],result["boxes"]):
                    x1,y1,x2,y2 = box.detach().cpu().tolist()
                    detections.append(Detection(keys[int(label)], float(score), [x1+ox,y1+oy,x2+ox,y2+oy]))
        detections = clean_detections(detections,image.width,image.height,threshold,nms_iou)
        return [d.to_dict() for d in detections], time.perf_counter()-start

class YoloDetector:
    """Optional detector for a locally trained Ultralytics model."""
    def __init__(self, weights, device="cpu"):
        from ultralytics import YOLO
        self.model = YOLO(str(weights))
        self.model_id = "Custom YOLO / " + Path(weights).name
        self.device = device
        self.lock = threading.Lock()

    def predict(self, image, keys=None, threshold=0.25, nms_iou=0.45, detailed=False):
        aliases = {"banana-peel":"banana_peel", "orange-peel":"orange_peel"}
        start = time.perf_counter()
        with self.lock:
            result = self.model.predict(image, conf=threshold, iou=nms_iou,
                device=self.device, imgsz=960 if detailed else 640, verbose=False)[0]
        ds = []
        for box in result.boxes:
            name = result.names[int(box.cls)]
            key = aliases.get(name, name.lower().strip().replace(" ", "_"))
            ds.append(Detection(key, float(box.conf), box.xyxy[0].tolist()))
        return [d.to_dict() for d in clean_detections(ds,image.width,image.height,threshold,nms_iou)], time.perf_counter()-start
