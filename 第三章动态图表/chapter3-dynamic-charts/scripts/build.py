"""Export seven default PNGs and a self-contained interactive HTML preview."""
from pathlib import Path
import argparse
import base64
import io
import json
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def build(include_html=True,update_preview=False):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from PIL import Image,ImageDraw,ImageFont
    from dynamic_charts import FUNCTIONS,DEFAULTS,NAMES,FONT,ROOT,state_options
    out=ROOT/'outputs';(out/'charts').mkdir(parents=True,exist_ok=True)
    pngs=[]
    for number in range(1,8):
        figure=FUNCTIONS[number](**DEFAULTS[number])
        path=out/'charts'/f'{number:02d}_{NAMES[number]}.png'
        figure.savefig(path,dpi=160,facecolor=figure.get_facecolor())
        plt.close(figure);pngs.append(path)
        if update_preview:shutil.copy(path,ROOT/'assets/charts'/path.name)
        print(f'已生成 {number}：{NAMES[number]}',flush=True)
    if include_html:
        charts=[]
        for number in range(1,8):
            states=[];default_index=0
            for index,(label,config) in enumerate(state_options(number)):
                figure=FUNCTIONS[number](**config);buffer=io.BytesIO()
                figure.savefig(buffer,format='png',dpi=120,facecolor=figure.get_facecolor())
                plt.close(figure)
                states.append({'label':label,'config':config,'image':'data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode()})
                if config==DEFAULTS[number]:default_index=index
            charts.append({'number':number,'title':NAMES[number],'states':states,'selected':default_index})
        template=(ROOT/'src/preview_template.html').read_text(encoding='utf-8')
        payload=json.dumps(charts,ensure_ascii=False).replace('<','\\u003c')
        html=template.replace('CHART_DATA_JSON',payload)
        (out/'interactive.html').write_text(html,encoding='utf-8')
        if update_preview:shutil.copy(out/'interactive.html',ROOT/'interactive.html')
        print(f'离线预览已生成，共 {sum(len(c["states"]) for c in charts)} 种选择状态。',flush=True)
    preview=Image.new('RGB',(1440,1960),'#F3F5F9');draw=ImageDraw.Draw(preview)
    font=ImageFont.truetype(str(ROOT/'assets/fonts/NotoSansCJKsc-Regular.otf'),20)
    for index,path in enumerate(pngs):
        image=Image.open(path).convert('RGB');image.thumbnail((690,435))
        x=index%2*720+10;y=index//2*490+35
        preview.paste(image,(x,y));draw.text((x,y-28),path.stem,fill='#253455',font=font)
    preview.save(out/'preview.png')
    if update_preview:shutil.copy(out/'preview.png',ROOT/'assets/preview.png')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='生成第三章七组动态图表与离线交互预览。')
    parser.add_argument('--no-html',action='store_true',help='只生成默认 PNG。')
    parser.add_argument('--update-preview',action='store_true',help='同时更新仓库中已提交的示例图片和 HTML。')
    args=parser.parse_args();build(not args.no_html,args.update_preview)
