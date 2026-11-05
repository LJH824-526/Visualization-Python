"""逐项对照用户提供的教材PPT，使用真实Superstore指标绘制30幅模板。

T编号是本项目选编序号，不冒充教材图号。原图页码、图块及设计细节见template_mapping.csv。
"""
from pathlib import Path
from io import BytesIO
import json, math, html
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Circle, Wedge, Polygon, PathPatch
from matplotlib.path import Path as MPath
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap
from matplotlib import font_manager
from .pipeline import ROOT
from .visuals import REG,CAT,SEG,SUB

OUT=ROOT/'outputs/templates';TABLE=ROOT/'outputs/tables';REF=ROOT/'assets/reference'
BG='#1A1E43';WHITE='#FFFFFF';GRAY='#74758E';GRID='#414563'
BLUE='#188EFC';DEEP='#0070C0';CYAN='#62C7D8';PINK='#E74E69';YELLOW='#F5C353';TEAL='#11A7AD';PURPLE='#5130CD'
PALETTE=[PINK,YELLOW,TEAL,DEEP,CYAN,PURPLE]

# 原图图块从上到下、从左到右编号。对应原始shape_id保存在源索引。
SPECS=[
 (18,1,'基础条形图','2021年区域销售额分布','条末原值标签；隐藏网格和图例'),
 (18,2,'分组条形图','区域年度销售额对比','蓝红两组条形；右侧图例；条末标签'),
 (18,3,'背景进度条','近四年销售额对比','等长灰轨道；蓝色实值条；内置白标签'),
 (18,4,'甘特区间图','订单下单至发货的日期区间','顶部日期轴；纵向虚线；条内天数'),
 (18,5,'分段信息条','区域销售额及同比变化','蓝灰比较条；右侧红色同比信息块'),
 (18,6,'子弹目标图','区域销售与上年基线比较','灰色轨道；蓝色实值；白色基线标记'),
 (18,7,'蝴蝶对比图','区域年度销售额镜像对比','左蓝右红；区域居中；年度置顶'),
 (18,8,'棒棒糖图','区域综合利润率','青色细线与圆点；百分比标签'),
 (18,9,'阶梯漏斗图','2021年客户价值筛选过程','居中矩形；层间虚线；逐层转化比例'),
 (18,10,'梯形漏斗图','2021年客户价值筛选漏斗','彩色梯形连接；右侧人数和条件'),
 (18,11,'圆角进度条','各区域未标记退货的订单占比','圆角灰轨道；蓝条；空心终点'),
 (18,14,'分面条形图','2021年一季度子品类销售额','三列小面板；粉紫橙配色；条内值'),
 (18,20,'均值参照柱形图','2021年主要子品类销售额','蓝色柱；金色均值线；柱顶数值'),
 (20,1,'细线渐变环','技术产品销售额占比','细渐变环；灰底环；中心粗体百分比'),
 (20,2,'粗线渐变环','A类商品的累计销售贡献','粗渐变环；中心百分比；下方指标名'),
 (20,3,'圆头进度环','个人消费者销售贡献','蓝灰环；圆形端点；中心百分比'),
 (20,4,'扇区填充进度环','2021年销售额占全期比例','半透明扇区；外圈蓝色进度；中心数值'),
 (20,5,'嵌套累计圆环','区域销售累计占比','多层彩色圆弧；标签列；270度为全量刻度'),
 (20,6,'同心排名圆弧','前六子品类销售额排行','内外多环；粉黄青紫配色；上方分类标签'),
 (20,7,'南丁格尔玫瑰图','主要子品类销售份额','彩色极面积扇区；外侧折线标签和圆点'),
 (20,8,'错位圆环图','区域销售额构成','紫蓝青黄扇区；错位半径；外侧引导线'),
 (20,10,'双层旭日图','品类与子品类销售构成','内层大类；外层子类；中心销售合计'),
 (20,11,'半圆仪表图','高价值活跃客户占比','半圆蓝灰粗环；中心百分比'),
 (22,6,'渐变面积图','2021年月度销售额趋势','蓝色垂直渐变；面积轮廓；点上数字'),
 (22,9,'双圈水球图','全期未标记退货的订单占比','蓝色平水面；双描边圆；中心百分比'),
 (22,10,'波浪水球图','技术产品销售额占比','青色正弦水面；双圈；中心大数字'),
 (22,3,'发光标记折线图','2021年前八个月销售趋势','蓝色折线；青色圆点与光晕；点上标签'),
 (22,5,'分层多线趋势图','近三年月度销售额对比','三条错层曲线；红黄蓝；直接年份标签'),
 (24,6,'柱线组合图','区域销售额及同比增长','蓝红分组柱；黄色同比折线；右下图例'),
 (24,11,'条形气泡组合图','区域销售额与同比增长','粉色水平条；右侧蓝气泡；气泡内增长率'),
]

def init_font():
    plt.rcdefaults()
    for f in (ROOT/'assets/fonts').glob('*.otf'):font_manager.fontManager.addfont(str(f))
    available={f.name for f in font_manager.fontManager.ttflist}
    family=next(n for n in ['Course Report Sans','Noto Sans CJK SC','Microsoft YaHei','SimHei'] if n in available)
    plt.rcParams.update({'font.family':family,'font.size':11,'axes.unicode_minus':False,'text.color':WHITE,
        'axes.labelcolor':WHITE,'xtick.color':WHITE,'ytick.color':WHITE,'axes.edgecolor':GRAY,'figure.facecolor':BG,
        'axes.facecolor':BG,'savefig.facecolor':BG})

