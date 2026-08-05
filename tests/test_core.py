from pathlib import Path
import json, zipfile
import numpy as np
from PIL import Image, ImageDraw
from ai_image_studio.hashing import sha256_file, safe_filename
from ai_image_studio.inspect import inspect_file
from ai_image_studio.masks import compare_mask_files
from ai_image_studio.qc import validate_background, validate_dimensions
from ai_image_studio.export import export_webp
from ai_image_studio.packaging import package_directory

def test_inspect_and_hash(tmp_path):
    p=tmp_path/'x.png'; Image.new('RGB',(20,10),'white').save(p)
    data=inspect_file(p)
    assert data['width']==20 and data['height']==10
    assert data['sha256']==sha256_file(p)

def test_safe_filename():
    assert safe_filename('á test /x?.png') == 'x-.png'

def test_mask_comparison(tmp_path):
    a=np.zeros((20,20),dtype=np.uint8); a[5:15,5:15]=255
    b=a.copy()
    pa=tmp_path/'a.png'; pb=tmp_path/'b.png'
    Image.fromarray(a).save(pa); Image.fromarray(b).save(pb)
    out=compare_mask_files(pa,pb)
    assert out['iou']==1.0 and out['a']['components']==1

def test_background_and_export(tmp_path):
    src=tmp_path/'src.png'
    img=Image.new('RGBA',(100,50),(0,0,0,0)); d=ImageDraw.Draw(img); d.rectangle((30,10,70,45),fill=(10,20,30,255)); img.save(src)
    dst=tmp_path/'out.webp'
    export_webp(src,dst,1000,1000,86)
    assert validate_dimensions(dst,1000,1000,'webp')['status']=='PASS'
    assert validate_background(dst, min_channel=245, max_nonwhite_ratio=.01)['status']=='PASS'

def test_package(tmp_path):
    d=tmp_path/'outputs'; d.mkdir(); (d/'a.txt').write_text('ok')
    z=tmp_path/'x.zip'; out=package_directory(d,z,'job-1')
    assert out['files']==1
    with zipfile.ZipFile(z) as f: assert 'artifact-manifest.json' in f.namelist()
