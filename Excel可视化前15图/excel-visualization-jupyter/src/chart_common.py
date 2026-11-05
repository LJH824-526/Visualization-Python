from pathlib import Path
from io import BytesIO
import math
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager, colors
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle, FancyBboxPatch, PathPatch, Circle, Wedge
from matplotlib.path import Path as MplPath
from matplotlib.ticker import FuncFormatter

# 从脚本目录或 Notebook 工作目录向上定位项目，支持不同启动目录。
def find_project_root():
    candidates = [Path.cwd()]
    if '__file__' in globals():
        candidates.insert(0, Path(__file__).resolve().parent)
    for start in candidates:
        for candidate in (start, *start.parents):
            if (candidate / 'data' / '第二章 图表(前15).xlsx').is_file():
                return candidate
    raise FileNotFoundError('找不到项目 data 目录。请保留完整项目结构，并从项目根目录或 notebooks 目录运行。')

BASE_DIR = find_project_root()
EXCEL_FILE = BASE_DIR / 'data' / '第二章 图表(前15).xlsx'
OUT_DIR = BASE_DIR / 'outputs' / 'charts'
OUT_DIR.mkdir(parents=True, exist_ok=True)
if not EXCEL_FILE.exists():
    raise FileNotFoundError(f'未找到 {EXCEL_FILE.name}。请将 Excel 放在项目 data 目录，或修改 EXCEL_FILE。')

for font_file in (BASE_DIR / 'assets' / 'fonts').glob('*.otf'):
    font_manager.fontManager.addfont(str(font_file))
available_fonts = {f.name for f in font_manager.fontManager.ttflist}
FONT = next((s for s in ['Microsoft YaHei', '微软雅黑', 'Noto Sans CJK SC', 'SimHei', 'PingFang SC']
             if s in available_fonts), 'DejaVu Sans')
if FONT == 'DejaVu Sans':
    raise RuntimeError('缺少中文字体。请保留配套 assets/fonts 文件夹，或安装微软雅黑/黑体后重启内核。')
plt.rcParams.update({'font.family': FONT, 'axes.unicode_minus': False,
                     'figure.dpi': 110, 'savefig.dpi': 180,
                     'svg.fonttype': 'path', 'axes.linewidth': 0.6})
