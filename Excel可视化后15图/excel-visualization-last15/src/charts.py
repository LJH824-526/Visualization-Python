from chart_common import *
from matplotlib.lines import Line2D


def check_rates(values):
    if not np.isfinite(values).all() or ((values < 0) | (values > 1)).any():
        raise ValueError('占比/完成率必须为 0 到 1 之间的有效数值。')


def round_axes(ax):
    ax.set_aspect('equal')
    ax.set_xlim(-1.04, 1.04)
    ax.set_ylim(-1.04, 1.04)
    ax.axis('off')


def rose(ax, labels, values, palette, hole=0, normalize=True):
    """按原比例决定扇区角度和半径；不把扇区重画成等角度。"""
    check_rates(values)
    if values.sum() <= 0:
        raise ValueError('占比合计必须大于零。')
    round_axes(ax)
    angles = values / values.sum() if normalize else values
    middles = 90 - (np.cumsum(angles)-angles/2)*360
    left_indices = [i for i,a in enumerate(middles) if np.cos(np.deg2rad(a)) < 0]
    left_positions = dict(zip(left_indices, np.linspace(-.88,.94,len(left_indices))))
    start = 90.
    for index,(label, value, fraction, color) in enumerate(zip(labels, values, angles, palette)):
        end = start - fraction * 360
        radius = hole + (1-hole) * value/values.max()
        ax.add_patch(Wedge((0,0),radius,end,start,width=radius-hole if hole else None,
                           facecolor=color,edgecolor=BG,lw=.35))
        middle=np.deg2rad((start+end)/2)
        # 使用两段引导线，把标签放在扇区外，避免遮挡扇区。
        side=1 if np.cos(middle)>=0 else -1
        sy=radius*np.sin(middle)
        label_y=np.clip(sy*1.15,-1.04,1.04)
        if side<0:
            label_y=left_positions[index]
        x0,y0=radius*np.cos(middle),radius*np.sin(middle)
        x1,y1=side*1.17,label_y
        x2=side*1.64
        ax.plot([x0,x1,x2],[y0,y1,y1],color=color,lw=.45,alpha=.9,clip_on=False)
        ax.text((x1+x2)/2,y1+.035,f'{str(label).strip()}\n{value:.1%}',
                ha='center',va='bottom',fontsize=8,color=WHITE,clip_on=False,linespacing=1.15)
        start=end


# %% 16 波浪水球图
def chart_16(show=True):
    df=read_table(16,'B:C',1,header=2)
    p=float(df.loc[0,'完成率']);check_rates(np.array([p]))
    fig,ax,root=canvas(16)
    ax.set_position([.26,.16,.48,.58]);round_axes(ax)
    boundary=Circle((0,0),1,facecolor='none',edgecolor=BLUE,lw=1.3,zorder=5)
    ax.add_patch(boundary)
    x=np.linspace(-1.1,1.1,800)
    level=2*p-1
    wave=level+.055*np.sin(2*np.pi*(x+1)+.6)
    water=ax.fill_between(x,-1.1,wave,color=BLUE,zorder=3)
    water.set_clip_path(boundary)
    ax.text(0,.08,f'{p:.0%}',ha='center',va='center',color=WHITE,fontsize=36,zorder=8)
    fig.text(.065,.938,'本科及以上学历员占比',fontsize=18,weight='bold',color=WHITE,va='top')
    fig.text(.065,.845,f'6月30日最新统计数据本科及以上员工占比{p:.0%}',fontsize=12,color=WHITE,va='top')
    fig.text(.052,.065,'*注：数据来源于公司人力资源系统',fontsize=8,color=WHITE)
    return finish(fig,16,'波浪水球图',show)


