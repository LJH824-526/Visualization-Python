from chart_common import *

# %% 01 渐变柱形图
def chart_01(show=True):
    df = read_table(1, 'B:C', 6)
    labels, y = df['区域'].tolist(), numeric(df, '销售量')
    x = np.arange(len(y))
    fig, ax, root = canvas(1)
    category_axis(ax, labels, 4000, 1000)
    width = 1/(1+2.19)
    for xi, yi in zip(x, y):
        gradient_rect(ax, xi-width/2, 0, width, yi, '#00B0F0', '#0070C0')
    value_labels(ax, x, y)
    template_text(fig, root)
    return finish(fig, 1, '渐变柱形图', show)


# %% 02 带均值柱形图
def chart_02(show=True):
    df = read_table(2, 'B:D', 6)
    labels, y = df['区域'].tolist(), numeric(df, '销售量')
    mean = y.mean()  # 根据销售量实时计算，避免使用可能失效的公式缓存。
    x = np.arange(len(y))
    fig, ax, root = canvas(2)
    category_axis(ax, labels, 4000, grid=False, ylabels=False, baseline=True)
    ax.bar(x, y, width=1/3.19, color=BLUE, zorder=3)
    ax.axhline(mean, color='#FFC000', linewidth=1.5, zorder=5)
    value_labels(ax, x, y, color=BLUE)
    template_text(fig, root, {'2656': f'{mean:.0f}'})
    return finish(fig, 2, '带均值柱形图', show)


# %% 03 渐变圆角柱形图
def chart_03(show=True):
    df = read_table(3, 'B:C', 6)
    labels, y = df['商品'].tolist(), numeric(df, '销量')
    x = np.arange(len(y))
    fig, ax, root = canvas(3)
    category_axis(ax, labels, 1200, 200)
    width = 1/6
    for xi, yi in zip(x, y):
        gradient_rect(ax, xi-width/2, 0, width, yi, '#0050A4', '#00EDF2', rounded=True)
        ax.annotate(f'{yi:g}', (xi,yi), xytext=(10,14), textcoords='offset points',
                    ha='center', va='bottom', fontsize=9, color='#BFD9EF',
                    bbox={'boxstyle':'round,pad=0.35','fc':'#0070C0','alpha':.19,'ec':'none'},
                    arrowprops={'arrowstyle':'-','color':'#82ADD7','lw':.55,
                                'connectionstyle':'angle,angleA=90,angleB=0,rad=0'}, zorder=8)
    template_text(fig, root)
    return finish(fig, 3, '渐变圆角柱形图', show)


# %% 04 标注柱形图
def chart_04(show=True):
    df = read_table(4, 'B:C', 8)
    labels, y = df.iloc[:,0].tolist(), numeric(df, '销量')
    palette = ['#7BBDD5','#49A098','#E66B4C','#FFC000','#0097E0','#0070C0','#4A5BD1','#464CAC']
    x=np.arange(len(y)); fig,ax,root=canvas(4)
    category_axis(ax, labels, 10000, 2000)
    ax.bar(x,y,width=.5,color=palette,zorder=3)
    for xi,yi,c in zip(x,y,palette):
        ax.annotate(f'{yi:g}',(xi,yi),xytext=(0,5),textcoords='offset points',
                    ha='center',va='bottom',fontsize=8,color=WHITE,
                    bbox={'boxstyle':'square,pad=.16','fc':c,'ec':'none'},zorder=8)
        ax.annotate('',(xi,yi+20),xytext=(0,5),textcoords='offset points',
                    arrowprops={'arrowstyle':'-|>','color':c,'lw':0,'mutation_scale':7})
    template_text(fig,root)
    return finish(fig,4,'标注柱形图',show)


