"""Seven data-driven chart functions, independent of Jupyter widgets."""
from pathlib import Path
from itertools import product
import json
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import colors, font_manager
from matplotlib.patches import Wedge

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT/'data'
MANIFEST = json.loads((DATA_DIR/'source_manifest.json').read_text(encoding='utf-8'))
STYLES = json.loads((DATA_DIR/'styles.json').read_text(encoding='utf-8'))
DEFAULTS = {int(k):v for k,v in MANIFEST['defaults'].items()}
NAMES = {1:'动态柱形图',2:'动态跑道图',3:'动态南丁格尔圆环图',4:'动态组合图',
         5:'透视表切片器',6:'VBA动态玉玦图',7:'动态滑珠图'}
for path in (ROOT/'assets/fonts').glob('*.otf'):
    font_manager.fontManager.addfont(str(path))
available = {f.name for f in font_manager.fontManager.ttflist}
FONT = next((f for f in ['Microsoft YaHei','微软雅黑','Noto Sans CJK SC','SimHei','PingFang SC'] if f in available),None)
if FONT is None:
    raise RuntimeError('缺少中文字体，请保留 assets/fonts 文件夹或安装微软雅黑。')
plt.rcParams.update({'font.family':FONT,'axes.unicode_minus':False,'figure.dpi':110,
                     'savefig.dpi':160,'axes.linewidth':.6,'svg.fonttype':'path'})
BG,WHITE,BLUE,PINK = '#1A1E43','#F2F2F2','#0070C0','#E74E69'
FILES={1:'01_monthly_sales.csv',2:'02_department_months.csv',3:'03_traffic_periods.csv',
       4:'04_products.csv',5:'05_hr_department_education.csv',6:'06_yujue_periods.csv',7:'07_region_months.csv'}


def load_data(number):
    return pd.read_csv(DATA_DIR/FILES[number],encoding='utf-8-sig')


def month_options(number=1):
    frame=load_data(number)
    return frame['月份'].tolist() if number==1 else frame.columns[1:].tolist()


def period_options(number):
    return load_data(number)['周期'].tolist()


def department_options():
    return sorted(load_data(5)['部门'].unique().tolist())


def row_values(number,key,column):
    frame=load_data(number)
    matches=frame.loc[frame[column]==key]
    if len(matches)!=1:raise ValueError(f'无效的 {column}：{key}')
    return frame.columns[1:].tolist(),matches.iloc[0,1:].to_numpy(dtype=float)


def hr_summary(departments=None):
    frame=load_data(5)
    if departments is not None:
        departments=list(departments)
        bad=set(departments)-set(frame['部门'])
        if bad:raise ValueError(f'未知部门：{sorted(bad)}')
        frame=frame.loc[frame['部门'].isin(departments)]
    if frame.empty:return pd.DataFrame(columns=['学历','平均月收入','人数'])
    grouped=frame.groupby('学历')[['人数','月收入合计']].sum()
    order=[x for x in MANIFEST['education_order'] if x in grouped.index]
    grouped=grouped.reindex(order)
    result=pd.DataFrame({'学历':order,'平均月收入':(grouped['月收入合计']/grouped['人数']).to_numpy(),
                         '人数':grouped['人数'].to_numpy()})
    total=pd.DataFrame([{'学历':'总计','平均月收入':frame['月收入合计'].sum()/frame['人数'].sum(),
                         '人数':int(frame['人数'].sum())}])
    return pd.concat([result,total],ignore_index=True)


def slider_values(axis,selection):
    frame=load_data(7)
    if axis=='月份':
        if selection not in frame.columns[1:]:raise ValueError('无效月份')
        labels=frame['区域'].tolist();values=frame[selection].to_numpy(float)
    elif axis=='区域':
        labels,values=row_values(7,selection,'区域')
    else:raise ValueError('axis 必须为“月份”或“区域”。')
    return labels,values