# %% 17 玉玦图
def chart_17(show=True):
    df=read_table(17,'B:D',4)
    p=numeric(df,'占比');check_rates(p)
    total=p[0]+p[-1]  # 原模板：每一圈“占比+占位”均为 50%。
    if total<=0 or np.any(p>total):raise ValueError('占比超过玉玦图的原始比例基准。')
    fig,ax,root=canvas(17);round_axes(ax)
    palette=['#37A2DA','#11A7AD','#F5C353',PINK]
    hole=.35;width=(1-hole)/len(df)
    for i,(label,value,color) in enumerate(zip(df['年龄'],p,palette)):
        radius=hole+(i+1)*width
        theta=90-360*value/total
        ax.add_patch(Wedge((0,0),radius,theta,90,width=width-.009,facecolor=color,edgecolor='none'))
        mid=radius-width/2
        ax.text(-.055,mid,str(label),ha='right',va='center',fontsize=9,color=WHITE)
        ang=np.deg2rad(theta)
        ax.text((radius+.065)*np.cos(ang),(radius+.065)*np.sin(ang),f'{value:.1%}',
                ha='center',va='center',fontsize=8,color=WHITE)
    template_text(fig,root,skip_text=('[20,30)',))
    return finish(fig,17,'玉玦图',show)


# %% 18 跑道图
def chart_18(show=True):
    df=read_table(18,'B:D',6)
    y=numeric(df,'人数');total=y.sum()/2
    if total<=0:raise ValueError('部门人数合计必须大于零。')
    fig,ax,root=canvas(18);round_axes(ax)
    palette=['#7030A0',BLUE,'#37A2DA','#11A7AD','#F5C353',PINK]
    hole=.45;width=(1-hole)/len(df)
    for i,(label,value,color) in enumerate(zip(df['部门'],y,palette)):
        radius=hole+(i+1)*width
        ax.add_patch(Wedge((0,0),radius,90-360*value/total,90,width=width-.008,
                           facecolor=color,edgecolor='none'))
        ax.text(-.04,radius-width/2,f'{str(label).strip()}  {value:g}',ha='right',va='center',
                fontsize=7.5,color=WHITE)
    template_text(fig,root,skip_text=('人力部',))
    return finish(fig,18,'跑道图',show)


# %% 19 南丁格尔圆饼图
def chart_19(show=True):
    df=read_table(19,'B:C',6)
    fig,ax,root=canvas(19)
    rose(ax,df['部门'],numeric(df,'人数占比'),[PINK,'#F5C353','#11A7AD',BLUE,'#37A2DA','#7030A0'])
    template_text(fig,root)
    return finish(fig,19,'南丁格尔圆饼图',show)


# %% 20 南丁格尔圆环图
def chart_20(show=True):
    df=read_table(20,'B:C',4)
    fig,ax,root=canvas(20)
    # 保留源 XML 的 60% 内孔，按占比改变各扇区外径。
    rose(ax,df['年龄'],numeric(df,'人数占比'),['#512DCB','#6073F3','#66CBDD','#F5C353'],hole=.60)
    template_text(fig,root)
    return finish(fig,20,'南丁格尔圆环图',show)


# %% 21 南丁格尔圆饼图（PPT 造型）
def chart_21(show=True):
    # 第 6 个工作表原名“20 南丁格尔（PPT）”；按顺序映射到 21。
    # 其独立表格最后一项为 5%，合计 98.3%；不使用透明辅助图表对第 19 表的引用。
    df=read_table(21,'B:C',6)
    fig,ax,root=canvas(21)
    rose(ax,df['部门'],numeric(df,'人数占比'),[PINK,'#F5C353','#11A7AD','#37A2DA',BLUE,'#7030A0'],
         normalize=False)
    _,title_root=template_xml(19)
    template_text(fig,title_root)
    return finish(fig,21,'南丁格尔_PPT造型',show)