# %% 05 层叠柱形图
def chart_05(show=True):
    df=read_table(5,'B:D',6)
    sales,profit=numeric(df,'销售额'),numeric(df,'利润额')
    x=np.arange(len(df)); fig,ax,root=canvas(5)
    category_axis(ax,df['季度'].tolist(),6000,grid=False,ylabels=False,baseline=True)
    # 源图采用重叠 30% 的簇状柱形，两个指标均从零开始。
    width=1/(2-.30+2.19); shift=width*(1-.30)/2
    ax.bar(x-shift,sales,width=width,color=BLUE,zorder=3)
    ax.bar(x+shift,profit,width=width,color=PINK,zorder=4)
    value_labels(ax,x-shift,sales)
    value_labels(ax,x+shift,profit)
    template_text(fig,root,skip_exact=('销售额', '利润额'))
    for txt,c,ypos in [('销售额',BLUE,.463),('利润额',PINK,.388)]:
        fig.text(.847,ypos,txt,ha='center',va='center',fontsize=8,color=WHITE,
                 bbox={'fc':'none','ec':c,'lw':.7,'pad':2.3},zorder=20)
    return finish(fig,5,'层叠柱形图',show)


# %% 06 蝴蝶图（销量）
def chart_06(show=True):
    df=read_table(6,'B:F',5)
    left,right=numeric(df,'2022年销量'),numeric(df,'2021年销量')
    # 重算占位：让左侧条形右端对齐，中央留出相同宽度。
    left_edge=left[0]+left[-1]; gap=left[0]
    y=np.arange(len(df)); fig,ax,root=canvas(6)
    ax.set_xlim(0,7000);ax.set_ylim(-.5,4.5);ax.set_xticks([]);ax.set_yticks([])
    ax.barh(y,left,left=left_edge-left,height=.4,color=BLUE)
    ax.barh(y,right,left=left_edge+gap,height=.4,color=PINK)
    for j,(a,b,region) in enumerate(zip(left,right,df['区域'])):
        ax.text(left_edge-a+30,j,f'{a:g}',ha='left',va='center',fontsize=9,color=WHITE)
        ax.text(left_edge+gap+b-30,j,f'{b:g}',ha='right',va='center',fontsize=9,color=WHITE)
        ax.text(left_edge+gap/2,j,region,ha='center',va='center',fontsize=9,color=WHITE)
    template_text(fig,root,skip_text=('                              ',))
    fig.text(.37,.738,'2022',ha='center',fontsize=11,color=BLUE)
    fig.text(.615,.738,'2021',ha='center',fontsize=11,color='#F94C66')
    return finish(fig,6,'蝴蝶图_销量',show)


# %% 07 蝴蝶图（百分比条纹）
def chart_07(show=True):
    df=read_table(7,'B:D',5)
    left,right=numeric(df,'2022年'),numeric(df,'2021年')
    fig,ax,root=canvas(7)
    ax.set_xlim(-.54,.54);ax.set_ylim(4.8,-.8);ax.set_xticks([]);ax.set_yticks([])
    gap=.13
    for j,(a,b,region) in enumerate(zip(left,right,df['区域'])):
        # REPT("|", 完成率*200) 的代码等价实现：用等间距竖线组成条纹。
        na,nb=int(a*200),int(b*200)
        ax.vlines(-gap-np.arange(na)/200,j-.29,j+.29,color=BLUE,lw=.7)
        ax.vlines(gap+np.arange(nb)/200,j-.29,j+.29,color=PINK,lw=.7)
        ax.text(0,j,region,ha='center',va='center',fontsize=9,color=WHITE)
        ax.text(-gap-a-.015,j,f'{a:.0%}',ha='right',va='center',fontsize=9,color=WHITE)
        ax.text(gap+b+.015,j,f'{b:.0%}',ha='left',va='center',fontsize=9,color=WHITE)
    fig.text(.06,.922,'2022年第一季度销售目标完成情况',fontsize=18,weight='bold',color=WHITE,va='top')
    fig.text(.06,.815,'华东区域完成率最高达到36%，但是相比去年的42%有所下降',fontsize=11,color=WHITE,va='top')
    fig.text(.04,.075,'*注：数据来源于公司销售系统，统计日期截至2022.03.31',fontsize=8,color=WHITE)
    return finish(fig,7,'蝴蝶图_百分比',show)