def make_canvas(number,bounds=None):
    fig=plt.figure(figsize=(6.4,4.45),facecolor=BG)
    if bounds is None:
        x,top,w,h=STYLES[str(number)]['plot']
        bounds=[x,1-top-h,w,h]
    ax=fig.add_axes(bounds,facecolor=BG)
    for spine in ax.spines.values():spine.set_visible(False)
    ax.tick_params(colors=WHITE,labelsize=9,length=0,pad=4)
    ax.set_axisbelow(True)
    return fig,ax


def headings(fig,title,state='',source='数据来源公司销售系统'):
    size=18 if len(title)<24 else 16
    fig.text(.062,.945,title,color=WHITE,fontsize=size,weight='bold',va='top')
    if state:fig.text(.062,.842,state,color=WHITE,fontsize=10,va='top')
    fig.text(.043,.045,'*注：'+source,color=WHITE,fontsize=7.5,va='bottom')


def category_axis(ax,labels,maximum,step=None,ylabels=True,grid=False):
    ax.set_xlim(-.5,len(labels)-.5);ax.set_ylim(0,maximum)
    ax.set_xticks(range(len(labels)),labels)
    if step:ax.set_yticks(np.arange(0,maximum+.01,step))
    if not ylabels:ax.set_yticks([])
    if grid:ax.yaxis.grid(True,color=WHITE,alpha=.20,lw=.5,ls=(0,(6,3)))
    ax.spines['bottom'].set_visible(True);ax.spines['bottom'].set_color((1,1,1,.3))


def labels_above(ax,x,values,size=9):
    for xi,value in zip(x,values):
        ax.annotate(f'{value:g}',(xi,value),xytext=(0,4),textcoords='offset points',
                    ha='center',va='bottom',fontsize=size,color=WHITE)


def circle_axis(ax):
    ax.set_aspect('equal');ax.set_xlim(-1.06,1.06);ax.set_ylim(-1.06,1.06);ax.axis('off')


def chart_1(month=None):
    month=month or DEFAULTS[1]['month'];labels,values=row_values(1,month,'月份')
    fig,ax=make_canvas(1)
    maximum=max(800,math.ceil(values.max()/200)*200)
    category_axis(ax,labels,maximum,200,grid=True)
    x=np.arange(len(labels));ax.bar(x,values,width=1/3.19,color='#0097E0',zorder=3)
    labels_above(ax,x,values)
    headings(fig,'2022年上半年各区域销售情况',f'月份：{month}')
    return fig


def chart_2(month=None):
    month=month or DEFAULTS[2]['month'];frame=load_data(2)
    if month not in frame.columns[1:]:raise ValueError('无效月份')
    values=frame[month].to_numpy(float);labels=frame['部门'].tolist()
    total=values.sum()
    if total<=0:raise ValueError('公司总人数必须大于零。')
    fig,ax=make_canvas(2,[.245,.13,.51,.65]);circle_axis(ax)
    palette=['#7030A0',BLUE,'#37A2DA','#11A7AD','#F5C353',PINK]
    hole=STYLES['2']['hole'];width=(1-hole)/len(labels)
    for i,(name,value,c) in enumerate(zip(labels,values,palette)):
        radius=hole+(i+1)*width
        ax.add_patch(Wedge((0,0),radius,90-360*value/(total/2),90,width=width-.008,facecolor=c,edgecolor='none'))
        ax.text(-.04,radius-width/2,f'{name}  {value:g}',ha='right',va='center',color=WHITE,fontsize=7.5)
    headings(fig,f'{month}公司总人数为{total:g}','各部门人数分布','数据来源公司人力资源系统')
    return fig


