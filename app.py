from __future__ import annotations
import hashlib
import html
import json
from pathlib import Path
import streamlit as st
from PIL import Image
from wastewise import __version__
from wastewise.catalog import CATALOG, BY_KEY, DEFAULT_KEYS
from wastewise.config import ROOT, MODEL_PATH, DB_PATH, RUNTIME
from wastewise.database import (init_db, get_recommendations, save_scan, list_scans,
    scan_rows, add_feedback, csv_bytes, database_bytes, export_feedback)
from wastewise.imaging import load_image, annotate, png_bytes

st.set_page_config(page_title="ReUseWaste · See waste differently", page_icon="♻️", layout="wide")
st.markdown("""<style>
.stApp {background:#f6f8f5;color:#173b2b}
.block-container {padding-top:2rem;max-width:1450px}
[data-testid="stSidebar"] {background:#e8efe7}
h1,h2,h3 {letter-spacing:-.035em;color:#153e2d}
.eyebrow {font-size:.73rem;letter-spacing:.17em;font-weight:700;color:#437457;margin-bottom:12px}
.hero {background:linear-gradient(120deg,#143f2c,#2d6347);padding:30px 34px;border-radius:20px;margin:8px 0 25px;color:#fff}
.hero h1 {color:#fff;font-size:2.8rem;line-height:1.13;margin:0 0 10px}
.hero p {color:#dceadd;max-width:780px;font-size:1.04rem;margin:0}
.pill {display:inline-block;border-radius:30px;padding:4px 12px;font-size:.8rem;font-weight:600;background:#e2eee5;color:#235c3b;margin:0 5px 8px 0}
.fine {font-size:.83rem;color:#5f7467;line-height:1.5}
[data-testid="stMetric"] {background:white;border:1px solid #dfe7df;border-radius:13px;padding:15px}
div.stButton > button[kind="primary"] {background:#1d6140;border-color:#1d6140;border-radius:10px}
[data-testid="stExpander"] {background:#fff;border-radius:12px}
</style>""", unsafe_allow_html=True)

@st.cache_resource
def initialize():
    init_db()
    return True

@st.cache_resource(show_spinner="Loading the local detector…")
def get_detector(engine, device, weights=""):
    from wastewise.detector import Owlv2Detector, YoloDetector
    return Owlv2Detector(device=device) if engine == "Pretrained OWLv2" else YoloDetector(weights,device)

initialize()
ready = (MODEL_PATH/"model.safetensors").is_file()
with st.sidebar:
    st.markdown("## ♻ ReUseWaste")
    st.caption("See it. Sort it. Give it another life.")
    page = st.radio("Workspace", ["Detect waste","Scan history","Recovery guide","Dataset & training","About the model"], label_visibility="collapsed")
    st.divider()
    st.markdown("**Your local workspace**")
    st.caption("Images are processed on your computer. Scans stay local unless you choose to export or share them.")
    st.success("Pretrained weights available" if ready else "Model download required")
    st.caption(f"Version {__version__} · CPU supported")

def guidance(key):
    recs=get_recommendations(key)
    if not recs:
        st.info("This class needs identification and handling review. No automatic recommendation is available.")
    for rec in recs:
        st.markdown(f'**{rec["action"]} · {rec["title"]}**')
        st.caption("Applies when: " + rec["conditions"])
        for n,step in enumerate(rec["steps"],1):
            st.write(f"{n}. {step}")
        if rec["note"]:
            st.caption(rec["note"])
        st.link_button("Supporting guidance ↗",rec["source_url"])