# %% 08 数值百分比
def chart_08(show=True):
    df=read_table(8,'B:F',6)
    y=np.arange(len(df)); sales=numeric(df,'销量'); yoy=numeric(df,'同比去年')
    max_sales=sales.max(); tail=max_sales/4
    fig,ax,root=canvas(8)
    ax.set_xlim(0,max_sales+tail);ax.set_ylim(-.5,len(df)-.5)
    ax.set_xticks([]);ax.set_yticks(y,df['区域']);ax.tick_params(axis='y',pad=3)
    ax.barh(y,sales,height=1/1.3,color='#09387E')
    ax.barh(y,max_sales-sales,left=sales,height=1/1.3,color=LIGHT_BLUE)
    ax.barh(y,np.full(len(df),tail),left=max_sales,height=1/1.3,color='#9B3D4F')
    for j,(s,p) in enumerate(zip(sales,yoy)):
        ax.text(s-35,j,f'{s:g}',ha='right',va='center',fontsize=9,color=WHITE)
        ax.text(max_sales+tail/2,j,f'{p:.1%}',ha='center',va='center',fontsize=9,color=WHITE)
    template_text(fig,root)
    return finish(fig,8,'数值百分比',show)


# %% 09 对比柱形图
def chart_09(show=True):
    df=read_table(9,'B:E',5)
    old,new=numeric(df,'2021销量'),numeric(df,'2022销量')
    difference=old-new
    x=np.arange(len(df));fig,ax,root=canvas(9)
    category_axis(ax,df['商品'].tolist(),6000,grid=False,ylabels=False,baseline=True)
    width=.22; off=.14
    bars1=ax.bar(x-off,old,width=width,color=BLUE,zorder=3,label='2021销量')
    bars2=ax.bar(x+off,new,width=width,color=LIGHT_BLUE,zorder=3,label='2022销量')
    value_labels(ax,x-off,old,offset=5)
    for xi,a,b,delta in zip(x,old,new,difference):
        ax.text(xi+off,b-110,f'{b:g}',ha='center',va='top',fontsize=9,color=WHITE,zorder=8)
        ax.plot([xi+off,xi+off],[b,a],color=WHITE,lw=.8,zorder=5)
        ax.plot([xi+off-.035,xi+off+.035],[a,a],color=WHITE,lw=.8,zorder=5)
        ax.plot([xi-.01],[a],marker='s',ms=4.5,color='white',zorder=6)
        ax.text(xi+off,(a+b)/2,f'{delta:g}',ha='center',va='center',fontsize=9,color=WHITE,zorder=8)
    legend=fig.legend([bars1,bars2],['2021销量','2022销量'],loc='upper left',
                     bbox_to_anchor=(.058,.742),frameon=False,ncol=2,fontsize=9,
                     handlelength=.6,handletextpad=.4,columnspacing=1.2)
    for t in legend.get_texts():t.set_color(WHITE)
    template_text(fig,root)
    return finish(fig,9,'对比柱形图',show)


