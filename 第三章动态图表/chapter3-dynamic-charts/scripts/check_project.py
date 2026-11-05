from pathlib import Path
import base64
import io
import json
import re
from PIL import Image,ImageStat

ROOT=Path(__file__).resolve().parents[1]


def check():
    csvs=list((ROOT/'data').glob('*.csv'))
    assert len(csvs)==7,'应包含 7 份图表数据。'
    assert not list((ROOT/'data').glob('*.xlsm')),'本项目使用提取数据，不依赖宏工作簿。'
    hr=(ROOT/'data/05_hr_department_education.csv').read_text(encoding='utf-8-sig')
    assert '员工号' not in hr and '月收入合计' in hr
    files=sorted((ROOT/'outputs/charts').glob('*.png'))
    assert len(files)==7
    for number,file in enumerate(files,1):
        assert file.name.startswith(f'{number:02d}_')
        with Image.open(file) as image:
            rgb=image.convert('RGB')
            assert rgb.width>=1000 and rgb.height>=650
            assert rgb.getpixel((0,0))==(26,30,67)
            assert sum(ImageStat.Stat(rgb).var)>100
    notebook=json.loads((ROOT/'notebooks/chapter3_dynamic_charts.ipynb').read_text(encoding='utf-8'))
    cells=[c for c in notebook['cells'] if c['cell_type']=='code']
    assert notebook['nbformat']==4 and len(cells)==8
    for cell in cells:
        code='\n'.join(s for s in cell['source'].splitlines() if not s.startswith('%'))
        compile(code,'<notebook>','exec')
        assert not any(o.get('output_type')=='error' for o in cell['outputs'])
    html=(ROOT/'outputs/interactive.html').read_text(encoding='utf-8')
    match=re.search(r'<script id="chart-data" type="application/json">(.*?)</script>',html,re.S)
    payload=json.loads(match.group(1));assert len(payload)==7
    assert [len(c['states']) for c in payload]==[6,4,2,8,8,2,12]
    for chart in payload:
        assert 0<=chart['selected']<len(chart['states'])
        for state in chart['states']:
            data=base64.b64decode(state['image'].split(',',1)[1])
            with Image.open(io.BytesIO(data)) as image:assert image.width>=700 and image.height>=500
    print('通过：7 组数据、7 张默认图、8 个 Notebook 代码单元格及 42 种离线预览状态。')


if __name__=='__main__':
    check()