def show_result(image, result, shape, show_score):
    rows=result["rows"]
    marked=annotate(image,rows,shape,show_score)
    a,b,c,d=st.columns(4)
    a.metric("Objects detected",len(rows))
    b.metric("Organic",sum(r["category"]=="Organic" for r in rows))
    c.metric("Inorganic",sum(r["category"]=="Inorganic" for r in rows))
    d.metric("Inference",f'{result["elapsed"]:.1f} s')
    left,right=st.columns([1.65,1],gap="large")
    with left:
        st.image(marked,width="stretch",caption="Green: organic · Blue: inorganic · Amber: unmapped class. Every label is a model prediction.")
        x,y,z=st.columns(3)
        x.download_button("↓ Labeled image",png_bytes(marked),"wastewise_result.png","image/png",width="stretch")
        y.download_button("↓ CSV",csv_bytes(rows),"wastewise_objects.csv","text/csv",width="stretch")
        report={"model":result["model_id"],"seconds":result["elapsed"],"settings":result["settings"],
                "coordinate_format":"original-image pixels: x1,y1,x2,y2", "detections":rows}
        z.download_button("↓ JSON",json.dumps(report,indent=2),"wastewise_result.json","application/json",width="stretch")
        st.caption("Scores rank model matches; they are not measured accuracy or proof of correct material identification.")
    with right:
        st.subheader("Explore an object")
        if not rows:
            st.info("No objects passed the selected threshold. Try a clearer photo, a lower threshold, or different query classes.")
        else:
            idx=st.selectbox("Choose a numbered object",range(len(rows)),format_func=lambda i:f'{i+1}. {rows[i]["name"]} · {rows[i]["category"]}')
            row=rows[idx]
            st.markdown(f'**{row["name"]}** · {row["category"]}')
            st.caption(f'Model score {row["score"]:.3f} · {row["handling"]}')
            st.caption("Confirm the object and its condition before following a recommendation.")
            guidance(row["key"])
    if rows:
        with st.expander("All detected objects"):
            st.dataframe([{"Object":n,"Name":r["name"],"Category":r["category"],"Score":round(r["score"],3),"Review":"Unverified"} for n,r in enumerate(rows,1)],hide_index=True,width="stretch")
    sid=result.get("scan_id")
    if sid and rows:
        with st.expander("Correct a prediction"):
            persisted=scan_rows(sid)
            with st.form("feedback_"+sid):
                target=st.selectbox("Object to correct",range(len(persisted)),format_func=lambda i:f'{i+1}. {persisted[i]["name"]}')
                corrected=st.selectbox("Correct label",["false_positive"]+list(BY_KEY),format_func=lambda k:"Not a supported waste object / false positive" if k=="false_positive" else BY_KEY[k]["name"])
                comment=st.text_input("Optional explanation")
                if st.form_submit_button("Save correction"):
                    add_feedback(persisted[target]["id"],corrected,comment)
                    st.success("Correction saved separately. It will require review before future model training.")