# %% 10 甘特图
def chart_10(show=True):
    df=read_table(10,'B:G',7,header=2)
    starts=df['开始日期']
    if pd.api.types.is_numeric_dtype(starts):
        starts=pd.to_datetime(starts,unit='D',origin='1899-12-30')
    else:starts=pd.to_datetime(starts)
    start_numbers=(starts-pd.Timestamp('1899-12-30')).dt.total_seconds().to_numpy()/86400
    duration,completion=numeric(df,'项目天数'),numeric(df,'完成度')
    y=np.arange(len(df));fig,ax,root=canvas(10)
    ax.set_xlim(44621,44726);ax.set_ylim(len(df)-.5,-.5)
    ax.set_yticks(y,df['项目名称']);ticks=np.arange(44621,44727,15)
    dates=pd.to_datetime(ticks,unit='D',origin='1899-12-30')
    ax.set_xticks(ticks,[f'{d.month}/{d.day}/{d.year}' for d in dates])
    ax.xaxis.tick_top();ax.tick_params(axis='x',labelsize=8,pad=5)
    ax.xaxis.grid(True,color=WHITE,alpha=.28,ls='--',lw=.6)
    ax.barh(y,duration,left=start_numbers,height=.5,color=BLUE,zorder=3)
    ax.barh(y,duration*completion,left=start_numbers,height=.5,color='#00A7DF',zorder=4)
    for j,(s,d,p) in enumerate(zip(start_numbers,duration,completion)):
        ax.text(s+d/2,j,f'{p:.0%}',ha='center',va='center',fontsize=9,color=WHITE,zorder=6)
    template_text(fig,root)
    return finish(fig,10,'甘特图',show)


# %% 11 平滑折线图
def chart_11(show=True):
    df=read_table(11,'B:D',11)
    y=numeric(df,'销量');x=np.arange(len(y));xx,yy=smooth_curve(x,y)
    fig,ax,root=canvas(11)
    category_axis(ax,df['月份'].tolist(),4000,1000,grid=False,baseline=True)
    ax.tick_params(axis='x',labelsize=8)
    ax.tick_params(axis='y',labelsize=8,colors='#E66B4C')
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v,pos:f'{v:,.0f}'))
    ax.plot(xx,yy,color='#E66B4C',lw=1)
    peak=int(np.argmax(y))
    ax.annotate(f'{y[peak]:g}',(peak,y[peak]),xytext=(0,4),textcoords='offset points',
                ha='center',va='bottom',fontsize=9,color=WHITE)
    ax.vlines(peak,0,y[peak],color='#E66B4C',ls=(0,(2,3)),lw=.6,alpha=.7)
    template_text(fig,root,skip_exact=('2021','2022'))
    # 年份色带的位置和配色沿用原模板。
    for x0,w,year,c in [(.09325,.64013,'2021','#62C7DC'),(.74219,.23483,'2022','#F4C75B')]:
        patch=FancyBboxPatch((x0,.113),w,.052,boxstyle='round,pad=0,rounding_size=.005',
                            transform=fig.transFigure,facecolor=c,edgecolor='none')
        fig.patches.append(patch)
        fig.text(x0+w/2,.139,year,ha='center',va='center',fontsize=10,color=WHITE)
    return finish(fig,11,'平滑折线图',show)


# %% 12 菱形走势图
def chart_12(show=True):
    df=read_table(12,'B:C',8)
    y=numeric(df,'完成率');x=np.arange(len(y));fig,ax,root=canvas(12)
    category_axis(ax,df['月份'].tolist(),.8,grid=False,ylabels=False,baseline=True)
    # 源文件连接线为 noFill：只画空心菱形，不擅自增加折线。
    ax.plot(x,y,linestyle='none',marker='D',ms=8,mfc=BG,mec=PINK,mew=.75)
    for xi,yi in zip(x,y):
        ax.annotate(f'{yi:.2%}',(xi,yi),xytext=(0,7),textcoords='offset points',
                    ha='center',va='bottom',fontsize=9,color=WHITE)
    template_text(fig,root)
    return finish(fig,12,'菱形走势图',show)