def base(title,subtitle,source,unit='金额单位 万USD'):
    fig=plt.figure(figsize=(10,7.48),dpi=200,facecolor=BG)
    fig.text(.055,.935,title,size=21,weight='bold',color=WHITE,va='top')
    fig.text(.055,.855,subtitle,size=12.2,color=WHITE,va='top')
    fig.text(.055,.035,f'数据 Superstore官方教学样例  截至2021年12月30日  {unit}',size=9.2,color='#D2D4E0')
    return fig

def axes(fig,rect=(.15,.15,.75,.60),off=True):
    ax=fig.add_axes(rect)
    if off:ax.set_axis_off()
    else:
        ax.spines[['top','right','left']].set_visible(False);ax.tick_params(length=0,pad=8,labelsize=10)
        ax.grid(axis='y',ls=':',color=GRID,alpha=.7);ax.set_axisbelow(True)
    return ax

def draw_h(ax,values,labels,color=BLUE,labels_inside=False):
    x=np.arange(len(values));ax.barh(x,values,height=.42,color=color)
    ax.set_ylim(len(values)-.4,-.6);ax.set_xlim(0,max(values)*1.19)
    for i,(v,label) in enumerate(zip(values,labels)):
        ax.text(-max(values)*.035,i,label,ha='right',va='center',size=11)
        ax.text(v*.98 if labels_inside else v+max(values)*.025,i,f'{v:,.1f}',ha='right' if labels_inside else 'left',va='center',size=10)

def save(fig,idx,name):
    path=OUT/f'tpl{idx:02d}_{name}.png';buf=BytesIO();fig.savefig(buf,format='png',dpi=200);plt.close(fig)
    tmp=path.with_suffix('.png.tmp');tmp.write_bytes(buf.getvalue());tmp.replace(path);return path

def ring(ax,value,width=.12,gradient=False,roundcap=False,fill=False,thin=False):
    ax.set_aspect('equal');ax.set_xlim(-1.3,1.3);ax.set_ylim(-1.25,1.25)
    ax.add_patch(Wedge((0,0),1,0,360,width=width,color=GRAY,alpha=.45))
    if fill:
        ax.add_patch(Wedge((0,0),.93,90-value*360,90,color=BLUE,alpha=.24))
    if gradient:
        cmap=LinearSegmentedColormap.from_list('ring',['#0070FF','#5440CB','#E74E69','#FF7880'])
        ts=np.linspace(np.pi/2,np.pi/2-value*2*np.pi,500)
        points=np.c_[np.cos(ts)*(1-width/2),np.sin(ts)*(1-width/2)]
        segs=np.stack([points[:-1],points[1:]],axis=1)
        lc=LineCollection(segs,colors=cmap(np.linspace(0,1,len(segs))),linewidth=2 if thin else 14)
        ax.add_collection(lc)
    else:ax.add_patch(Wedge((0,0),1,90-value*360,90,width=width,color=DEEP))
    if roundcap:
        t=np.pi/2-value*2*np.pi;r=1-width/2
        for ang in [np.pi/2,t]:ax.add_patch(Circle((r*np.cos(ang),r*np.sin(ang)),width/2,color=DEEP))
    ax.text(0,.03,f'{value:.1%}',ha='center',va='center',size=33,weight='bold')

def leaders(ax,ang,r,label,value,color,rad=1.35):
    x,y=np.cos(ang),np.sin(ang);side=1 if x>=0 else -1
    xy=(x*r,y*r);p=(x*(r+.18),y*(r+.18));end=(side*rad,p[1])
    ax.plot([xy[0],p[0],end[0]],[xy[1],p[1],end[1]],color=color,lw=.8)
    ax.scatter(*xy,s=22,color=color,zorder=4)
    ax.text(end[0],end[1]+.045,f'{label}\n{value:.1%}',color=color,size=10,ha='left' if side==1 else 'right',va='bottom')