if page=="Detect waste":
    st.markdown('<div class="eyebrow">MATERIALS HAVE MORE THAN ONE LIFE</div><div class="hero"><h1>See waste differently.</h1><p>Find individual objects in a photo, explore their sorting category, and discover practical ways to recover value.</p></div>',unsafe_allow_html=True)
    samples=sorted((ROOT/"assets"/"examples").glob("*.jpg"))
    sources=["Upload","Camera snapshot"]+(["Examples"] if samples else [])
    source=st.radio("Image source",sources,horizontal=True,key="image_source")
    raw=None;source_name="image.png"
    if source=="Upload":
        f=st.file_uploader("Choose a photo with one or more waste objects",type=["jpg","jpeg","png","webp"],help="Up to 20 MB and 24 megapixels.")
        if f is not None:
            raw=f.getvalue();source_name=f.name
    elif source=="Camera snapshot":
        st.caption("Take a still photograph. This version does not process a continuous video stream.")
        f=st.camera_input("Photograph your waste")
        if f is not None:
            raw=f.getvalue();source_name="camera_snapshot.jpg"
    else:
        p=st.selectbox("Example photograph",samples,format_func=lambda p:p.stem.replace("_"," "))
        raw=p.read_bytes();source_name=p.name
    with st.expander("Detection settings",expanded=False):
        a,b,c=st.columns(3)
        engine=a.selectbox("Detector",["Pretrained OWLv2","Custom YOLO"])
        device=b.selectbox("Compute",["cpu","cuda"],help="CPU works without a graphics card. CUDA requires a compatible PyTorch installation.")
        shape=c.selectbox("Draw around objects",["Rectangle","Ellipse"])
        a,b,c=st.columns(3)
        threshold=a.slider("Minimum model score",0.05,0.70,0.20,0.01)
        overlap=b.slider("Duplicate box overlap",0.20,0.80,0.45,0.05,help="Lower values suppress more overlapping proposals. This may also hide genuinely overlapping objects.")
        detailed=c.checkbox("Detailed scan",help="OWLv2: full photo plus four crops. Slower, and may produce extra false positives. YOLO: larger input size.")
        show_score=st.checkbox("Show scores on image",value=True)
        persist=st.checkbox("Save this scan to local history",value=True)
        weights=""
        if engine=="Pretrained OWLv2":
            keys=st.multiselect("Object classes to look for",DEFAULT_KEYS,default=DEFAULT_KEYS,format_func=lambda k:BY_KEY[k]["name"])
        else:
            keys=[]
            weights=st.text_input("Your own trained .pt model",str(ROOT/"models"/"custom"/"best.pt"))
            st.caption("Install requirements-training.txt first. The model's own classes are used. Unmapped names receive Needs review.")
    if raw:
        try:
            image=load_image(raw)
        except ValueError as e:
            st.error(str(e));st.stop()
        fingerprint=hashlib.sha256(raw).hexdigest()
        settings=dict(engine=engine,device=device,threshold=threshold,nms_iou=overlap,detailed=detailed,keys=keys)
        if st.button("Identify waste →",type="primary",width="stretch"):
            try:
                detector=get_detector(engine,device,weights)
                with st.spinner("Looking for objects… a detailed CPU scan takes longer."):
                    rows,elapsed=detector.predict(image,keys,threshold,overlap,detailed)
                result=dict(rows=rows,elapsed=elapsed,model_id=detector.model_id,settings=settings,fingerprint=fingerprint)
                if persist:
                    result["scan_id"]=save_scan(image,annotate(image,rows,shape,show_score),rows,source_name,detector.model_id,elapsed,settings)
                st.session_state["result"]=result
            except Exception as e:
                st.error(f"Detection could not finish: {e}")
                st.caption("See START_HERE.md for model setup, memory and installation troubleshooting.")
        result=st.session_state.get("result")
        if result and result["fingerprint"]==fingerprint:
            if result["settings"]!=settings:
                st.info("Detection settings changed. The result below uses the previous settings; select Identify waste to run again.")
            show_result(image,result,shape,show_score)
        else:
            st.image(image,width="stretch",caption="Your photograph · select Identify waste to generate predictions")
    else:
        st.info("Upload a photograph or take a snapshot to start.")
        cols=st.columns(3)
        for col,title,body in zip(cols,["01 · Find the objects","02 · Understand the category","03 · Choose a useful next step"],["Separate boxes and labels for individual objects.","Organic and inorganic household sorting categories.","Conditional reuse, recycling, composting and regrowing guidance."]):
            with col:
                with st.container(border=True):
                    st.markdown(f"**{title}**");st.caption(body)

elif page=="Scan history":
    st.title("Your scan history")
    st.write("Revisit saved predictions and export your local records.")
    scans=list_scans()
    a,b=st.columns(2)
    a.download_button("Download SQLite database",database_bytes(),"wastewise.sqlite3","application/vnd.sqlite3")
    b.download_button("Download corrections",json.dumps(export_feedback(),indent=2),"wastewise_feedback.json","application/json")
    st.caption("The SQLite export contains metadata and file paths. Keep the runtime/scans folder too if you want the saved images on another computer.")
    if not scans:
        st.info("No saved scans yet. Enable saving on the detection page.")
    else:
        i=st.selectbox("Saved scan",range(len(scans)),format_func=lambda i:f'{scans[i]["created_at"][:19]} UTC · {scans[i]["source_name"]} · {scans[i]["object_count"]} objects')
        s=scans[i]
        original=Path(s["image_path"])
        if not original.is_absolute():
            original=RUNTIME/original
        if original.is_file():
            im=load_image(original.read_bytes())
            show_result(im,dict(rows=scan_rows(s["id"]),elapsed=s["elapsed_seconds"],model_id=s["model_id"],settings=json.loads(s["settings_json"]),scan_id=s["id"]),"Rectangle",True)
        else:
            st.warning("The original image is not at the recorded path. Copy its runtime/scans folder with the database.")
            st.dataframe(scan_rows(s["id"]))

