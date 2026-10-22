# -*- coding: utf-8 -*-
"""
《Excel数据可视化——从图表到数据大屏》第二章 图表(前15) matplotlib 复刻
依赖: pip install matplotlib numpy
运行: 直接 python 运行本脚本, 输出 15 张 PNG 到 output/ 目录
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Wedge, PathPatch
from matplotlib.path import Path
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D

BG = '#1A1E43'
GRID = dict(color='white', alpha=0.22, linestyle='--', linewidth=0.7)
plt.rcParams['font.family'] = ['Microsoft YaHei', 'SimHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

try:
    OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
except NameError:
    OUT = os.path.join(os.getcwd(), 'output')
os.makedirs(OUT, exist_ok=True)

FIG = []


def new_fig(w=8.32, h=6.1):
    fig = plt.figure(figsize=(w, h), facecolor=BG)
    FIG.append(fig)
    return fig


def header(fig, title, subtitle=None, note=None):
    fig.text(0.055, 0.935, title, fontsize=17, fontweight='bold',
             color='white', ha='left', va='center')
    if subtitle:
        fig.text(0.055, 0.875, subtitle, fontsize=11.5,
                 color='white', ha='left', va='center')
    if note:
        fig.text(0.055, 0.04, note, fontsize=8.5,
                 color='#D9D9D9', ha='left', va='center')


def plot_ax(fig, rect=(0.10, 0.12, 0.86, 0.68)):
    ax = fig.add_axes(rect)
    ax.set_facecolor(BG)
    ax.tick_params(colors='white', labelsize=9, length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    return ax


def grad_bar(ax, x, y0, h, w, c_top, c_bottom, zorder=2):
    cmap = LinearSegmentedColormap.from_list('g', [c_bottom, c_top])
    img = np.linspace(0, 1, 256).reshape(-1, 1)
    ax.imshow(img, extent=[x - w / 2, x + w / 2, y0, y0 + h],
              aspect='auto', cmap=cmap, zorder=zorder, interpolation='bilinear')


def rounded_bar(ax, x, y0, h, w, c_top, c_bottom, zorder=2, n=80):
    r = w / 2
    a = np.linspace(180, 0, n)
    verts = [(x - r, y0), (x - r, y0 + h)]
    codes = [Path.MOVETO, Path.LINETO]
    for an in a[1:]:
        verts.append((x + r * np.cos(np.radians(an)), y0 + h + r * np.sin(np.radians(an))))
        codes.append(Path.LINETO)
    verts += [(x + r, y0), (x - r, y0)]
    codes += [Path.LINETO, Path.CLOSEPOLY]
    patch = PathPatch(Path(verts, codes), fc='none', ec='none')
    ax.add_patch(patch)
    cmap = LinearSegmentedColormap.from_list('g', [c_bottom, c_top])
    img = np.linspace(0, 1, 256).reshape(-1, 1)
    ax.imshow(img, extent=[x - r, x + r, y0, y0 + h + r],
              aspect='auto', cmap=cmap, zorder=zorder,
              clip_path=patch, interpolation='bilinear')


def val_label(ax, x, y, text, span, fs=9, zorder=5):
    ax.text(x, y + 0.02 * span, str(text), ha='center', va='bottom',
            fontsize=fs, color='white', zorder=zorder)


def save(name):
    plt.savefig(os.path.join(OUT, name), facecolor=BG, dpi=100)


def catmull_rom(xs, ys, n=120):
    P = list(zip(list(xs), list(ys)))
    pts = [P[0]] + P + [P[-1]]
    t = np.linspace(0, 1, n)
    ox, oy = [], []
    for i in range(len(pts) - 3):
        p0, p1, p2, p3 = pts[i:i + 4]
        for tt in t:
            ox.append(0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * tt
                             + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * tt ** 2
                             + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * tt ** 3))
            oy.append(0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * tt
                             + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * tt ** 2
                             + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * tt ** 3))
    return ox, oy


# ============ 1. 渐变柱形图 ============
def chart1():
    regions = ['华北', '华南', '东北', '西北', '西南', '华东']
    sales = [2354, 1902, 3524, 2698, 2896, 2563]
    fig = new_fig()
    header(fig, '3月各区域销量分布', '东北销量最多占比总销量的22%，华南销量最低',
           '*注：数据来源于公司销售系统，统计日期截至2022.03.31')
    ax = plot_ax(fig)
    xs = np.arange(len(regions))
    bw = 1 / (1 + 2.19)
    for x, v in zip(xs, sales):
        grad_bar(ax, x, 0, v, bw, '#0070C0', '#00B0F0')
    for x, v in zip(xs, sales):
        val_label(ax, x, v, v, 4000)
    ax.set_xlim(-0.6, 5.6)
    ax.set_ylim(0, 4200)
    ax.set_xticks(xs)
    ax.set_xticklabels(regions, fontsize=10)
    ax.set_yticks([0, 1000, 2000, 3000, 4000])
    ax.grid(axis='y', **GRID)
    save('01_渐变柱形图.png')


# ============ 2. 带均值柱形图 ============
def chart2():
    regions = ['华北', '华南', '东北', '西北', '西南', '华东']
    sales = [2354, 1902, 3524, 2698, 2896, 2563]
    mean = round(sum(sales) / len(sales), 2)
    fig = new_fig(h=5.94)
    header(fig, '3月各区域销量分布', '东北销量最多占比总销量的22%，华南销量最低',
           '*注：数据来源于公司销售系统，统计日期截至2022.03.31')
    ax = plot_ax(fig)
    xs = np.arange(len(regions))
    bw = 1 / (1 + 2.19)
    ax.bar(xs, sales, width=bw, color='#0070C0', zorder=3)
    ax.axhline(mean, color='#FFC000', lw=1.8, zorder=4)
    for x, v in zip(xs, sales):
        val_label(ax, x, v, v, 4200)
    ax.text(4.30, mean, f'平均值：{int(round(mean))}', fontsize=9, color='white',
            ha='left', va='center', zorder=6)
    ax.set_xlim(-0.6, 5.6)
    ax.set_ylim(0, 4200)
    ax.set_xticks(xs)
    ax.set_xticklabels(regions, fontsize=10)
    ax.set_yticks([0, 1000, 2000, 3000, 4000])
    ax.grid(axis='y', **GRID)
    save('02_带均值柱形图.png')


# ============ 3. 渐变圆角柱形图 ============
def chart3():
    goods = ['口红', '面膜', '隔离', '防晒', '精华', '面霜']
    sales = [653, 523, 648, 856, 714, 785]
    fig = new_fig()
    header(fig, '3月商品销量对比', '防晒销量最多，3月销量856；面膜最少，3月销量523',
           '*注：数据来源于公司销售系统，统计日期截至2022.03.31')
    ax = plot_ax(fig)
    xs = np.arange(len(goods))
    bw = 1 / (1 + 5.0)
    span = 1200
    for x, v in zip(xs, sales):
        rounded_bar(ax, x, 0, v, bw, '#00F3FE', '#0052A8')
    for x, v in zip(xs, sales):
        ax.vlines(x, v, v + 0.035 * span, color='#5B9BD5', lw=1.0, zorder=5)
        ax.text(x, v + 0.055 * span, str(v), ha='center', va='center',
                fontsize=9, color='white', zorder=6,
                bbox=dict(boxstyle='round,pad=0.3,rounding_size=0.14',
                          fc='#152E5C', ec='none'))
    ax.set_xlim(-0.7, 5.7)
    ax.set_ylim(0, 1250)
    ax.set_xticks(xs)
    ax.set_xticklabels(goods, fontsize=10)
    ax.set_yticks([0, 200, 400, 600, 800, 1000, 1200])
    ax.grid(axis='y', **GRID)
    save('03_渐变圆角柱形图.png')


# ============ 4. 标注柱形图 ============
def chart4():
    goods = ['口红', '面膜', '隔离', '防晒', '精华', '面霜', '眼影', '气垫']
    sales = [9221, 5102, 6571, 5760, 6321, 8612, 2645, 5321]
    colors = ['#7BBDD5', '#49A098', '#E66B4C', '#FFC000',
              '#0097E0', '#0070C0', '#4A5BD1', '#464CAC']
    fig = new_fig()
    header(fig, '2021年商品销量情况', '口红销量最好达9221，是眼影最低值2645近3.5倍',
           '*注：数据来源于公司销售系统，统计日期截至2022.08.31')
    ax = plot_ax(fig)
    xs = np.arange(len(goods))
    bw = 1 / (1 + 1.0)
    ax.bar(xs, sales, width=bw, color=colors, zorder=3)
    for x, v in zip(xs, sales):
        val_label(ax, x, v, v, 10500)
    ax.set_xlim(-0.7, 7.7)
    ax.set_ylim(0, 10600)
    ax.set_xticks(xs)
    ax.set_xticklabels(goods, fontsize=10)
    ax.set_yticks([0, 2000, 4000, 6000, 8000, 10000])
    ax.grid(axis='y', **GRID)
    save('04_标注柱形图.png')


# ============ 5. 层叠柱形图 ============
def chart5():
    q = ['2021Q1', 'Q2', 'Q3', 'Q4', '2022Q1', 'Q2']
    sale = [3121, 4086, 4321, 4601, 4936, 4231]
    profit = [1020, 1421, 1502, 1623, 1781, 1432]
    fig = new_fig(h=5.88)
    header(fig, '2021年至今季度销售额(万)和利润额(万)',
           '2022年第二季度销售额首次出现下降，降幅达到15%',
           '*注：数据来源于公司销售系统，统计日期截至2022.06.30')
    ax = plot_ax(fig)
    xs = np.arange(len(q))
    bw = 1 / (1 + 2.19)
    ax.bar(xs, sale, width=bw, color='#0070C0', zorder=3)
    ax.bar(xs + 0.7 * bw, profit, width=bw, color='#E74E69', zorder=4)
    for x, v in zip(xs, sale):
        val_label(ax, x, v, v, 5400)
    for x, v in zip(xs, profit):
        val_label(ax, x + 0.7 * bw, v, v, 5400)
    ax.set_xlim(-0.7, 5.7)
    ax.set_ylim(0, 5400)
    ax.set_xticks(xs)
    ax.set_xticklabels(q, fontsize=10)
    ax.set_yticks([])
    ax.add_patch(Rectangle((0.905, 0.585), 0.028, 0.05, transform=ax.transAxes,
                           fc='#0070C0', ec='none'))
    ax.add_patch(Rectangle((0.905, 0.45), 0.028, 0.05, transform=ax.transAxes,
                           fc='#E74E69', ec='none'))
    ax.text(0.945, 0.61, '销售额', transform=ax.transAxes, fontsize=10,
            color='white', ha='left', va='center')
    ax.text(0.945, 0.475, '利润额', transform=ax.transAxes, fontsize=10,
            color='white', ha='left', va='center')
    save('05_层叠柱形图.png')


# ============ 6. 蝴蝶图 ============
def butterfly(fig, cats, v2022, v2021, legend=True, label_fmt=None,
              bar_scale=None, inset=0.04):
    ax = plot_ax(fig, rect=(0.09, 0.10, 0.84, 0.70))
    y = np.arange(len(cats), 0, -1)
    m = max(max(v2022), max(v2021))
    scale = bar_scale or m * 1.478
    ax.barh(y, [-v for v in v2022], height=0.52, color='#0070C0', zorder=3)
    ax.barh(y, v2021, height=0.52, color='#E74E69', zorder=3)
    for yy, v in zip(y, v2022):
        ax.text(-v + inset * scale, yy, (label_fmt or str)(v), ha='left',
                va='center', fontsize=9, color='white', zorder=5)
    for yy, v in zip(y, v2021):
        ax.text(v - inset * scale, yy, (label_fmt or str)(v), ha='right',
                va='center', fontsize=9, color='white', zorder=5)
    for yy, c in zip(y, cats):
        ax.text(0, yy, c, ha='center', va='center', fontsize=10,
                color='white', zorder=6)
    ax.set_xlim(-scale, scale)
    ax.set_ylim(0.2, len(cats) + 1.3)
    ax.set_xticks([])
    ax.set_yticks([])
    if legend:
        ax.add_patch(Rectangle((-scale * 0.47, len(cats) + 0.82), scale * 0.04,
                               scale * 0.075, fc='#0070C0', ec='none'))
        ax.text(-scale * 0.42, len(cats) + 0.86, '2022', fontsize=10,
                color='white', ha='left', va='center')
        ax.add_patch(Rectangle((scale * 0.60, len(cats) + 0.82), scale * 0.04,
                               scale * 0.075, fc='#E74E69', ec='none'))
        ax.text(scale * 0.65, len(cats) + 0.86, '2021', fontsize=10,
                color='white', ha='left', va='center')
    return ax


def chart6():
    cats = ['华南', '华北', '东北', '西北', '华东']
    v2022 = [2238, 1531, 1426, 1321, 1215]
    v2021 = [2066, 1436, 1531, 1265, 1003]
    fig = new_fig()
    header(fig, '2022年上半年各区域对比去年销量',
           '2022年整体销量高于2021年，只有东北区域较2021有所下降',
           '*注：数据来源于公司销售系统，统计日期截至2022.06.30')
    butterfly(fig, cats, v2022, v2021)
    save('06_蝴蝶图.png')


# ============ 7. 蝴蝶图 28 ============
def chart7():
    cats = ['华东', '西北', '东北', '华北', '华南']
    v2022 = [0.36, 0.31, 0.18, 0.13, 0.09]
    v2021 = [0.42, 0.26, 0.19, 0.12, 0.05]
    fig = new_fig(8.32, 2.30)
    header(fig, '2022年第一季度销售目标完成情况',
           '华东区域完成率最高达到36%，但是相比去年的42%有所下降',
           '*注：数据来源于公司销售系统，统计日期截至2022.03.31')
    adv = 0.00422
    xb0, xbe = 0.154, 0.402
    xr0, xre = 0.560, 0.853
    cap_b = int(round((xbe - xb0) / adv))
    cap_r = int(round((xre - xr0) / adv))
    ys = [0.75, 0.70, 0.65, 0.60, 0.55]
    for yy, c, v22, v21 in zip(ys, cats, v2022, v2021):
        fig.text(0.141, yy, f'{v22:.0%}', ha='right', va='center',
                 fontsize=8, color='white')
        nb = min(int(round(v22 * 200)), cap_b)
        for k in range(nb):
            fig.text(xb0 + k * adv, yy, '|', ha='center', va='center',
                     fontsize=12, family='Stencil', color='#0070C0')
        fig.text(0.480, yy, c, ha='center', va='center',
                 fontsize=8, color='white')
        nr = min(int(round(v21 * 200)), cap_r)
        for k in range(nr):
            fig.text(xr0 + k * adv, yy, '|', ha='center', va='center',
                     fontsize=12, family='Stencil', color='#E74E69')
        fig.text(0.863, yy, f'{v21:.0%}', ha='left', va='center',
                 fontsize=8, color='white')
    save('07_蝴蝶图_28.png')


# ============ 8. 数值百分比 ============
def chart8():
    cats = ['华东', '西南', '西北', '东北', '华南', '华北']
    sales = [2109, 1369, 1872, 1536, 1946, 4321]
    place1 = [2212, 2952, 2449, 2785, 2375, 0]
    place2 = [1080.25] * 6
    pct = ['-5.8%', '-17.9%', '-15.9%', '-9.3%', '-20.8%', '-13.6%']
    total = 5401.25
    fig = new_fig()
    header(fig, '2021年各区域销量及同比情况',
           '各区域商品销量同比去年均有下降，其中华南下降最多，同比下降20.8%',
           '*注：数据来源于公司销售系统，统计日期截至2022.01.01')
    ax = plot_ax(fig)
    y = np.arange(len(cats), 0, -1)
    ax.barh(y, sales, height=0.55, color='#09387E', zorder=3)
    ax.barh(y, place1, left=sales, height=0.55, color='#82ADD7', zorder=3)
    ax.barh(y, place2, left=[a + b for a, b in zip(sales, place1)],
            height=0.55, color='#9B3D4F', zorder=3)
    for yy, v in zip(y, sales):
        ax.text(v - total * 0.015, yy, str(v), ha='right', va='center',
                fontsize=9, color='white', zorder=5)
    for yy, p in zip(y, pct):
        ax.text(total - place2[0] / 2, yy, p, ha='center', va='center',
                fontsize=9, color='white', zorder=5)
    ax.set_yticks(y)
    ax.set_yticklabels(cats, fontsize=10)
    ax.set_xticks([])
    ax.set_xlim(0, total * 1.02)
    ax.set_ylim(-0.6, 5.6)
    save('08_数值百分比.png')


# ============ 9. 对比柱形图 ============
def chart9():
    goods = ['口红', '面膜', '隔离', '防晒', '精华']
    v2021 = [3568, 4135, 4436, 4106, 4936]
    v2022 = [2569, 3241, 2965, 3209, 3541]
    diff = [a - b for a, b in zip(v2021, v2022)]
    fig = new_fig(h=6.45)
    header(fig, '2022年商品对比去年销售情况',
           '商品整体比去年销量有所下降，其中隔离下降最多，下降33%',
           '*注：数据来源于公司销售系统，统计日期截至2022.01.01')
    ax = plot_ax(fig)
    xs = np.arange(len(goods))
    bw = 1 / (1 + 2.19)
    off = bw * (1 + 0.27) / 2
    ax.bar(xs - off, v2021, width=bw, color='#0070C0', zorder=3)
    ax.bar(xs + off, v2022, width=bw, color='#82ADD7', zorder=3)
    for x, v in zip(xs, v2021):
        val_label(ax, x - off, v, v, 5200, fs=9)
    for x, v in zip(xs, v2022):
        val_label(ax, x + off, v, v, 5200, fs=9)
    for x, d in zip(xs, diff):
        ax.text(x, (v2021[xs.tolist().index(x)] + v2022[xs.tolist().index(x)]) / 2,
                str(d), ha='center', va='center', fontsize=9,
                color='white', zorder=6)
    ax.set_xlim(-0.8, 4.8)
    ax.set_ylim(0, 5250)
    ax.set_xticks(xs)
    ax.set_xticklabels(goods, fontsize=10)
    ax.set_yticks([])
    ax.add_patch(Rectangle((0.04, 0.875), 0.028, 0.05, transform=ax.transAxes,
                           fc='#0070C0', ec='none'))
    ax.text(0.078, 0.90, '2021销量', transform=ax.transAxes, fontsize=10,
            color='white', ha='left', va='center')
    ax.add_patch(Rectangle((0.20, 0.875), 0.028, 0.05, transform=ax.transAxes,
                           fc='#82ADD7', ec='none'))
    ax.text(0.238, 0.90, '2022销量', transform=ax.transAxes, fontsize=10,
            color='white', ha='left', va='center')
    save('09_对比柱形图.png')


# ============ 10. 甘特图 ============
def chart10():
    import datetime as dt
    items = ['制定计划', '方案设计', '资源调配', '第一阶段', '第二阶段', '第三阶段', '项目总结']
    start = [44621, 44633, 44642, 44653, 44667, 44692, 44707]
    days = [11, 8, 10, 13, 24, 14, 7]
    pct = ['51%', '32%', '21%', '85%', '36%', '68%', '68%']
    base = dt.datetime(1899, 12, 30)
    d0 = base + dt.timedelta(days=44621)
    d1 = base + dt.timedelta(days=44726)
    fig = new_fig(8.86, 5.88)
    header(fig, '2022年化妆品类目采购项目进度')
    ax = plot_ax(fig, rect=(0.16, 0.12, 0.78, 0.70))
    y = np.arange(len(items), 0, -1)
    ax.barh(y, days, left=start, height=0.5, color='#0070C0', zorder=3)
    for yy, s, d, p in zip(y, start, days, pct):
        ax.text(s + d / 2, yy, p, ha='center', va='center', fontsize=9,
                color='white', zorder=5)
    ax.set_yticks(y)
    ax.set_yticklabels(items, fontsize=10)
    ax.set_xlim(44621, 44726)
    ax.set_ylim(0.4, len(items) + 0.8)
    ax.xaxis.set_ticks_position('top')
    ticks = range(44621, 44727, 15)
    ax.set_xticks(list(ticks))
    ax.set_xticklabels([f'{(base + dt.timedelta(days=t)).year}/'
                        f'{(base + dt.timedelta(days=t)).month}/'
                        f'{(base + dt.timedelta(days=t)).day}'
                        for t in ticks], fontsize=9)
    ax.tick_params(axis='x', colors='white', length=3)
    ax.tick_params(axis='y', colors='white', length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    save('10_甘特图.png')


# ============ 11. 平滑折线图 ============
def chart11():
    months = ['5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月', '1月', '2月', '3月']
    sales = [146, 198, 296, 412, 506, 615, 789, 1021, 3782, 3215, 2936]
    fig = new_fig(h=6.16)
    header(fig, '化妆品品类月度销量走势', '2022年销量迅速增加，1月最高，销量达到3782',
           '*注：数据来源于公司销售系统，统计日期截至2022.03.31')
    ax = plot_ax(fig)
    xs = np.arange(len(months))
    sx, sy = catmull_rom(xs, sales)
    ax.plot(sx, sy, color='#E66B4C', lw=2.2, zorder=3)
    peak = max(sales)
    pi = sales.index(peak)
    ax.text(pi, peak + 120, str(peak), ha='center', va='bottom', fontsize=9,
            color='white', zorder=5)
    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(0, 4200)
    ax.set_xticks(xs)
    ax.set_xticklabels(months, fontsize=10)
    ax.set_yticks([0, 1000, 2000, 3000, 4000])
    ax.grid(axis='y', **GRID)
    fig.text(0.402, 0.215, '2021', ha='center', va='center',
             fontsize=10, color='#D9D9D9')
    fig.text(0.803, 0.215, '2022', ha='center', va='center',
             fontsize=10, color='#D9D9D9')
    save('11_平滑折线图.png')


# ============ 12. 菱形走势图 ============
def chart12():
    months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月']
    rate = [0.536, 0.498, 0.527, 0.708, 0.609, 0.496, 0.586, 0.704]
    fig = new_fig(h=5.90)
    header(fig, '2022年1-8月公司计划完成率',
           '公司整体完成率55%，4月和8月超过70%，2月和6月较低未过半',
           '*注：数据来源于公司销售系统，统计日期截至2022.08.31')
    ax = plot_ax(fig, rect=(0.10, 0.178, 0.86, 0.661))
    xs = np.arange(len(months))
    ax.vlines(xs, 0, rate, color='#E74E69', lw=1.2, zorder=3)
    ax.plot(xs, rate, ls='none', marker='D', markersize=8,
            mfc=BG, mec='#E74E69', mew=1.2, zorder=4)
    for x, v in zip(xs, rate):
        ax.text(x, v + 0.08, f'{v:.2%}', ha='center', va='bottom',
                fontsize=9, color='white', zorder=5)
    ax.axhline(0, color='#A6A6A6', lw=1.0, zorder=2)
    ax.set_xlim(-0.6, 7.6)
    ax.set_ylim(0, 1.0)
    ax.set_xticks(xs)
    ax.set_xticklabels(months, fontsize=10)
    ax.set_yticks([])
    save('12_菱形走势图.png')


# ============ 13. 对比折线图 ============
def chart13():
    months = ['1月', '2月', '3月', '4月', '5月', '6月']
    v2021 = [1686, 1345, 1934, 1658, 1865, 1936]
    v2022 = [1385, 1846, 1654, 1936, 2564, 2236]
    fig = new_fig(h=6.22)
    header(fig, '2022年上半年各月同比去年销量',
           '上半年同比去年增长明显，5月份同比增长最多，增长近40%',
           '*注：数据来源于公司销售系统，统计日期截至2022.06.30')
    ax = plot_ax(fig)
    xs = np.arange(len(months))
    ax.plot(xs, v2021, color='#E74E69', lw=2.2, marker='o', ms=5.5,
            mfc='#E74E69', mec='#E74E69', zorder=4)
    ax.plot(xs, v2022, color='#0070C0', lw=2.2, marker='o', ms=5.5,
            mfc='#0070C0', mec='#0070C0', zorder=4)
    for x, v in zip(xs, v2021):
        ax.text(x, v + 60, str(v), ha='center', va='bottom', fontsize=8.5,
                color='white', zorder=5)
    for x, v in zip(xs, v2022):
        ax.text(x, v + 60, str(v), ha='center', va='bottom', fontsize=8.5,
                color='white', zorder=5)
    ax.set_xlim(-0.4, 5.4)
    ax.set_ylim(1000, 3100)
    ax.set_xticks(xs)
    ax.set_xticklabels(months, fontsize=10)
    ax.set_yticks([0, 500, 1000, 1500, 2000, 2500, 3000])
    ax.grid(axis='y', **GRID)
    ax.add_patch(Rectangle((0.82, 0.88), 0.025, 0.045, transform=ax.transAxes,
                           fc='#E74E69', ec='none'))
    ax.text(0.855, 0.902, '2021年', transform=ax.transAxes, fontsize=10,
            color='white', ha='left', va='center')
    ax.add_patch(Rectangle((0.82, 0.80), 0.025, 0.045, transform=ax.transAxes,
                           fc='#0070C0', ec='none'))
    ax.text(0.855, 0.822, '2022年', transform=ax.transAxes, fontsize=10,
            color='white', ha='left', va='center')
    save('13_对比折线图.png')


# ============ 14. 单值圆环图 ============
def chart14():
    fig = new_fig()
    header(fig, '2022年上半年目标完成率',
           '截至6月30日销售目标总体完成率达到85%',
           '*注：数据来源于公司销售系统')
    ax = fig.add_axes([0.29, 0.13, 0.45, 0.615])
    ax.set_facecolor(BG)
    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-1.15, 1.15)
    ax.set_aspect('equal')
    ax.axis('off')
    # 85% arc: gradient 7030A0 (top) -> E74E69 (bottom), Excel firstSliceAng=300
    start = 150.0
    sweep = 306.0
    n = 60
    seg = sweep / n
    for i in range(n):
        t0 = start + i * seg
        t1 = t0 + seg
        mid = np.radians((t0 + t1) / 2)
        t = (np.sin(mid) + 1) / 2
        col = '#{:02X}{:02X}{:02X}'.format(
            int(round(0x70 + (0xE7 - 0x70) * t)),
            int(round(0x30 + (0x4E - 0x30) * t)),
            int(round(0xA0 + (0x69 - 0xA0) * t)))
        ax.add_patch(Wedge((0, 0), 1.0, t0, t1, width=0.11,
                           facecolor=col, edgecolor='none', zorder=3))
    ax.add_patch(Wedge((0, 0), 1.0, start + sweep, start + 360, width=0.11,
                       facecolor='#313454', edgecolor='none', zorder=3))
    ax.text(0, 0.09, '85%', ha='center', va='center', fontsize=36,
            fontweight='bold', color='white', zorder=6)
    ax.text(0, -0.42, '目标完成率', ha='center', va='center', fontsize=10.5,
            color='white', zorder=6)
    save('14_单值圆环图.png')


# ============ 15. 水球图 ============
def chart15():
    fig = new_fig(3.75, 3.72)
    ax = fig.add_axes([0.01, 0.01, 0.98, 0.98])
    ax.set_facecolor(BG)
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.add_patch(Circle((0, 0), 1.0, facecolor='#0070C0', zorder=2))
    ax.add_patch(Rectangle((-1.05, 0.30), 2.1, 1.1, fc=BG, zorder=3))
    ax.add_patch(Circle((0, 0), 1.0, facecolor='none', edgecolor='#0070C0',
                        lw=2.6, zorder=4))
    ax.add_patch(Circle((0, 0), 0.92, facecolor='none', edgecolor='#0070C0',
                        lw=1.4, zorder=4))
    ax.text(0, 0, '65%', ha='center', va='center', fontsize=40,
            fontweight='bold', color='white', zorder=6)
    save('15_水球图.png')


if __name__ == '__main__':
    chart1()
    chart2()
    chart3()
    chart4()
    chart5()
    chart6()
    chart7()
    chart8()
    chart9()
    chart10()
    chart11()
    chart12()
    chart13()
    chart14()
    chart15()
    for f in FIG:
        plt.close(f)
    print('done:', len(FIG), 'charts ->', OUT)