# %% 22 仪表盘图
def chart_22(show=True):
    df=read_table(22,'H:H',1)
    value=float(df.loc[0,'指针数值'])
    scale=pd.read_excel(EXCEL_FILE,sheet_name=SHEET_NAMES[22],usecols='B',header=1,nrows=21,engine='openpyxl')
    marks=pd.to_numeric(scale.iloc[:,0],errors='raise').dropna().to_numpy(float)
    low,high=marks.min(),marks.max()
    if not np.isfinite(value) or high<=low:raise ValueError('无效的仪表盘读数或刻度。')
    clipped=np.clip(value,low,high)
    fig,ax,root=canvas(22)
    ax.set_position([.21,.12,.60,.65]);round_axes(ax)
    # 原始刻度范围 50—150，270° 刻度带：50—80 青绿、80—120 黄色、120—150 红色。
    for start,end,c in [(50,80,'#087E8B'),(80,120,'#FFC54D'),(120,150,'#F94C66')]:
        a=225-(start-low)/(high-low)*270;b=225-(end-low)/(high-low)*270
        ax.add_patch(Wedge((0,0),.88,b,a,width=.13,facecolor=c,edgecolor=BG,lw=.5))
    for v in marks:
        angle=np.deg2rad(225-(v-low)/(high-low)*270)
        ax.plot([.91*np.cos(angle),.96*np.cos(angle)],
                [.91*np.sin(angle),.96*np.sin(angle)],color=WHITE,lw=.7)
        ax.text(1.08*np.cos(angle),1.08*np.sin(angle),f'{v:g}',ha='center',va='center',
                color=WHITE,fontsize=8,clip_on=False)
    angle=np.deg2rad(225-(clipped-low)/(high-low)*270)
    ax.plot([0,.72*np.cos(angle)],[0,.72*np.sin(angle)],color=WHITE,lw=1.5,zorder=6)
    ax.add_patch(Circle((0,0),.045,facecolor=WHITE,edgecolor='none',zorder=7))
    template_text(fig,root,skip_exact=('76',))
    # 读数单独居中，避免 100—150 的三位数在源双位数文本框内自动换行。
    fig.text(.534,.20,f'{value:g}',ha='center',va='center',fontsize=24,color=WHITE)
    return finish(fig,22,'仪表盘图',show)


# %% 23 柱形折线图
def chart_23(show=True):
    df=read_table(23,'B:D',6)
    sales=numeric(df,'销售量');growth=numeric(df,'同比')
    if (sales[:-1]==0).any():raise ValueError('上年销量为零，不能计算同比。')
    growth[1:]=sales[1:]/sales[:-1]-1
    x=np.arange(len(df));fig,ax,root=canvas(23)
    category_axis(ax,[str(int(v)) for v in df['年份']],6000,grid=False,ylabels=False,baseline=True)
    bar=ax.bar(x,sales,width=1/3.19,color=BLUE,zorder=3,label='销售量');value_labels(ax,x,sales)
    right=ax.twinx();right.set_ylim(-1.2,.5);right.set_yticks([])
    for spine in right.spines.values():spine.set_visible(False)
    line,=right.plot(x,growth,color=PINK,lw=1.3,marker='o',ms=4,label='同比')
    for xi,v in zip(x,growth):
        right.annotate(f'{v:.0%}',(xi,v),xytext=(0,5),textcoords='offset points',ha='center',
                       va='bottom',color=WHITE,fontsize=8)
    legend=fig.legend([bar,line],['销售量','同比'],bbox_to_anchor=(.926,.785),loc='upper right',
                      frameon=False,ncol=2,fontsize=8,handlelength=1,handletextpad=.4)
    for t in legend.get_texts():t.set_color(WHITE)
    template_text(fig,root)
    return finish(fig,23,'柱形折线图',show)


# %% 24 目标柱形图
def chart_24(show=True):
    df=read_table(24,'B:D',6)
    actual,target=numeric(df,'实际销量'),numeric(df,'目标销量')
    x=np.arange(len(df));fig,ax,root=canvas(24)
    category_axis(ax,df['商品'].tolist(),1000,grid=False,ylabels=False,baseline=True)
    ax.bar(x,target,width=.25,facecolor='none',edgecolor=(1,1,1,.5),lw=.8,zorder=2)
    ax.bar(x,actual,width=1/5.5,color=BLUE,alpha=.97,zorder=3)
    value_labels(ax,x,actual)
    template_text(fig,root)
    return finish(fig,24,'目标柱形图',show)


