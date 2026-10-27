import json
import sqlite3
from PIL import Image
import pytest
from wastewise.domain import Detection, clean_detections
from wastewise.database import (init_db, save_scan, scan_rows, add_feedback, export_feedback,
    database_bytes, get_recommendations, csv_bytes, list_scans)
from wastewise.imaging import load_image, png_bytes, annotate
from scripts.prepare_dataset import convert_box, safe_name

def test_duplicate_boxes_and_coordinates():
    ds=[Detection("plastic_bottle",.8,[-2,-3,100,50]),Detection("glass_bottle",.6,[0,0,99,49]),
        Detection("paper",.9,[40,30,60,45]),Detection("paper",float('nan'),[1,1,5,5])]
    out=clean_detections(ds,90,50,threshold=.2)
    assert len(out)==2
    assert out[1].box==[0,0,90.,50.]

def test_empty_image_result_and_invalid_upload():
    im=Image.new("RGB",(200,120),"white")
    assert load_image(png_bytes(im)).size==im.size
    assert annotate(im,[]).size==im.size
    with pytest.raises(ValueError):load_image(b"not an image")

def test_annotation_does_not_mutate_input():
    im=Image.new("RGB",(300,180),"white")
    ds=[Detection("banana_peel",.35,[40,50,190,130]).to_dict()]
    marked=annotate(im,ds,shape="Ellipse")
    assert im.tobytes()!=marked.tobytes()
    assert im.getpixel((40,50))==(255,255,255)

def test_scan_correction_and_consistent_database_export(tmp_path):
    db=tmp_path/"test.sqlite3";init_db(db);init_db(db)
    im=Image.new("RGB",(300,200),"white")
    rows=[Detection("banana_peel",.35,[10,10,100,90]).to_dict()]
    sid=save_scan(im,annotate(im,rows),rows,"photo.jpg","test-model",.1,{"threshold":.2},db,tmp_path)
    saved=scan_rows(sid,db);add_feedback(saved[0]["id"],"orange_peel","wrong fruit",db)
    assert scan_rows(sid,db)[0]["key"]=="banana_peel"
    assert export_feedback(db)[0]["corrected_key"]=="orange_peel"
    scan=list_scans(db)[0]
    assert (tmp_path/scan["image_path"]).exists()
    assert not __import__('pathlib').Path(scan["image_path"]).is_absolute()
    target=tmp_path/"export.sqlite3";target.write_bytes(database_bytes(db))
    with sqlite3.connect(target) as con:
        assert con.execute("SELECT count(*) FROM feedback").fetchone()[0]==1
        assert con.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
    assert get_recommendations("banana_peel",db)[0]["action"]=="Compost"
    assert b"Organic" in csv_bytes(rows)

def test_no_detection_scan_is_saved(tmp_path):
    db=tmp_path/"empty.sqlite3";init_db(db)
    im=Image.new("RGB",(100,100))
    sid=save_scan(im,im,[],"empty.png","test",0,{},db,tmp_path)
    assert scan_rows(sid,db)==[]
    assert list_scans(db)[0]["object_count"]==0

def test_coco_conversion_clips_and_rejects_bad_boxes():
    assert convert_box([-10,-10,30,30],100,100)==[.1,.1,.2,.2]
    assert convert_box([110,110,5,5],100,100) is None
    assert convert_box([0,0,-1,20],100,100) is None
    assert convert_box([0,0,float('nan'),20],100,100) is None

@pytest.mark.parametrize("name",["../outside.jpg","/etc/passwd","C:/bad.jpg","a/../../b.jpg"])
def test_archive_path_traversal_rejected(name):
    with pytest.raises(ValueError):safe_name(name)

def test_unknown_model_class_is_reviewable():
    d=Detection("new_unknown_label",.9,[0,0,100,100]).to_dict()
    assert d["category"]=="Needs review"
    assert d["needs_review"] is True

def test_split_weight_assembly_checks_integrity(tmp_path):
    from bootstrap import assemble_bundled_model
    import hashlib
    folder=tmp_path/"models/owlv2";folder.mkdir(parents=True)
    (folder/"model.safetensors.001").write_bytes(b"first")
    (folder/"model.safetensors.002").write_bytes(b"second")
    manifest=tmp_path/"models/download_manifest.json"
    manifest.write_text(json.dumps({"files":[{"name":"model.safetensors","sha256":hashlib.sha256(b"firstsecond").hexdigest()}]}))
    assemble_bundled_model(tmp_path)
    assert (folder/"model.safetensors").read_bytes()==b"firstsecond"
    (folder/"model.safetensors").unlink()
    (folder/"model.safetensors.002").write_bytes(b"corrupt")
    with pytest.raises(ValueError):assemble_bundled_model(tmp_path)
    assert not (folder/"model.safetensors").exists()