elif page=="Recovery guide":
    st.title("A useful next step")
    st.write("Explore the same reviewed guidance used for detected objects.")
    st.info("Organic/Inorganic are this project's household sorting labels. Paper and cardboard use the Inorganic dry-recyclables stream, even though they are plant-derived. Special handling is shown separately.")
    group=st.radio("Filter",["All","Organic","Inorganic"],horizontal=True)
    choices=[c["key"] for c in CATALOG if group=="All" or c["category"]==group]
    key=st.selectbox("Material or object",choices,format_func=lambda k:BY_KEY[k]["name"])
    st.subheader(BY_KEY[key]["name"])
    st.caption(BY_KEY[key]["category"]+" · "+BY_KEY[key]["handling"])
    guidance(key)

elif page=="Dataset & training":
    st.title("From a working baseline to your own model")
    st.write("The OWLv2 detector works without training on the downloadable dataset. Dataset downloads do not change its weights.")
    st.subheader("Downloadable detection dataset")
    st.markdown("**GARBAGE CLASSIFICATION 3** · Material Identification · mirrored by keremberke · CC BY 4.0")
    st.write("Six annotated classes: biodegradable, cardboard, glass, metal, paper and plastic. The biodegradable label is broad; it does not identify a specific fruit peel.")
    available=sum((ROOT/"data"/"garbage"/(s+".zip")).exists() for s in ["train","valid","test"])
    st.caption(f"Dataset archives available locally: {available}/3. Download archives with the command below.")
    report=ROOT/"data"/"dataset_report.json"
    if report.exists():
        summary=json.loads(report.read_text())
        st.dataframe(summary.get("splits",[]),hide_index=True,width="stretch")
        st.caption(summary.get("note",""))
    st.link_button("Dataset source ↗","https://huggingface.co/datasets/keremberke/garbage-object-detection")
    st.markdown("**Prepare the supplied archives**")
    st.code("python scripts/download_dataset.py\npython scripts/prepare_dataset.py",language="bash")
    st.markdown("**Train a separate YOLO model**")
    st.code("python -m pip install -r requirements-training.txt\npython scripts/train.py --epochs 50 --device cpu\npython scripts/evaluate.py --weights models/custom/best.pt",language="bash")
    st.caption("GPU training is recommended for the full dataset. CPU training is supported but can take a long time. See notebooks/Train_in_Colab.ipynb for a GPU workflow.")
    st.markdown("**Before reporting research results**")
    st.write("Run the dataset audit, inspect annotations, choose settings on validation data, and keep final test data separate. Preparation creates a split stratified by dominant class and grouped by source filename. Original upstream split provenance is retained. This does not establish independence from every pretrained model's training data.")
    st.code("python scripts/audit_dataset.py",language="bash")
    st.write("To learn exact organic object names with YOLO, add human-reviewed boxes for those classes and retrain with the expanded class list. Current broad dataset labels cannot establish that capability.")

else:
    st.title("Know what the model can tell you")
    st.markdown("**Default engine: Google OWLv2, an open-vocabulary pretrained detector.** It compares visual regions with the selected text descriptions. This package does not claim to have trained OWLv2 on its waste dataset.")
    st.link_button("Original model card ↗","https://huggingface.co/google/owlv2-base-patch16-ensemble")
    st.write("The application adds category mapping, duplicate suppression, conditional recovery guidance, image annotation, SQLite history and exports.")
    st.markdown("**Practical limits**")
    st.write("Materials with similar appearance can be confused. Occluded objects may be missed, nested boxes may remain, and unsupported objects may be mislabeled. A photograph cannot establish contamination, polymer type, food safety, plant viability, ownership, or whether an object has been discarded.")
    st.write("Prediction scores are not calibrated accuracy. There is no universal accuracy percentage in this application. The included validation report records checks actually run during packaging.")
    verification=ROOT/"docs"/"VERIFICATION.md"
    if verification.exists():
        with st.expander("Packaging verification"):
            st.markdown(verification.read_text())
    st.caption("For local educational and research use. No cloud AI key is required for the default engine. Model and dataset attribution are in THIRD_PARTY_NOTICES.md.")