BG, WHITE = '#1A1E43', '#F2F2F2'
BLUE, PINK, LIGHT_BLUE = '#0070C0', '#E74E69', '#82ADD7'
NS = {'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'd': 'http://schemas.openxmlformats.org/drawingml/2006/chartDrawing'}
SHEETS = pd.ExcelFile(EXCEL_FILE, engine='openpyxl').sheet_names


def read_table(number, usecols, nrows, header=1):
    """按原表的准确位置读取；不依赖 Unnamed 列名，也不读取右侧辅助图形。"""
    df = pd.read_excel(EXCEL_FILE, sheet_name=SHEETS[number-1],
                       usecols=usecols, header=header, nrows=nrows,
                       engine='openpyxl')
    df.columns = [str(c).strip() for c in df.columns]
    if df.iloc[:, 0].isna().any():
        raise ValueError(f'{SHEETS[number-1]} 的数据区域含空白分类，请检查原表。')
    return df


def numeric(df, column):
    return pd.to_numeric(df[column], errors='raise').to_numpy(dtype=float)


def xml_color(element, default=WHITE):
    if element is None:
        return default
    rgb = element.find('.//a:srgbClr', NS)
    scheme = element.find('.//a:schemeClr', NS)
    if rgb is not None:
        value, node = '#' + rgb.get('val'), rgb
    elif scheme is not None:
        palette = {'bg1': '#FFFFFF', 'lt1': '#FFFFFF', 'dk1': '#000000',
                   'tx1': '#000000', 'accent1': BLUE, 'accent2': '#ED7D31'}
        value, node = palette.get(scheme.get('val'), default), scheme
    else:
        return default
    rgb_array = np.array(colors.to_rgb(value))
    mod, off, alpha = 1., 0., 1.
    for child in node:
        key = child.tag.split('}')[-1]
        if key == 'lumMod': mod = int(child.get('val')) / 100000
        elif key == 'lumOff': off = int(child.get('val')) / 100000
        elif key == 'alpha': alpha = int(child.get('val')) / 100000
    return (*np.clip(rgb_array * mod + off, 0, 1), alpha)


def template_xml(number):
    """只读取 Excel 内的矢量样式和文本，不提取或粘贴模板截图。"""
    if number == 7:
        return None, None
    chart_number = number if number < 7 else number - 1
    with zipfile.ZipFile(EXCEL_FILE) as archive:
        chart = ET.fromstring(archive.read(f'xl/charts/chart{chart_number}.xml'))
        rels = ET.fromstring(archive.read(f'xl/charts/_rels/chart{chart_number}.xml.rels'))
        shape_ref = chart.find('c:userShapes', NS)
        shape_root = None
        if shape_ref is not None:
            rid = shape_ref.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
            rel = next(r for r in rels if r.get('Id') == rid)
            name = Path(rel.get('Target')).name
            shape_root = ET.fromstring(archive.read('xl/drawings/' + name))
    return chart, shape_root


# 保留各示例画布的长宽比例；绘图区位置直接读取 Excel 的 manualLayout。
ASPECTS = {1:866/608, 2:866/593, 3:866/607, 4:866/606, 5:865/579,
           6:866/578, 7:748/373, 8:866/581, 9:865/636, 10:924/579,
           11:865/624, 12:866/590, 13:865/613, 14:866/606, 15:865/604}


def canvas(number):
    fig = plt.figure(figsize=(6, 6/ASPECTS[number]), facecolor=BG)
    chart, shape_root = template_xml(number)
    if chart is not None:
        layout = chart.find('c:chart/c:plotArea/c:layout/c:manualLayout', NS)
        if layout is not None:
            d = {e.tag.split('}')[-1]: e.get('val') for e in layout}
            x, top, w, h = (float(d[k]) for k in ('x', 'y', 'w', 'h'))
            bounds = [x, 1-top-h, w, h]
        else:
            bounds = [.25, .16, .50, .60]
    else:
        bounds = [.12, .22, .76, .43]
    ax = fig.add_axes(bounds, facecolor=BG)
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.tick_params(colors=WHITE, labelsize=9, length=0, pad=3)
    ax.set_axisbelow(True)
    return fig, ax, shape_root


def text_width(fig, text, size, weight='normal'):
    prop = FontProperties(family=FONT, size=size, weight=weight)
    return fig.canvas.get_renderer().get_text_width_height_descent(text, prop, False)[0] / fig.dpi


def wrap_text(fig, text, size, width, weight='normal'):
    lines, line = [], ''
    for ch in text:
        if ch == '\n' or (line and text_width(fig, line + ch, size, weight) > width):
            lines.append(line)
            line = '' if ch == '\n' else ch
        else:
            line += ch
    if line: lines.append(line)
    return lines or ['']


def template_text(fig, root, replacements=None, skip_text=(), skip_exact=()):
    """读取原图文本框的坐标、字号、粗细、文字颜色和段间距。"""
    if root is None: return
    replacements = replacements or {}
    fw, fh = fig.get_size_inches()
    for anchor in root:
        shape = anchor.find('d:sp', NS)
        if shape is None: continue
        body = shape.find('d:txBody', NS)
        if body is None: continue
        paragraphs = body.findall('a:p', NS)
        if not any(p.find('.//a:t', NS) is not None for p in paragraphs): continue
        actual_text = ''.join(t.text or '' for t in body.findall('.//a:t', NS))
        if actual_text in skip_exact or any(t in actual_text for t in skip_text): continue
        origin, end = anchor.find('d:from', NS), anchor.find('d:to', NS)
        if origin is None or end is None: continue
        x0, top = float(origin.find('d:x', NS).text), float(origin.find('d:y', NS).text)
        x1, bot = float(end.find('d:x', NS).text), float(end.find('d:y', NS).text)
        bp = body.find('a:bodyPr', NS)
        li = float(bp.get('lIns', '91440')) / 914400 if bp is not None else .1
        ti = float(bp.get('tIns', '45720')) / 914400 if bp is not None else .05
        ri = float(bp.get('rIns', '91440')) / 914400 if bp is not None else .1
        vcenter = bp is not None and bp.get('anchor') == 'ctr'
        cursor = top + ti/fh
        for para in paragraphs:
            text = ''.join(t.text or '' for t in para.findall('.//a:t', NS))
            for old, new in replacements.items(): text = text.replace(old, new)
            if not text: continue
            run_props = para.find('a:r/a:rPr', NS)
            if run_props is None: run_props = para.find('a:endParaRPr', NS)
            size = float(run_props.get('sz', '1100'))/100 if run_props is not None else 11
            weight = 'bold' if run_props is not None and run_props.get('b') == '1' else 'normal'
            color = xml_color(run_props)
            pp = para.find('a:pPr', NS)
            center = pp is not None and pp.get('algn') == 'ctr'
            lines = wrap_text(fig, text, size, max(.3, (x1-x0)*fw-li-ri), weight)
            spacing = para.find('a:pPr/a:lnSpc/a:spcPts', NS)
            leading = float(spacing.get('val'))/100 if spacing is not None else size*1.3
            xpos = (x0+x1)/2 if center else x0+li/fw
            ypos = (top+bot)/2 if vcenter and len(paragraphs)==1 else cursor
            fig.text(xpos, 1-ypos, '\n'.join(lines), fontsize=size, color=color,
                     weight=weight, ha='center' if center else 'left',
                     va='center' if vcenter and len(paragraphs)==1 else 'top',
                     linespacing=leading/size, zorder=20)
            cursor += max(leading, size*1.15)*len(lines)/72/fh


def category_axis(ax, labels, ymax, step=None, grid=True, ylabels=True, baseline=False):
    ax.set_xlim(-.5, len(labels)-.5)
    ax.set_xticks(np.arange(len(labels)), labels)
    ax.set_ylim(0, ymax)
    if step is not None: ax.set_yticks(np.arange(0, ymax + step*.01, step))
    if not ylabels: ax.set_yticks([])
    if grid: ax.yaxis.grid(True, color=WHITE, alpha=.20, lw=.5, ls=(0,(6,3)))
    if baseline:
        ax.spines['bottom'].set_visible(True)
        ax.spines['bottom'].set_color((1,1,1,.35))


def gradient_rect(ax, x, y, w, h, bottom, top, rounded=False):
    ramp = np.linspace(0, 1, 320)[:, None, None]
    c0, c1 = np.array(colors.to_rgba(bottom)), np.array(colors.to_rgba(top))
    img = ax.imshow(c0[None,None,:]*(1-ramp)+c1[None,None,:]*ramp,
                    extent=(x,x+w,y,y+h), origin='lower', aspect='auto',
                    interpolation='bicubic', zorder=3)
    if rounded:
        # 使用显示坐标计算圆角，避免横纵轴量纲不同造成圆角失真。
        p0, p1 = ax.transData.transform((0,0)), ax.transData.transform((1,1))
        rx = w/2
        ry = min(h/2, rx*abs((p1[0]-p0[0])/(p1[1]-p0[1])))
        k = .55228475
        verts=[(x+rx,y),(x+w-rx,y),(x+w-rx+k*rx,y),(x+w,y+ry-k*ry),(x+w,y+ry),
               (x+w,y+h-ry),(x+w,y+h-ry+k*ry),(x+w-rx+k*rx,y+h),(x+w-rx,y+h),
               (x+rx,y+h),(x+rx-k*rx,y+h),(x,y+h-ry+k*ry),(x,y+h-ry),
               (x,y+ry),(x,y+ry-k*ry),(x+rx-k*rx,y),(x+rx,y),(x+rx,y)]
        codes=[MplPath.MOVETO,MplPath.LINETO]+[MplPath.CURVE4]*3+[MplPath.LINETO]+[MplPath.CURVE4]*3+[MplPath.LINETO]+[MplPath.CURVE4]*3+[MplPath.LINETO]+[MplPath.CURVE4]*3+[MplPath.CLOSEPOLY]
        clip=PathPatch(MplPath(verts,codes),facecolor='none',edgecolor='none')
        ax.add_patch(clip); img.set_clip_path(clip)
    return img


def value_labels(ax, x, y, color=WHITE, size=9, offset=3, **kwargs):
    for a,b in zip(x,y):
        ax.annotate(f'{b:g}', (a,b), xytext=(0,offset), textcoords='offset points',
                    ha='center', va='bottom', color=color, fontsize=size, zorder=8, **kwargs)


def finish(fig, number, name, show=True):
    # 不使用 tight_layout/bbox_inches='tight'，保留模板边距和原始画布比例。
    path = OUT_DIR / f'{number:02d}_{name}.png'
    fig.savefig(path, dpi=180, facecolor=BG, edgecolor=BG)
    if show: plt.show()
    return fig


def smooth_curve(x, y, samples=50):
    """保形三次 Hermite 插值，经过所有原始点，避免平滑曲线产生虚假的负数。"""
    x, y = np.asarray(x,float), np.asarray(y,float)
    slopes = np.diff(y)/np.diff(x)
    tangents = np.zeros(len(y)); tangents[0],tangents[-1]=slopes[0],slopes[-1]
    for j in range(1,len(y)-1):
        if slopes[j-1]*slopes[j] > 0:
            tangents[j] = 2/(1/slopes[j-1]+1/slopes[j])
    xx, yy = [], []
    for j in range(len(x)-1):
        t=np.linspace(0,1,samples,endpoint=(j==len(x)-2)); h=x[j+1]-x[j]
        yy.extend((2*t**3-3*t**2+1)*y[j]+(t**3-2*t**2+t)*h*tangents[j]
                  +(-2*t**3+3*t**2)*y[j+1]+(t**3-t**2)*h*tangents[j+1])
        xx.extend(x[j]+t*h)
    return np.array(xx),np.array(yy)

print(f'已读取 {len(SHEETS)} 个工作表；中文字体：{FONT}；图片输出：{OUT_DIR.name}')
