from pathlib import Path
import sys,json,base64,re,io,itertools
from PIL import Image,ImageStat

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import dashboard as d


def check():
    assert len(list((ROOT/'data').glob('*.csv')))==6
    components=json.loads((ROOT/'data/components.json').read_text(encoding='utf-8'))
    assert len(components)==len(d.COMPONENTS)
    for item in components:
        image=Image.open(ROOT/'outputs/charts'/item['filename']).convert('RGB')
        assert image.width>=1000 and image.height>=650
        assert sum(ImageStat.Stat(image).var)>100
    image=Image.open(ROOT/'outputs/dashboard.png').convert('RGB')
    assert image.width>=2000 and image.height>=1000
    assert image.getpixel((0,0))==tuple(int(d.BG[i:i+2],16) for i in [1,3,5])
    nb=json.loads((ROOT/'notebooks/dashboard.ipynb').read_text(encoding='utf-8'))
    code_cells=[c for c in nb['cells'] if c['cell_type']=='code']
    assert nb['nbformat']==4 and len(code_cells)==len(d.COMPONENTS)+2
    for cell in code_cells:
        code='\n'.join(s for s in cell['source'].splitlines() if not s.startswith('%'))
        compile(code,'<notebook>','exec')
        assert not any(o.get('output_type')=='error' for o in cell['outputs'])
    html=(ROOT/'outputs/dashboard.html').read_text(encoding='utf-8')
    match=re.search(r'<script type="application/json" id="dashboard-data">(.*?)</script>',html,re.S)
    data=json.loads(match.group(1));expected=2 if 'mode' in d.DEFAULTS else 24
    assert len(data['states'])==expected
    combinations=list(itertools.product(*(item['options'] for item in data['controls'])))
    keys=[item['key'] for item in data['controls']]
    configs=[state['config'] for state in data['states']]
    assert all(dict(zip(keys,values)) in configs for values in combinations)
    assert data['default'] in configs
    for state in data['states']:
        image=Image.open(io.BytesIO(base64.b64decode(state['image'].split(',',1)[1])))
        assert image.width>=1500 and image.height>=750
    for path in [*(ROOT/'src').glob('*.py'),*(ROOT/'scripts').glob('*.py'),*(ROOT/'tests').glob('*.py')]:
        compile(path.read_text(encoding='utf-8'),path.name,'exec')
    print(f'通过：独立看板、{len(components)} 张组件图、{expected} 个离线状态和 Notebook 语法检查。')


if __name__=='__main__':check()