def chart_3(period=None):
    period=period or DEFAULTS[3]['period'];labels,values=row_values(3,period,'周期')
    if not np.isclose(values.sum(),1):raise ValueError('流量来源占比合计应为 100%。')
    fig,ax=make_canvas(3,[.29,.11,.42,.61]);circle_axis(ax)
    palette=['#4A5BD1','#6073F3','#11A7AD','#FFC000','#E66B4C']
    hole=STYLES['3']['hole'];start=90
    middles=90-(np.cumsum(values)-values/2)*360
    left=[i for i,a in enumerate(middles) if np.cos(np.deg2rad(a))<0]
    left_y=dict(zip(left,np.linspace(-.87,.92,len(left))))
    for i,(name,value,c) in enumerate(zip(labels,values,palette)):
        end=start-value*360;radius=hole+(1-hole)*value/values.max()
        ax.add_patch(Wedge((0,0),radius,end,start,width=radius-hole,facecolor=c,edgecolor=BG,lw=.4))
        angle=np.deg2rad((start+end)/2);side=1 if np.cos(angle)>=0 else -1
        label_y=left_y[i] if side<0 else np.clip(radius*np.sin(angle)*1.12,-.85,.85)
        ax.plot([radius*np.cos(angle),side*1.15,side*1.72],
                [radius*np.sin(angle),label_y,label_y],lw=.45,color=c,clip_on=False)
        ax.text(side*1.43,label_y+.035,f'{name}\n{value:.0%}',ha='center',va='bottom',
                color=WHITE,fontsize=8,linespacing=1.15,clip_on=False)
        start=end
    headings(fig,'2022年6月30日流量来源分布',f'统计周期：{period}','数据来源公司网站')
    return fig


def chart_4(sales=True,profit=True,margin=True):
    frame=load_data(4);values=frame['销售额'].to_numpy(float);profits=frame['利润'].to_numpy(float)
    if (values==0).any():raise ValueError('销售额为零时不能计算利润率。')
    fig,ax=make_canvas(4)
    maximum=max(4000,math.ceil(max(values.max(),profits.max())/1000)*1000)
    category_axis(ax,frame['商品'].tolist(),maximum,ylabels=False)
    x=np.arange(len(frame));handles=[];legend_names=[]
    if sales:
        bar=ax.bar(x-.13 if profit else x,values,width=.26,color=BLUE,zorder=3)
        labels_above(ax,x-.13 if profit else x,values);handles.append(bar);legend_names.append('销售额')
    if profit:
        bar=ax.bar(x+.13 if sales else x,profits,width=.26,color=PINK,zorder=3)
        labels_above(ax,x+.13 if sales else x,profits);handles.append(bar);legend_names.append('利润')
    if margin:
        right=ax.twinx();right.set_ylim(-1,1);right.set_yticks([])
        for spine in right.spines.values():spine.set_visible(False)
        rate=profits/values;line,=right.plot(x,rate,color='#FFC000',lw=1.5,marker='o',ms=4)
        for xi,r in zip(x,rate):
            right.annotate(f'{r:.0%}',(xi,r),xytext=(0,6),textcoords='offset points',
                           ha='center',va='bottom',color=WHITE,fontsize=9)
        handles.append(line);legend_names.append('利润率')
    if handles:
        legend=fig.legend(handles,legend_names,loc='upper right',bbox_to_anchor=(.95,.79),
                          frameon=False,ncol=3,fontsize=8,handlelength=1,columnspacing=1)
        for t in legend.get_texts():t.set_color(WHITE)
    else:ax.text(.5,.5,'请选择至少一个指标',transform=ax.transAxes,ha='center',color=WHITE,fontsize=13)
    headings(fig,'2022年化妆品销售情况')
    return fig


def chart_5(departments=None):
    # None 表示全部部门；空元组表示没有选择部门，二者不能混为一谈。
    summary=hr_summary(departments)
    fig,ax=make_canvas(5)
    selected='全部部门' if departments is None else ('、'.join(departments) if departments else '未选择部门')
    if summary.empty:
        ax.set_xticks([]);ax.set_yticks([])
        ax.text(.5,.5,'请选择部门',transform=ax.transAxes,ha='center',va='center',color=WHITE,fontsize=13)
    else:
        values=summary['平均月收入'].to_numpy(float);x=np.arange(len(summary))
        maximum=max(2500,math.ceil(values.max()*1.12/2500)*2500)
        category_axis(ax,summary['学历'].tolist(),maximum,ylabels=False)
        ramp=np.linspace(0,1,300)[:,None,None]
        c0,c1=np.array(colors.to_rgba('#00B0F0')),np.array(colors.to_rgba(BLUE))
        for xi,v in zip(x,values):
            ax.imshow(c0[None,None,:]*(1-ramp)+c1[None,None,:]*ramp,
                      extent=(xi-.16,xi+.16,0,v),origin='lower',aspect='auto',zorder=3)
            ax.annotate(f'{v:,.0f}',(xi,v),xytext=(0,4),textcoords='offset points',
                        ha='center',va='bottom',color=WHITE,fontsize=9)
    if len(selected)>32:selected=selected[:29]+'…'
    headings(fig,'各学历平均工资情况',f'部门：{selected}',
             '数据来源于人力资源管理系统，统计日期截至2022.03.31')
    return fig