# %% 25 子弹图
def chart_25(show=True):
    df=read_table(25,'B:G',6,header=2)
    actual,target=numeric(df,'实际'),numeric(df,'目标')
    passed,good,excellent=(numeric(df,c) for c in ['及格','良好','优秀'])
    x=np.arange(len(df));fig,ax,root=canvas(25)
    category_axis(ax,df['商品'].tolist(),1200,200,grid=False,baseline=True)
    handles=[]
    bottom=np.zeros(len(df))
    for values,c in zip([passed,good,excellent],[LIGHT_BLUE,'#00B0F0',BLUE]):
        handles.append(ax.bar(x,values,bottom=bottom,width=1/3.5,color=c,zorder=2))
        bottom+=values
    handles.append(ax.bar(x,actual,width=1/6,color='#0E5DFF',zorder=3))
    mark,=ax.plot(x,target,ls='none',marker='_',ms=10,mew=2,color='#FFC000',zorder=6)
    legend=fig.legend([*handles,mark],['及格','良好','优秀','实际','目标'],loc='upper left',
                      bbox_to_anchor=(.14,.765),frameon=False,ncol=5,fontsize=8,
                      handlelength=.7,handletextpad=.3,columnspacing=1)
    for t in legend.get_texts():t.set_color(WHITE)
    template_text(fig,root)
    return finish(fig,25,'子弹图',show)


# %% 26 柱形圆
def chart_26(show=True):
    df=read_table(26,'B:E',6)
    sales,bubble,yoy=numeric(df,'销量'),numeric(df,'占位'),numeric(df,'同比去年')
    x=np.arange(len(df));fig,ax,root=canvas(26)
    category_axis(ax,df['区域'].tolist(),6000,grid=False,ylabels=False,baseline=True)
    ax.bar(x,sales,width=1/3.19,color=PINK,zorder=3);value_labels(ax,x,sales)
    sizes=np.maximum(8,np.abs(yoy)*100)
    ax.scatter(x,bubble,s=sizes**2,color=BLUE,edgecolors='none',zorder=4)
    for xi,yi,p,size in zip(x,bubble,yoy,sizes):
        ax.text(xi,yi,f'{p:.0%}',ha='center',va='center',fontsize=min(8,size*.43),color=WHITE,zorder=6)
    template_text(fig,root)
    return finish(fig,26,'柱形圆',show)


# %% 27 簇状柱形折线图
def chart_27(show=True):
    df=read_table(27,'B:E',6)
    now,old,growth=(numeric(df,c) for c in ['2022销量','2021销量','同比去年'])
    x=np.arange(len(df));fig,ax,root=canvas(27)
    category_axis(ax,df['区域'].tolist(),5000,grid=False,ylabels=False,baseline=True)
    width=1/(2+.27+2.19);shift=width*(1+.27)/2
    ax.bar(x-shift,now,width=width,color=BLUE,zorder=3)
    ax.bar(x+shift,old,width=width,color=PINK,zorder=3)
    value_labels(ax,x-shift,now,size=8);value_labels(ax,x+shift,old,size=8)
    right=ax.twinx();right.set_ylim(-1.1,.35);right.set_yticks([])
    for spine in right.spines.values():spine.set_visible(False)
    right.plot(x,growth,color='#FFC000',lw=1.2,marker='o',ms=3)
    for xi,v in zip(x,growth):
        right.annotate(f'{v:.0%}',(xi,v),xytext=(0,5),textcoords='offset points',ha='center',
                       va='bottom',color=WHITE,fontsize=8)
    template_text(fig,root,skip_exact=('2021','2022'))
    for label,c,y in [('2022',BLUE,.315),('2021',PINK,.245)]:
        fig.text(.960,y,label,ha='center',va='center',fontsize=8,color=WHITE,
                 bbox={'fc':'none','ec':c,'pad':2,'lw':.7})
    return finish(fig,27,'簇状柱形折线图',show)