def create_templates(z):
    init_font();OUT.mkdir(parents=True,exist_ok=True);d=z['d'];recent=d[d.Year==2021]
    reg=recent.groupby('Region').Sales.sum().reindex(['West','East','Central','South'])/1e4
    prev=d[d.Year==2020].groupby('Region').Sales.sum().reindex(reg.index)/1e4
    labels=[REG[i] for i in reg.index];growth=reg/prev-1
    m=recent.groupby('Month').Sales.sum()/1e4
    sc=recent.groupby('Sub-Category').Sales.sum().sort_values(ascending=False)/1e4
    cat=d.groupby('Category').Sales.sum();share_tech=cat['Technology']/cat.sum()
    r=z['rfm'];nested=[d['Customer ID'].nunique(),len(r),int(((r.F_high==1)&(r.M_high==1)).sum()),int((r.Code=='111').sum())]
    funnel_labels=['历史全部客户','2021年有交易','高频且高额','高价值活跃']
    all_nr=1-z['summary']['returned_order_share'];rows=[];inputs=[]
    def output(fig,idx,metric,values,adaptation='',legend='无图例 采用直接标签'):
        page,no,typ,title,detail=SPECS[idx-1];path=save(fig,idx,typ)
        reference=next(REF.glob(f'p{page:02d}_{no:02d}.*')).name
        rows.append({'编号':f'T{idx:02d}','模板名称':typ,'PPT页码':page,'页内图块':f'{no:02d}',
            '参考图片':reference,'复现图片':path.name,'业务标题':title,'指标口径':metric,
            '布局结构':detail,'配色方案':'背景#1A1E43 蓝#188EFC 红#E74E69 青#62C7D8 黄#F5C353',
            '标签样式':'白色数值 直接标注 指标保留1位小数或百分比','图例位置':legend,
            '标题设计':'左上白色粗体主标题 其下白色副标题 左下来源及单位','适配说明':adaptation or '以Superstore指标替换原模板样例值，保持主要图形结构'})
        inputs.append({'template':f'T{idx:02d}','metric':metric,'values':values})
    def b(i,sub,unit='金额单位 万USD'):return base(SPECS[i-1][3],sub,f'T{i:02d}',unit)

    f=b(1,'西部销售额最高 各区域采用统一金额刻度');ax=axes(f);draw_h(ax,reg.values,labels);output(f,1,'2021年按Region汇总Sales/10000',reg.to_dict())
    f=b(2,'蓝色为2021年 红色为2020年 基期口径一致');ax=axes(f,off=False);y=np.arange(4)
    ax.barh(y-.18,reg,.32,color=DEEP,label='2021年');ax.barh(y+.18,prev,.32,color='#E70014',label='2020年');ax.set_yticks(y,labels);ax.invert_yaxis();ax.set_xlim(0,max(reg.max(),prev.max())*1.24);ax.grid(False)
    for i,(v,w) in enumerate(zip(reg,prev)):ax.text(v+.25,i-.18,f'{v:.1f}',va='center',size=9);ax.text(w+.25,i+.18,f'{w:.1f}',va='center',size=9)
    ax.legend(loc='center right',bbox_to_anchor=(1.10,.5),frameon=False,labelcolor='white',fontsize=9);output(f,2,'各Region的2021与2020年Sales',{'2021':reg.to_dict(),'2020':prev.to_dict()},legend='绘图区右侧中部')
    yearly=z['annual'].Sales.iloc[::-1]/1e4;f=b(3,'灰条以最大年度销售额为参照 不代表预算目标');ax=axes(f);y=np.arange(4)
    ax.barh(y,np.repeat(yearly.max(),4),.45,color=GRAY);ax.barh(y,yearly,.45,color=DEEP)
    for i,(year,v) in enumerate(yearly.items()):ax.text(-yearly.max()*.035,i,f'{year}年',ha='right',va='center');ax.text(v*.5,i,f'{v:.1f}',ha='center',va='center')
    ax.set_ylim(3.5,-.5);ax.set_xlim(0,yearly.max()*1.08);output(f,3,'按Year汇总Sales/10000',yearly.to_dict(),'原图五年改为数据实际覆盖的四年；轨道是样本最大年度值')
    orders=recent.groupby('Order ID').agg(Start=('Order Date','min'),End=('Ship Date','max')).sort_values(['Start','End']).head(7)
    f=b(4,'展示2021年最早七个订单的下单至发货区间','单位 日期与天数');ax=axes(f,(.24,.16,.67,.57),off=False);ax.grid(axis='x',color=GRID,ls=':');ax.grid(axis='y',visible=False)
    for i,(oid,row) in enumerate(orders.iterrows()):
        days=(row.End-row.Start).days;ax.barh(i,days,left=mdates.date2num(row.Start),height=.56,color=DEEP);ax.text(mdates.date2num(row.Start)+days/2,i,f'{days}天',ha='center',va='center',size=9)
    ax.set_yticks(range(7),[s[-6:] for s in orders.index]);ax.invert_yaxis();ax.xaxis.tick_top();ax.xaxis.set_major_locator(mdates.DayLocator(interval=2));ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'));ax.spines['bottom'].set_visible(False)
    output(f,4,'按Order ID取最早Order Date与最晚Ship Date',orders.astype(str).to_dict('index'),'以真实订单日期和发货天数替换虚构项目进度，不伪造完成率')
    f=b(5,'左侧为本期与上期金额 右侧独立显示同比率');ax=axes(f);y=np.arange(4);total=reg+prev;end=total.max()*1.03;box=total.max()*.20
    ax.barh(y,reg,.53,color=DEEP);ax.barh(y,prev,.53,left=reg,color='#80B0D4');ax.barh(y,np.repeat(box,4),.53,left=end,color=PINK)
    for i in range(4):ax.text(-total.max()*.035,i,labels[i],ha='right',va='center');ax.text(reg.iloc[i]/2,i,f'{reg.iloc[i]:.1f}',ha='center',va='center');ax.text(end+box/2,i,f'{growth.iloc[i]:+.1%}',ha='center',va='center',size=10)
    ax.set_xlim(0,end+box*1.15);ax.set_ylim(3.5,-.5);output(f,5,'2021与2020年区域销售额并列分段 同比单独成块',{'2021':reg.to_dict(),'2020':prev.to_dict(),'YoY':growth.to_dict()},'红色块长度固定，仅承载同比文本，不作为第三项可加金额')
    f=b(6,'白色标记是2020年销售基线 并非虚构预算目标');ax=axes(f);y=np.arange(4);limit=max(reg.max(),prev.max())*1.12
    ax.barh(y,np.repeat(limit,4),.38,color=GRAY,alpha=.55);ax.barh(y,reg,.38,color='#4E8FFB')
    for i in range(4):ax.plot([prev.iloc[i],prev.iloc[i]],[i-.14,i+.14],color='white',lw=2);ax.text(reg.iloc[i]*.45,i,f'{reg.iloc[i]:.1f}',ha='center',va='center');ax.text(limit*1.03,i,f'{reg.iloc[i]/prev.iloc[i]:.0%}',va='center');ax.text(-limit*.035,i,labels[i],ha='right',va='center')
    ax.set_ylim(3.5,-.5);ax.set_xlim(0,limit*1.2);output(f,6,'2021Sales与2020Sales基线之比',{'current':reg.to_dict(),'baseline':prev.to_dict()},'目标字段不存在，改用明确标识的上年实际基线；比例可超过100%')
    f=b(7,'左侧2021年 右侧2020年 左右独立显示正金额');ax=axes(f,(.10,.16,.80,.59));lim=max(reg.max(),prev.max())*1.3
    for i in range(4):
        ax.barh(i,-reg.iloc[i],.43,left=-lim*.08,color=DEEP);ax.barh(i,prev.iloc[i],.43,left=lim*.08,color=PINK)
        ax.text(0,i,labels[i],ha='center',va='center');ax.text(-reg.iloc[i]/2-lim*.08,i,f'{reg.iloc[i]:.1f}',ha='center',va='center');ax.text(prev.iloc[i]/2+lim*.08,i,f'{prev.iloc[i]:.1f}',ha='center',va='center')
    ax.text(-lim*.6,-.8,'2021年',ha='center',color=BLUE);ax.text(lim*.6,-.8,'2020年',ha='center',color=PINK);ax.set_xlim(-lim,lim);ax.set_ylim(3.6,-1)
    output(f,7,'2021与2020区域Sales镜像排布',{'2021':reg.to_dict(),'2020':prev.to_dict()},'左侧条向左延伸只为镜像布局，不表示负销售额',legend='绘图区上方左右年度标签')
    margins=d.groupby('Region').Profit.sum()/d.groupby('Region').Sales.sum();margins=margins.reindex(reg.index)
    f=b(8,'综合利润率按利润总额除以销售总额计算','单位 %');ax=axes(f)
    for i,v in enumerate(margins):ax.plot([0,v*100],[i,i],color=CYAN,lw=2);ax.scatter(v*100,i,s=80,color=CYAN);ax.text(v*100,i-.22,f'{v:.1%}',ha='center',size=10);ax.text(-.7,i,labels[i],ha='right',va='center')
    ax.set_xlim(0,20);ax.set_ylim(3.6,-.7);output(f,8,'全期各区域sum(Profit)/sum(Sales)',margins.to_dict())
    f=b(9,'逐层附加筛选条件 这是静态人群筛选 并非实际触达转化','单位 客户数 人');ax=axes(f,(.10,.15,.80,.59));yy=np.arange(4)
    for i,v in enumerate(nested):
        ax.barh(i,v,.52,left=-v/2,color=PALETTE[i]);ax.text(0,i,f'{v}',ha='center',va='center',size=15,weight='bold');ax.text(-nested[0]*.57,i,funnel_labels[i],ha='right',va='center',size=10)
        if i<3:ax.plot([-nested[0]/2,nested[0]/2],[i+.5,i+.5],color=GRID,ls='--',lw=.7);ax.text(-nested[0]*.4,i+.58,f'{nested[i+1]/v:.1%}',size=8)
    ax.set_xlim(-nested[0]*.75,nested[0]*.65);ax.set_ylim(3.65,-.6);output(f,9,'历史客户→当年客户→高F高M→高F高M高R',dict(zip(funnel_labels,nested)),'层层集合包含，转化标签仅表示筛选保留比例，不冒充招聘或电商浏览转化')
    f=b(10,'四层条件严格包含 各层宽度与真实人数成正比','单位 客户数 人');ax=axes(f,(.10,.15,.80,.59))
    for i,v in enumerate(nested):
        nxt=nested[i+1] if i<3 else v*.72
        ax.add_patch(Polygon([[-v/2,i],[v/2,i],[nxt/2,i+.95],[-nxt/2,i+.95]],color=PALETTE[i],ec='none'))
        ax.text(0,i+.42,str(v),ha='center',va='center',weight='bold',size=13);ax.text(nested[0]*.6,i+.42,funnel_labels[i],size=10,va='center')
    ax.set_xlim(-nested[0]*.6,nested[0]*.97);ax.set_ylim(4.15,-.2);output(f,10,'与T09相同的嵌套客户集合',dict(zip(funnel_labels,nested)),'末层尾部收窄用于梯形造型；末层的定量宽度取顶部，人数字标为实际值')
    of=d.groupby(['Region','Order ID']).Returned.max();nr=(1-of.groupby('Region').mean()).reindex(reg.index)
    f=b(11,'仅代表订单未被标记退货 不等于客户满意度','单位 %');ax=axes(f)
    for i,v in enumerate(nr):ax.plot([0,1],[i,i],color=GRAY,lw=20,solid_capstyle='round');ax.plot([0,v],[i,i],color=DEEP,lw=20,solid_capstyle='round');ax.scatter(v,i,s=130,facecolor=DEEP,edgecolor='white',zorder=5);ax.text(v*.5,i,f'{v:.1%}',ha='center',va='center',size=11);ax.text(-.065,i,labels[i],ha='right',va='center')
    ax.set_xlim(-.04,1.13);ax.set_ylim(3.65,-.65);output(f,11,'1减去各区域退货订单数/区域订单数',nr.to_dict(),'用真实未标记退货占比替代不存在的目标完成率')
    chosen=sc.head(6).index;quarter=recent[recent['Order Date'].dt.month<=3].pivot_table(index='Sub-Category',columns='Month',values='Sales',aggfunc='sum',fill_value=0).reindex(chosen)/1e3
    f=b(12,'同一组子品类在1至3月的真实金额采用同一横向尺度','金额单位 千USD');mx=quarter.to_numpy().max()*1.25
    for j,col in enumerate(quarter.columns):
        ax=axes(f,(.18+j*.25,.16,.20,.57));vals=quarter[col].values;ax.barh(np.arange(6),vals,.48,color=[PINK,'#5450C8','#F5A877'][j]);ax.set_xlim(0,mx);ax.set_ylim(5.5,-.8)
        ax.text(mx*.5,-.85,col[5:]+'月',ha='center',color='white',size=11)
        for i,v in enumerate(vals):ax.text(v*.5 if v>mx*.18 else v+mx*.035,i,f'{v:.1f}',ha='center' if v>mx*.18 else 'left',va='center',size=9)
        if j==0:
            for i,c in enumerate(chosen):ax.text(-mx*.08,i,SUB[c],ha='right',va='center',size=10)
    output(f,12,'2021年一季度选定6个子品类按月汇总Sales/1000',quarter.to_dict(),'各分面横轴上限相同，避免面板各自缩放导致错误比较',legend='分面顶部月份标签')
    vals=sc.head(6);f=b(13,'金色水平线为这六个子品类的销售均值');ax=axes(f,(.12,.16,.80,.59),off=False);ax.bar(np.arange(6),vals,color=DEEP,width=.48);ax.axhline(vals.mean(),color=YELLOW,lw=1.4)
    ax.text(5.4,vals.mean()*1.03,f'均值 {vals.mean():.1f}',color=YELLOW,ha='right',size=9);ax.set_xticks(range(6),[SUB[s] for s in vals.index]);ax.set_ylim(0,vals.max()*1.25)
    for i,v in enumerate(vals):ax.text(i,v+.2,f'{v:.1f}',ha='center',size=10)
    output(f,13,'2021Sales最高6个子品类及算术均值',vals.to_dict())
    f=b(14,'全期技术产品销售额除以全期总销售额','指标 占总销售额比例');ax=axes(f,(.14,.13,.72,.60));ring(ax,share_tech,width=.025,gradient=True,thin=True);ax.text(0,-.25,'销售额占比',ha='center',size=12);output(f,14,'Technology Sales / all Sales',float(share_tech))
    av=float(z['abc_summary'].loc[z['abc_summary'].ABC.eq('A'),'Sales Share'].iloc[0]);f=b(15,'414个A类商品贡献约八成销售额','指标 A类销售占比');ax=axes(f,(.14,.13,.72,.60));ring(ax,av,width=.12,gradient=True);ax.text(0,-.27,'A类销售贡献',ha='center',size=12);output(f,15,'ABC中A类商品Sales / all Sales',av)
    consumer=float(d.loc[d.Segment.eq('Consumer'),'Sales'].sum()/d.Sales.sum());f=b(16,'个人消费者客群的销售额占全期总额比例','指标 个人消费者销售占比');ax=axes(f,(.14,.13,.72,.60));ring(ax,consumer,width=.12,roundcap=True);output(f,16,'Consumer Sales / all Sales',consumer)
    yrshare=float(recent.Sales.sum()/d.Sales.sum());f=b(17,'扇形和外圈使用同一份额指标','指标 2021销售占全期比例');ax=axes(f,(.14,.13,.72,.60));ring(ax,yrshare,width=.018,fill=True);output(f,17,'2021Sales / 全期Sales',yrshare)
    allreg=d.groupby('Region').Sales.sum().sort_values();shares=allreg/allreg.sum();cum=shares.cumsum()
    f=b(18,'由内向外累计各区域销售份额 270度对应100%','指标 累计销售占比');ax=axes(f,(.13,.12,.74,.61));ax.set_aspect('equal');ax.set_xlim(-1.55,1.55);ax.set_ylim(-1.3,1.3)
    for i,((key,v),cv) in enumerate(zip(shares.items(),cum)):
        radius=.48+i*.16;ax.add_patch(Wedge((0,0),radius,90-270*cv,90,width=.13,color=[DEEP,TEAL,YELLOW,PINK][i]));ax.text(-.12,1.1-i*.14,f'{REG[key]} 累计{cv:.1%}',ha='right',size=9)
    output(f,18,'按区域销售升序累积Sales份额',cum.to_dict(),'原模板嵌套圆环改为可解释的累计份额，270度为100%的明确刻度；不是独立占比环')
    vals=sc.head(6);f=b(19,'圆弧按第一名归一 270度对应最大值','金额单位 万USD');ax=axes(f,(.12,.12,.76,.61));ax.set_aspect('equal');ax.set_xlim(-1.5,1.5);ax.set_ylim(-1.3,1.4)
    for i,((key,v),color) in enumerate(zip(vals.items(),PALETTE)):
        rad=1.1-i*.12;ax.add_patch(Wedge((0,0),rad,90-270*v/vals.max(),90,width=.09,color=color));ax.text(-.025,rad-.05,f'{SUB[key]} {v:.1f}',ha='right',va='center',size=8.5)
    output(f,19,'2021销售额最高6个子品类金额/最大值',vals.to_dict(),'只用弧长表达相对值，半径排列用于区分类别，不声称扇区面积是销售份额')
    vals=sc.head(5);part=vals/vals.sum();f=b(20,'等角扇区面积与五个子品类销售额成正比','指标 五个子品类内部销售份额');ax=axes(f,(.11,.12,.78,.62));ax.set_aspect('equal');ax.set_xlim(-1.9,1.9);ax.set_ylim(-1.5,1.5)
    for i,((key,v),color) in enumerate(zip(part.items(),PALETTE)):
        a1=90-(i+1)*72;a2=90-i*72;rad=.55+.65*np.sqrt(v/part.max());ax.add_patch(Wedge((0,0),rad,a1,a2,color=color,ec=BG,lw=.5))
        # 内部半径为0，半径取sqrt份额；无额外基底项，确保面积定量准确。
        ax.patches[-1].set_radius(1.25*np.sqrt(v/part.max()))
        leaders(ax,np.deg2rad((a1+a2)/2),1.25*np.sqrt(v/part.max()),SUB[key],v,color,rad=1.45)
    output(f,20,'2021销售额最高5个子品类的内部份额',part.to_dict(),'保留彩色扇区和引导线，采用等角且半径为sqrt份额的极面积编码，避免面积误导')
    vals=d.groupby('Region').Sales.sum().reindex(reg.index);part=vals/vals.sum();f=b(21,'引导线给出各区域份额 扇区角度保持金额比例','指标 区域销售占比');ax=axes(f,(.10,.12,.80,.62));ax.set_aspect('equal');ax.set_xlim(-1.85,1.85);ax.set_ylim(-1.5,1.5);angle=90
    for i,((key,v),color) in enumerate(zip(part.items(),[PURPLE,'#6272F5',CYAN,YELLOW])):
        end=angle-v*360;rad=1.08-i*.075;ax.add_patch(Wedge((0,0),rad,end,angle,width=rad-.58,color=color));leaders(ax,np.deg2rad((angle+end)/2),rad+.05,REG[key],v,color,rad=1.4);angle=end
    output(f,21,'全期各区域Sales / all Sales',part.to_dict(),'不同外半径保留原模板错位造型；比例以扇区角度和标注数值读取')
    ct=d.groupby('Category').Sales.sum();f=b(22,'内层为品类 外层为子品类 面积层级通过角度对应','金额单位 万USD');ax=axes(f,(.14,.12,.72,.62));ax.set_aspect('equal');ax.set_xlim(-1.25,1.25);ax.set_ylim(-1.25,1.25);angle=90
    for ci,(catkey,cv) in enumerate(ct.items()):
        end=angle-360*cv/ct.sum();color=[PINK,YELLOW,'#175479'][ci];ax.add_patch(Wedge((0,0),.68,end,angle,width=.27,color=color,ec=BG,lw=.7));ang=(angle+end)/2;ax.text(.53*np.cos(np.deg2rad(ang)),.53*np.sin(np.deg2rad(ang)),CAT[catkey],ha='center',va='center',size=10,color=BG if ci==1 else WHITE)
        subs=d[d.Category.eq(catkey)].groupby('Sub-Category').Sales.sum();cursor=angle
        for sj,(sk,sv) in enumerate(subs.items()):
            en=cursor-360*sv/ct.sum();ax.add_patch(Wedge((0,0),1,en,cursor,width=.31,color=color,alpha=.65+sj/len(subs)*.3,ec=BG,lw=.7));an=(cursor+en)/2
            if sv/ct.sum()>.02:ax.text(.84*np.cos(np.deg2rad(an)),.84*np.sin(np.deg2rad(an)),SUB[sk],ha='center',va='center',size=7,rotation=an-90,color=BG if ci==1 else WHITE)
            cursor=en
        angle=end
    ax.text(0,0,f'{d.Sales.sum()/1e4:.1f}\n销售合计',ha='center',va='center',weight='bold',size=16);output(f,22,'全期Category与Sub-Category层级Sales占比',{'category_sales':ct.to_dict(),'subcategory_sales':d.groupby(['Category','Sub-Category']).Sales.sum().to_dict()},'低于2%的小扇区不硬塞标签，完整值保存在模板数据JSON中')
    active_share=float(z['rfm_groups'].loc[z['rfm_groups'].Code.eq('111'),'Customer Share'].iloc[0]);f=b(23,'190名高价值活跃客户占2021年693名交易客户','指标 当年客户占比');ax=axes(f,(.14,.15,.72,.58));ax.set_aspect('equal');ax.set_xlim(-1.35,1.35);ax.set_ylim(-.25,1.3);ax.add_patch(Wedge((0,0),1,0,180,width=.25,color=GRAY,alpha=.45));ax.add_patch(Wedge((0,0),1,180-active_share*180,180,width=.25,color=BLUE));ax.text(0,.23,f'{active_share:.1%}',ha='center',size=33);output(f,23,'RFM111客户数 / 2021有交易客户数',active_share)
    f=b(24,'真实月度销售额随季节变化 面积采用蓝色垂直渐变');ax=axes(f,(.12,.17,.81,.57),off=False);xx=np.arange(12);yy=m.values;vertices=[(0,0),*zip(xx,yy),(11,0),(0,0)];clip=PathPatch(MPath(vertices),facecolor='none',edgecolor='none');ax.add_patch(clip)
    grad=np.linspace(0,1,256).reshape(256,1);im=ax.imshow(grad,extent=[0,11,0,yy.max()*1.15],origin='lower',aspect='auto',cmap=LinearSegmentedColormap.from_list('area',[BG,BLUE]));im.set_clip_path(clip);ax.plot(xx,yy,color=BLUE,lw=1.5)
    for i,v in enumerate(yy):ax.text(i,v+.2,f'{v:.1f}',ha='center',size=9)
    ax.set_xticks(xx,[f'{i}月' for i in range(1,13)]);ax.set_xlim(-.25,11.3);ax.set_ylim(0,yy.max()*1.25);ax.grid(False);output(f,24,'2021年逐月Sales/10000',m.to_dict())
    for idx,value,wavy in [(25,all_nr,False),(26,float(share_tech),True)]:
        f=b(idx,'占比由真实订单或销售额计算 水球高度对应百分比','指标 未退货订单占比' if idx==25 else '指标 技术产品销售占比');ax=axes(f,(.14,.13,.72,.60));ax.set_aspect('equal');ax.set_xlim(-1.25,1.25);ax.set_ylim(-1.25,1.25)
        ax.add_patch(Circle((0,0),1.04,fc='none',ec=DEEP,lw=1));circle=Circle((0,0),.98,fc='#163158',ec=DEEP,lw=1);ax.add_patch(circle)
        x=np.linspace(-1,1,500);level=-.98+1.96*value;y=level+(.045*np.sin(x*5+.5) if wavy else 0)
        poly=ax.fill_between(x,-1.1,y,color='#00B5EE' if wavy else DEEP);poly.set_clip_path(circle)
        ax.text(0,.04,f'{value:.1%}',ha='center',va='center',size=34);output(f,idx,'1减去退货订单占比' if idx==25 else 'Technology Sales/all Sales',value,'水球按垂直高度表示指标，不将填充面积视为占比')
    f=b(27,'圆形光晕和逐点金额标签沿用模板 真实数据允许波动');ax=axes(f,(.13,.16,.79,.58),off=False);v=m.iloc[:8].values;xx=np.arange(8);ax.plot(xx,v,color=DEEP,lw=2);ax.scatter(xx,v,s=100,color=BLUE,alpha=.2,zorder=3);ax.scatter(xx,v,s=26,fc=CYAN,ec='white',lw=.7,zorder=4)
    for i,val in enumerate(v):ax.text(i,val+.3,f'{val:.1f}',ha='center',size=10)
    ax.set_xticks(xx,[f'{i}月' for i in range(1,9)]);ax.set_ylim(0,max(v)*1.25);ax.grid(False);output(f,27,'2021年1至8月Sales/10000',m.iloc[:8].to_dict())
    f=b(28,'每条曲线使用独立基线且金额比例一致 以点上原值读取');ax=axes(f,(.13,.16,.80,.57),off=False);months=d.groupby(['Year',d['Order Date'].dt.month]).Sales.sum()/1e4;scale=months.max()*1.28
    for k,yr in enumerate([2019,2020,2021]):
        vals=months.loc[yr].values;off=k*scale;ax.plot(np.arange(12),vals+off,color=[BLUE,YELLOW,PINK][k],lw=1.4);ax.axhline(off,color=GRID,ls=':',lw=.5);ax.text(-.3,off+vals[0],str(yr),color=[BLUE,YELLOW,PINK][k],ha='right',size=10)
        for i,v in enumerate(vals):ax.text(i,off+v+.22,f'{v:.1f}',ha='center',size=7.5)
    ax.set_xticks(range(12),[f'{i}月' for i in range(1,13)]);ax.set_yticks([]);ax.set_xlim(-.35,11.4);ax.set_ylim(-.1,3*scale);ax.grid(False);output(f,28,'2019至2021逐月Sales/10000',months.to_dict(),'曲线错层采用相同金额尺度和独立基线，不能把不同层的绝对纵坐标相加')
    f=b(29,'分组柱读金额 黄色折线读右轴同比率');ax=axes(f,(.12,.17,.77,.57),off=False);xx=np.arange(4);ax.bar(xx-.17,reg,.29,color=DEEP,label='2021年');ax.bar(xx+.17,prev,.29,color=PINK,label='2020年');ax.set_xticks(xx,labels);ax.grid(False);ax.set_ylim(0,max(reg.max(),prev.max())*1.58)
    for i,(v,w) in enumerate(zip(reg,prev)):ax.text(i-.17,v+.25,f'{v:.1f}',ha='center',size=9);ax.text(i+.17,w+.25,f'{w:.1f}',ha='center',size=9)
    ax2=ax.twinx();ax2.plot(xx,growth*100,color=YELLOW,marker='o',lw=1.6);low=float(growth.min()*100);high=float(growth.max()*100);span=max(high-low,10);ax2.set_ylim(low-2*span,high+.35*span);ax2.tick_params(axis='y',labelsize=8,colors=YELLOW);ax2.set_ylabel('同比 %',color=YELLOW,size=9);ax2.spines[['top','left']].set_visible(False)
    for i,v in enumerate(growth):ax2.text(i,v*100+span*.06,f'{v:+.1%}',ha='center',color=YELLOW,size=10)
    ax.legend(loc='lower right',frameon=False,labelcolor='white',fontsize=9);output(f,29,'区域2021与2020销售金额及同比',{'2021':reg.to_dict(),'2020':prev.to_dict(),'YoY':growth.to_dict()},'双轴分别标记金额与同比，未把原参考百分比直接移植成实证结果',legend='右下角金额图例 黄色折线用右轴与标签识别')
    f=b(30,'粉色条形表示2021年金额 蓝色气泡标明同比率');ax=axes(f,(.16,.16,.75,.58));y=np.arange(4);limit=reg.max()*1.35
    ax.barh(y,reg,.4,color=PINK)
    for i,v in enumerate(reg):ax.text(-reg.max()*.035,i,labels[i],ha='right',va='center');ax.text(v+.25,i,f'{v:.1f}',va='center');ax.scatter(limit*.91,i,s=1000,color=DEEP);ax.text(limit*.91,i,f'{growth.iloc[i]:+.1%}',ha='center',va='center',size=9)
    ax.set_xlim(0,limit);ax.set_ylim(3.5,-.6);output(f,30,'2021区域Sales/10000与相对2020的同比',{'Sales':reg.to_dict(),'YoY':growth.to_dict()},'气泡大小固定只承载百分比文本，不将圆面积解释为增长量')
    # 审核与机器可读索引：六个设计维度和适配口径逐项记录。
    mapping=pd.DataFrame(rows);mapping.to_csv(TABLE/'template_mapping.csv',index=False,encoding='utf-8-sig')
    # MultiIndex字典键转为字符串，保留可复核的真实输入值。
    def normalize(x):
        if isinstance(x,dict):return {str(k):normalize(v) for k,v in x.items()}
        if isinstance(x,list):return [normalize(v) for v in x]
        if isinstance(x,np.generic):return x.item()
        return x
    (TABLE/'template_inputs.json').write_text(json.dumps(normalize(inputs),ensure_ascii=False,indent=2),encoding='utf-8')
    write_gallery(mapping)
    print('30幅教材模板复现完成，200dpi；逐项对照与指标输入已导出。')
    return mapping

