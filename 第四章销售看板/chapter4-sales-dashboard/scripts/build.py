"""Generate the dashboard, component PNGs and a self-contained HTML preview."""
from pathlib import Path
import sys,argparse,io,json,base64,shutil

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def build(update_preview=False):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import dashboard as d
    out=ROOT/'outputs';(out/'charts').mkdir(parents=True,exist_ok=True)
    figure=d.render_dashboard(**d.DEFAULTS)
    figure.savefig(out/'dashboard.png',dpi=140,facecolor=figure.get_facecolor());plt.close(figure)
    if update_preview:shutil.copy(out/'dashboard.png',ROOT/'assets/dashboard.png')
    components=[]
    for number,item in d.COMPONENTS.items():
        title=item[1] if isinstance(item,tuple) else item
        safe=title.replace('(','_').replace(')','')
        figure=d.render_component(number,**d.DEFAULTS)
        name=f'{number:02d}_{safe}.png';figure.savefig(out/'charts'/name,dpi=160,facecolor=figure.get_facecolor());plt.close(figure)
        if update_preview:shutil.copy(out/'charts'/name,ROOT/'assets/charts'/name)
        components.append({'number':number,'title':title,'filename':name})
    states=[]
    for label,config in d.preview_states():
        figure=d.render_dashboard(**config);buffer=io.BytesIO()
        figure.savefig(buffer,format='png',dpi=100,facecolor=figure.get_facecolor());plt.close(figure)
        states.append({'label':label,'config':config,'image':'data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode()})
    is_hr='mode' in d.DEFAULTS
    controls=[{'key':'mode','label':'数据口径','options':['模板复现','明细重算']}] if is_hr else [
        {'key':'month','label':'月份','options':d.MANIFEST['months']},
        {'key':'theme','label':'配色','options':list(d.THEMES)}]
    payload={'title':'公司人员结构看板' if is_hr else '公司销售数据可视化看板',
             'default':d.DEFAULTS,'controls':controls,'states':states,
             'note':'模板学历前两项原表引用互换，可切换明细重算核对。' if is_hr else '销量按明细记录数统计；销售额、利润额以万计；成本保持原表口径。'}
    template=(ROOT/'src/preview_template.html').read_text(encoding='utf-8')
    html=template.replace('DASHBOARD_DATA_JSON',json.dumps(payload,ensure_ascii=False).replace('<','\\u003c'))
    (out/'dashboard.html').write_text(html,encoding='utf-8')
    if update_preview:shutil.copy(out/'dashboard.html',ROOT/'dashboard.html')
    (out/'components.json').write_text(json.dumps(components,ensure_ascii=False,indent=2),encoding='utf-8')
    if update_preview:shutil.copy(out/'components.json',ROOT/'data/components.json')
    print(f'已生成 1 张看板、{len(components)} 张组件图、{len(states)} 个离线选择状态。')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--update-preview',action='store_true')
    build(parser.parse_args().update_preview)