# %% 28 复合柱形图
def chart_28(show=True):
    # 原表在各季度之间插入空行：保留这些间隔，不把月份挤到一起。
    df=pd.read_excel(EXCEL_FILE,sheet_name=SHEET_NAMES[28],usecols='B:D',header=1,nrows=15,engine='openpyxl')
    monthly=pd.to_numeric(df['月度销量'],errors='raise').to_numpy(float)
    labels=df['月份'].fillna('').tolist();x=np.arange(len(df))
    fig,ax,root=canvas(28)
    category_axis(ax,labels,12000,grid=False,ylabels=False,baseline=True)
    ax.tick_params(axis='x',labelsize=7)
    palette=['#4A5BD1','#FC6C0F','#F6A50B','#A2417B']
    for start,c in zip([0,4,8,12],palette):
        idx=np.arange(start,start+3)
        values=monthly[idx]
        if not np.isfinite(values).all():raise ValueError('季度包含缺失的月度销量。')
        total=values.sum()
        ax.bar(idx,np.full(3,total),width=1,color=c,alpha=.20,zorder=2)
        ax.bar(idx,values,width=.4,color=c,zorder=3)
        value_labels(ax,idx,values,size=7,offset=2)
        ax.annotate(f'{total:g}',(start+1,total),xytext=(0,3),textcoords='offset points',
                    ha='center',va='bottom',fontsize=8,color=WHITE)
    template_text(fig,root)
    return finish(fig,28,'复合柱形图',show)


# %% 29 滑珠图
def chart_29(show=True):
    df=read_table(29,'B:E',5)
    values=numeric(df,'完成率');check_rates(values)
    fig,ax,root=canvas(29)
    ax.set_xlim(0,1);ax.set_ylim(-.5,len(df)-.5)
    ax.set_xticks([]);ax.set_yticks(np.arange(len(df)),df['区域']);ax.tick_params(axis='y',labelsize=9,pad=8)
    for j,p in enumerate(values):
        ax.plot([0,1],[j,j],lw=12,color=(1,1,1,.34),solid_capstyle='round',clip_on=False)
        ax.plot([0,p],[j,j],lw=12,color=BLUE,solid_capstyle='round',clip_on=False)
        ax.scatter([p],[j],s=15**2,color=BLUE,edgecolors='none',zorder=6)
        ax.text(max(.04,p-.055),j,f'{p:.0%}',ha='right',va='center',fontsize=9,color=WHITE,zorder=7)
    template_text(fig,root)
    return finish(fig,29,'滑珠图',show)


# %% 30 对比滑珠图
def chart_30(show=True):
    df=read_table(30,'B:F',5,header=2)
    now,old=numeric(df,'2022完成率'),numeric(df,'2021完成率')
    check_rates(now);check_rates(old)
    fig,ax,root=canvas(30)
    ax.set_xlim(0,1);ax.set_ylim(-.5,len(df)-.5)
    ax.set_xticks([]);ax.set_yticks(np.arange(len(df)),df['区域']);ax.tick_params(axis='y',labelsize=9,pad=6)
    for j,(a,b) in enumerate(zip(now,old)):
        ax.plot([0,1],[j,j],color=(1,1,1,.34),lw=2.5,zorder=2)
        ax.plot([0,a],[j,j],color=BLUE,lw=2.5,zorder=3)
        ax.scatter([b],[j],s=10**2,color='#B3B4C5',edgecolors='none',zorder=5)
        ax.scatter([a],[j],s=10**2,color=BLUE,edgecolors='none',zorder=6)
        ax.annotate(f'{a:.0%}',(a,j),xytext=(0,7),textcoords='offset points',
                    ha='center',va='bottom',fontsize=8,color=WHITE,zorder=7)
    template_text(fig,root,skip_text=('完率',))
    legend=fig.legend([Line2D([],[],ls='none',marker='o',color=BLUE,ms=5),
                       Line2D([],[],ls='none',marker='o',color='#B3B4C5',ms=5)],
                      ['2022完成率','2021完成率'],loc='upper left',bbox_to_anchor=(.095,.77),
                      frameon=False,ncol=2,fontsize=8,handlelength=.7,handletextpad=.4,columnspacing=1.3)
    for t in legend.get_texts():t.set_color(WHITE)
    return finish(fig,30,'对比滑珠图',show)
