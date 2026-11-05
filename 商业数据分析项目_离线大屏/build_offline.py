"""Package a standalone offline dashboard; Python 3.11+ with plotly and fonttools."""
from pathlib import Path
import csv,json,base64,io,re,shutil
from plotly.offline import get_plotlyjs
from fontTools import subset

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'data/orders.csv'
TEMPLATE=ROOT/'src/dashboard.html'
OUT=ROOT/'dist/index.html'
numeric={'Row ID','Sales','Profit','Quantity','Discount','Year','Margin','Ship Days'}
integer={'Row ID','Quantity','Year','Ship Days'}
booleans={'Returned','Loss'}
with SOURCE.open(encoding='utf-8-sig',newline='') as f:
    reader=csv.DictReader(f);columns=reader.fieldnames;rows=[]
    for row in reader:
        vals=[]
        for k in columns:
            v=row[k]
            if k in numeric:v=int(v) if k in integer else float(v)
            elif k in booleans:v=v.lower()=='true'
            vals.append(v)
        rows.append(vals)
raw=TEMPLATE.read_text(encoding='utf-8')
font=ROOT/'data/NotoSansCJKsc-Regular.otf'
options=subset.Options();options.layout_features=['*'];options.recalc_timestamp=False
f=subset.load_font(str(font),options);sub=subset.Subsetter(options=options)
sub.populate(text=raw+''.join(chr(i) for i in range(32,256)))
sub.subset(f);buf=io.BytesIO();f.save(buf)
font_css="@font-face{font-family:DashboardCN;src:url(data:font/otf;base64,"+base64.b64encode(buf.getvalue()).decode()+") format('opentype');font-weight:100 900;font-display:swap;}"
data=json.dumps({'columns':columns,'rows':rows},ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
page=raw.replace('/*__FONT__*/',font_css).replace('/*__PLOTLY__*/',get_plotlyjs().replace('</script','<\\/script')).replace('__DATA__',data)
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(page,encoding='utf-8')
print(f'Built {OUT}: {len(rows)} rows; {OUT.stat().st_size/1024**2:.2f} MiB; no remote resources.')
