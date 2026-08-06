from pathlib import Path

from PIL import Image

from ai_image_studio.jobs import prepare_job, transition


def test_prepare_strict_job(tmp_path):
    src=tmp_path/'source.jpg'; Image.new('RGB',(10,10),'white').save(src)
    job={
      'job_id':'img-001','category':'product','fidelity':'strict','status':'SPEC_LOCKED',
      'decision':{
        'category':{'type':'product','subtype':'furniture','source':'confirmed','confidence':1.0},
        'destination':{'primary':'own_web','platform':'test','profile_id':'test-web','requirements_known':True},
        'capture':{'device':{'kind':'unknown','brand':None,'model':None,'metadata_checked':False,'configuration_known':False},'source_format':'jpeg','scenario':{'location':'indoor','lighting':'unknown','subject_motion':'static','challenges':[]},'guidance_requested':False},
        'fidelity':'strict',
        'background':{'relevance':'critical','policy':'product_catalog','original_type':'unknown','target_mode':'solid','target_value':'#FFFFFF','profile_id':'test-web','shadow':'contact-soft'},
        'outputs':{'requested':['catalog','web'],'environment':{'requested':False,'context_source':'none','description':None,'reference_paths':[],'recommendations_requested':False}}
      },
      'source':{'path':str(src),'immutable':True},
      'allowed_operations':['inspect','export'],
      'forbidden_operations':['full_image_generation','geometry_change'],
      'output':{'width':1000,'height':1000,'format':'webp','quality':86,'color_space':'sRGB','remove_metadata':True},
      'confirmed':True
    }
    out=prepare_job(job,tmp_path/'workspace')
    assert out['status']=='SOURCE_PRESERVED'
    assert Path(out['source_copy']).is_file()

def test_fail_closed_transition():
    try:
        transition('AUTOMATIC_QC','EXPORTED')
    except ValueError:
        pass
    else:
        raise AssertionError('Debe bloquear exportación directa tras QC')