def chart_6(period=None):
    period=period or DEFAULTS[6]['period'];labels,values=row_values(6,period,'周期')
    if ((values<0)|(values>.5)).any():raise ValueError('玉玦图源模板基准为 50%，输入须介于 0 和 50%。')
    fig,ax=make_canvas(6,[.24,.11,.49,.64]);circle_axis(ax)
    palette=['#00B0F0','#11A7AD','#FFC000',PINK]
    hole=STYLES['6']['hole'];width=(1-hole)/len(labels)
    for i,(name,v,c) in enumerate(zip(labels,values,palette)):
        radius=hole+(i+1)*width;end=90-v/.5*360
        ax.add_patch(Wedge((0,0),radius,end,90,width=width-.009,facecolor=c,edgecolor='none'))
        ax.text(-.05,radius-width/2,name,ha='right',va='center',fontsize=8,color=WHITE)
        angle=np.deg2rad(end)
        ax.text((radius+.07)*np.cos(angle),(radius+.07)*np.sin(angle),f'{v:.0%}',
                ha='center',va='center',fontsize=8,color=WHITE)
    headings(fig,'流量来源分布',f'统计周期：{period}','数据来源公司网站')
    return fig


def chart_7(axis='月份',selection=None):
    if selection is None:selection='1月' if axis=='月份' else load_data(7)['区域'].iloc[0]
    labels,values=slider_values(axis,selection)
    if ((values<0)|(values>1)).any():raise ValueError('完成率必须介于 0 与 1 之间。')
    fig,ax=make_canvas(7)
    ax.set_xlim(0,1);ax.set_ylim(-.5,len(labels)-.5)
    ax.set_xticks([]);ax.set_yticks(range(len(labels)),labels);ax.tick_params(axis='y',pad=8)
    for j,v in enumerate(values):
        ax.plot([0,1],[j,j],lw=10,color=(1,1,1,.33),solid_capstyle='round',clip_on=False)
        ax.plot([0,v],[j,j],lw=10,color=BLUE,solid_capstyle='round',clip_on=False)
        ax.scatter([v],[j],s=15**2,color=BLUE,edgecolors='none',zorder=5)
        ax.text(max(.035,v-.045),j,f'{v:.1%}',ha='right',va='center',color=WHITE,fontsize=9,zorder=6)
    headings(fig,'2022年上半年区域销量目标达成率情况',f'按{axis}查看：{selection}',
             '数据来源公司销售系统，日期截至2022.06.30')
    return fig


FUNCTIONS={1:chart_1,2:chart_2,3:chart_3,4:chart_4,5:chart_5,6:chart_6,7:chart_7}


def state_options(number):
    """有限状态用于离线 HTML 预览，Notebook 部门筛选另支持任意多选。"""
    if number==1:return [(m,{'month':m}) for m in month_options(1)]
    if number==2:return [(m,{'month':m}) for m in month_options(2)]
    if number in (3,6):return [(p,{'period':p}) for p in period_options(number)]
    if number==4:
        result=[]
        for flags in product([False,True],repeat=3):
            names=[s for s,on in zip(['销售额','利润','利润率'],flags) if on]
            result.append((' + '.join(names) or '全部隐藏',dict(zip(['sales','profit','margin'],flags))))
        return result
    if number==5:return [('全部部门',{'departments':None})]+[(d,{'departments':[d]}) for d in department_options()]
    if number==7:
        frame=load_data(7)
        return [(f'月份 · {m}',{'axis':'月份','selection':m}) for m in frame.columns[1:]]+[
            (f'区域 · {r}',{'axis':'区域','selection':r}) for r in frame['区域']]
    raise ValueError('图号应为 1—7。')