# %% 13 对比折线图
def chart_13(show=True):
    df=read_table(13,'B:D',6)
    old,new=numeric(df,'2021年'),numeric(df,'2022年')
    x=np.arange(len(df));fig,ax,root=canvas(13)
    category_axis(ax,df['月份'].tolist(),3000,500)
    line1,=ax.plot(x,old,color=PINK,lw=1.5,marker='o',ms=5,mec=BG,mew=.75,label='2021年')
    line2,=ax.plot(x,new,color=BLUE,lw=1.5,marker='o',ms=5,mec=BG,mew=.75,label='2022年')
    for xi,a,b in zip(x,old,new):
        old_above = a >= b
        ax.annotate(f'{a:g}',(xi,a),xytext=(0,6 if old_above else -7),textcoords='offset points',
                    ha='center',va='bottom' if old_above else 'top',fontsize=8,color=WHITE)
        ax.annotate(f'{b:g}',(xi,b),xytext=(0,-7 if old_above else 6),textcoords='offset points',
                    ha='center',va='top' if old_above else 'bottom',fontsize=8,color=WHITE)
    legend=fig.legend([line1,line2],['2021年','2022年'],loc='upper right',
                      bbox_to_anchor=(.945,.746),frameon=False,ncol=2,fontsize=8,
                      handlelength=1.1,handletextpad=.25,columnspacing=1)
    for t in legend.get_texts():t.set_color(WHITE)
    template_text(fig,root)
    return finish(fig,13,'对比折线图',show)


# %% 14 单值圆环图
def chart_14(show=True):
    df=read_table(14,'B:C',1)
    p=float(df.loc[0,'完成率'])
    if not 0<=p<=1:raise ValueError('完成率必须介于 0 和 1 之间。')
    fig,ax,root=canvas(14)
    ax.set_aspect('equal');ax.set_xlim(-1.02,1.02);ax.set_ylim(-1.02,1.02);ax.axis('off')
    # 原生 XML 设置 holeSize=90；保留 90% 的内径，而非渲染器的默认粗环。
    hole=.90
    ax.add_patch(Wedge((0,0),1,0,360,width=1-hole,facecolor=(1,1,1,.1),edgecolor='none'))
    # Excel firstSliceAng=300，从左上 150° 起顺时针填充。
    mask=Wedge((0,0),1,150-360*p,150,width=1-hole,facecolor='none',edgecolor='none')
    ax.add_patch(mask)
    ramp=np.linspace(0,1,600)[:,None,None]
    bottom=np.array(colors.to_rgba('#E74E69'));top=np.array(colors.to_rgba('#7030A0'))
    im=ax.imshow(bottom[None,None,:]*(1-ramp)+top[None,None,:]*ramp,
                 extent=(-1,1,-1,1),origin='lower',interpolation='bicubic',zorder=3)
    im.set_clip_path(mask)
    template_text(fig,root,{'85%':f'{p:.0%}'})
    return finish(fig,14,'单值圆环图',show)


# %% 15 水球图
def chart_15(show=True):
    df=read_table(15,'B:C',1)
    p=float(df.loc[0,'完成率'])
    if not 0<=p<=1:raise ValueError('完成率必须介于 0 和 1 之间。')
    fig,ax,root=canvas(15)
    ax.set_position([.26,.16,.48,.58]);ax.set_aspect('equal')
    ax.set_xlim(-1.04,1.04);ax.set_ylim(-1.04,1.04);ax.axis('off')
    # 圆形边界 + 按数值计算的水位 + 圆形裁切；不使用固定百分比的图片。
    boundary=Circle((0,0),1,facecolor='none',edgecolor=BLUE,lw=1.4,zorder=5)
    ax.add_patch(boundary)
    water=Rectangle((-1,-1),2,2*p,facecolor=BLUE,edgecolor='none',zorder=3)
    ax.add_patch(water);water.set_clip_path(boundary)
    ax.text(0,.03,f'{p:.0%}',ha='center',va='center',fontsize=40,color=WHITE,zorder=8)
    fig.text(.065,.938,'2022年上半年目标完成率',fontsize=18,weight='bold',color=WHITE,va='top')
    fig.text(.065,.845,f'截至6月30日销售目标总体完成率达到{p:.0%}',fontsize=12,color=WHITE,va='top')
    fig.text(.052,.065,'*注：数据来源于公司销售系统',fontsize=8,color=WHITE)
    return finish(fig,15,'水球图',show)