def write_gallery(mapping):
    """离线对照文档，原图只用于对照，复现输出均为Matplotlib计算绘图。"""
    cards=[]
    for _,r in mapping.iterrows():
        fields=['指标口径','布局结构','配色方案','标签样式','图例位置','标题设计','适配说明']
        detail=''.join(f'<dt>{f}</dt><dd>{html.escape(str(r[f]))}</dd>' for f in fields)
        cards.append(f'<section id="{r["编号"]}"><h2>{r["编号"]} {r["模板名称"]}</h2><p>参考PPT第{r["PPT页码"]}页 图块{r["页内图块"]}（项目按位置编号）</p><div class="pair"><figure><figcaption>用户提供的教材参考图</figcaption><img src="../assets/reference/{r["参考图片"]}"></figure><figure><figcaption>Python复现 使用Superstore真实指标</figcaption><img src="../outputs/templates/{r["复现图片"]}"></figure></div><dl>{detail}</dl></section>')
    page='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>30幅教材模板逐项对照</title><style>body{font-family:Microsoft YaHei,Noto Sans CJK SC,sans-serif;margin:28px;background:#f0f3f7;color:#17263a}h1{font-size:28px}section{background:white;padding:24px;margin:24px 0;border-radius:8px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{margin:0}img{width:100%;height:auto}figcaption{margin:8px 0;font-weight:bold}dl{display:grid;grid-template-columns:110px 1fr;gap:7px;font-size:14px}dt{font-weight:bold}dd{margin:0}a{color:#006ba0}nav{display:flex;gap:10px;flex-wrap:wrap}@media(max-width:700px){.pair{grid-template-columns:1fr}}</style><h1>30幅教材模板复现逐项对照</h1><p>原PPT共27页，未单列编号为1至30的模板清单。本项目从第18、20、22、24页56幅案例图中选择30幅，T01至T30为项目选编编号。比较图形结构、布局、配色、标签、图例、标题设计，同时说明真实业务指标适配。所有复现图由Matplotlib生成，未用Excel截图代替。</p><nav>'+''.join(f'<a href="#{r["编号"]}">{r["编号"]}</a>' for _,r in mapping.iterrows())+'</nav>'+''.join(cards)+'</html>'
    (ROOT/'docs/模板复现逐图对照.html').write_text(page,encoding='utf-8')

if __name__=='__main__':
    from .pipeline import run_analysis
    create_templates(run_analysis())
