import json,textwrap
import pandas as pd
from matplotlib.offsetbox import OffsetImage,AnnotationBbox
from matplotlib import colors
from _style import *

BG,CARD='#1A1E43','#2C3560'
MANIFEST=json.loads((ROOT/'data/source_manifest.json').read_text(encoding='utf-8'))
DEFAULTS={'month':MANIFEST['default_month'],'theme':MANIFEST['default_theme']}
STATE=DEFAULTS.copy()
COMPONENTS={1:'推广费用',2:'其他费用',3:'人工费用',4:'产品费用',5:'快递公司销量',6:'区域销量',
            7:'销量环比',8:'各月销售额(万)',9:'产品类别销量',10:'商品销售额Top3',11:'利润额占比销售额'}
THEMES={'展示参考':'#C0E4BA','原生白字':WHITE}
COST_KEYS={1:'推广',2:'其他',3:'人工',4:'产品'}


def read_data(filename):
    return pd.read_csv(ROOT/'data'/filename,encoding='utf-8-sig')


def get_stats(month=None):
    month=month or DEFAULTS['month']
    if month not in MANIFEST['months']:raise ValueError('月份不在源数据中。')
    monthly=read_data('monthly.csv').set_index('月份')
    row=monthly.loc[month]
    index=MANIFEST['months'].index(month)
    previous=MANIFEST['months'][index-1] if index else None
    previous_volume=int(monthly.loc[previous,'销量']) if previous else None
    growth=float(row['销量']/previous_volume-1) if previous_volume else None
    result={'month':month,'volume':int(row['销量']),'revenue':float(row['销售额']),
            'profit':float(row['利润额']),'margin':float(row['利润额']/row['销售额']) if row['销售额'] else None,
            'previous':previous,'previous_volume':previous_volume,'growth':growth,'monthly':monthly}
    for key,filename,column,order in [
        ('region','region_month.csv','区域',MANIFEST['regions']),
        ('courier','courier_month.csv','快递公司',MANIFEST['couriers']),
        ('category','category_month.csv','产品类别',MANIFEST['categories'])]:
        data=read_data(filename);selected=data.loc[data['月份']==month].set_index(column)['销量']
        result[key]=selected.reindex(order,fill_value=0).astype(int)
    costs=read_data('cost_month.csv');selected=costs.loc[costs['月份']==month].set_index('类别')['成本']
    result['costs']=selected.reindex(MANIFEST['costs'])
    if result['costs'].isna().any():raise ValueError('所选月份的成本类别有缺失。')
    result['cost_total']=float(result['costs'].sum())
    products=read_data('product_month.csv')
    result['top3']=products.loc[products['月份']==month].sort_values(['销售额','产品名称'],ascending=[False,True]).head(3)
    return result


def foreground(theme):
    if theme not in THEMES:raise ValueError('主题应为展示参考或原生白字。')
    return THEMES[theme]


def plain(ax):
    ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')


def draw_component(ax,number,stats,fg):
    if number in COST_KEYS:
        plain(ax);kind=COST_KEYS[number];value=float(stats['costs'][kind])
        rate=value/stats['cost_total'] if stats['cost_total'] else 0
        ax.text(.18,.89,kind,color=fg,fontsize=12,ha='left')
        ring=ax.inset_axes([.015,.08,.51,.66]);small_ring(ring,rate,f'{rate:.2%}','#7BBDD5',fg,width=.15)
        ax.text(.57,.60,kind+'费用\n合计',color=fg,fontsize=10,linespacing=1.5,va='center')
        ax.text(.57,.27,f'{value:.2f}',color=fg,fontsize=12)
    elif number in (5,6):
        values=stats['courier'] if number==5 else stats['region'];x=np.arange(len(values))
        ax.bar(x,values.to_numpy(),width=1/3.19,color='#FC6C9D' if number==5 else '#7BBDD5')
        ax.set_xlim(-.6,len(values)-.4);ax.set_ylim(0,max(1,float(values.max())*1.32))
        ax.set_xticks(x,values.index);ax.set_yticks([]);ax.tick_params(colors=fg,labelsize=9)
        for xi,v in zip(x,values):ax.annotate(str(v),(xi,v),xytext=(0,5),textcoords='offset points',ha='center',color=fg,fontsize=10)
    elif number==7:
        labels=[stats['previous'] or '上月无数据',stats['month']]
        values=[stats['previous_volume'] or 0,stats['volume']]
        ax.barh([0,1],values,height=.28,color=['#4A5BD1','#7BBDD5'])
        ax.set_yticks([0,1],labels);ax.set_xticks([]);ax.set_xlim(0,max(values)*1.5);ax.set_ylim(-.6,1.6)
        ax.tick_params(colors=fg,labelsize=10)
        for yi,v in enumerate(values):
            label='—' if yi==0 and stats['previous'] is None else str(v)
            ax.annotate(label,(v,yi),xytext=(5,0),textcoords='offset points',ha='left',va='center',color=fg,fontsize=10)
        ax.text(.96,.70,'—' if stats['growth'] is None else f'{stats["growth"]:.2%}',
                transform=ax.transAxes,ha='right',va='center',color=fg,fontsize=16,weight='bold')
        ax.text(.96,.24,'环比',transform=ax.transAxes,ha='right',color=fg,fontsize=10)
    elif number==8:
        data=stats['monthly'].reindex(MANIFEST['months']);y=data['销售额'].to_numpy(float)/10000;x=np.arange(len(data))
        maximum=max(200,np.ceil(y.max()/50)*50)
        ax.set_xlim(0,len(data)-1);ax.set_ylim(0,maximum)
        polygon=ax.fill_between(x,0,y,facecolor='none',edgecolor='none')
        ramp=np.linspace(.15,.95,250)[:,None,None]
        rgba=np.tile(np.array(colors.to_rgba('#4A5BD1')),(250,1,1));rgba[:,:,3]=ramp[:,:,0]
        image=ax.imshow(rgba,extent=(0,len(data)-1,0,maximum),origin='lower',aspect='auto')
        image.set_clip_path(polygon.get_paths()[0],ax.transData)
        ax.plot(x,y,color='#4A5BD1',lw=.8)
        ax.set_xticks(x,MANIFEST['months']);ax.set_yticks(np.arange(0,maximum+1,50))
        ax.set_yticklabels([f'{v:.2f}' for v in np.arange(0,maximum+1,50)])
        ax.tick_params(colors=fg,labelsize=8)
    elif number==9:
        values=stats['category']
        pie_ring(ax,values.index.tolist(),values.to_numpy(),['#FC6C9D','#4A5BD1','#F6A576'],
                 hole=.85,fg=fg,center=str(stats['volume']),subtitle='总销量')
    elif number==10:
        plain(ax)
        ax.text(.38,.91,'产品',ha='center',fontsize=10,color=fg)
        ax.text(.75,.91,'销售额(万)',ha='center',fontsize=10,color=fg)
        ax.text(.93,.91,'销量',ha='center',fontsize=10,color=fg)
        for rank,(_,row) in enumerate(stats['top3'].iterrows(),1):
            y=.72-(rank-1)*.29
            image=plt.imread(ROOT/'assets/icons'/f'medal{rank}.png')
            artist=AnnotationBbox(OffsetImage(image,zoom=.38),(.09,y),xycoords=ax.transAxes,frameon=False)
            ax.add_artist(artist)
            lines=textwrap.wrap(str(row['产品名称']),width=24,break_long_words=True)
            name='\n'.join(lines[:2])+('…' if len(lines)>2 else '')
            ax.text(.39,y,name,ha='center',va='center',fontsize=9,color=fg,linespacing=1.15)
            ax.text(.75,y,f'{row["销售额"]/10000:.2f}',ha='center',va='center',fontsize=10,color=fg,
                    bbox={'fc':'#4A5BD1','ec':'none','pad':3})
            ax.text(.93,y,str(int(row['销量'])),ha='center',va='center',fontsize=10,color=fg)
    elif number==11:
        plain(ax);rate=stats['margin']
        ring=ax.inset_axes([.015,.16,.44,.78]);small_ring(ring,rate or 0,'—' if rate is None else f'{rate:.2%}',
                                                       '#FC6C9D',fg,width=.15)
        # 单独扩大中心值字号，同时把“利润率”说明放在圆心下方。
        ring.texts[0].set_fontsize(25)
        ring.text(0,-.36,'利润率',ha='center',va='center',color=fg,fontsize=10)
        ax.text(.54,.69,'利润额(万)',color=fg,fontsize=10,va='center')
        ax.text(.94,.69,f'{stats["profit"]/10000:.2f}',ha='right',va='center',color='#FC6C9D',fontsize=18,weight='bold')
        ax.text(.54,.45,'销售额(万)',color=fg,fontsize=10,va='center')
        ax.text(.94,.45,f'{stats["revenue"]/10000:.2f}',ha='right',va='center',color='#FC6C9D',fontsize=18,weight='bold')
        ax.text(.54,.09,'利润额占比销售额',ha='center',va='center',fontsize=12,color=fg,
                bbox={'boxstyle':'round,pad=.55','fc':'none','ec':'#4A5BD1','lw':1.3})
    else:raise ValueError('图号应为 1—11。')


def render_dashboard(month=None,theme=None):
    month=month or DEFAULTS['month'];theme=theme or DEFAULTS['theme'];fg=foreground(theme);stats=get_stats(month)
    fig=plt.figure(figsize=(16,9),facecolor=BG)
    add_card(fig,[.015,.89,.97,.095],CARD)
    fig.text(.027,.942,'公司销售数据可视化看板',color=fg,fontsize=22,weight='bold',va='center')
    fig.text(.952,.942,month,ha='right',va='center',fontsize=15,color=fg)
    cal=fig.add_axes([.866,.921,.028,.047],zorder=3);cal.imshow(plt.imread(ROOT/'assets/icons/calendar.png'));cal.axis('off')
    cards={9:[.015,.515,.32,.365],7:[.343,.65,.32,.23],10:[.343,.37,.32,.27],
           11:[.343,.06,.32,.30],8:[.67,.57,.315,.31],6:[.67,.315,.315,.245],5:[.67,.06,.315,.245]}
    for number,b in cards.items():
        x,y,w,h=b;add_card(fig,b,CARD)
        if number not in (11,):fig.text(x+w/2,y+h-.030,COMPONENTS[number],ha='center',va='center',color=fg,fontsize=14)
        if number==9:bounds=[x+.010,y+.020,w-.020,h-.072]
        elif number==11:bounds=[x+.015,y+.010,w-.030,h-.020]
        elif number==10:bounds=[x+.015,y+.014,w-.030,h-.067]
        elif number==8:bounds=[x+.038,y+.045,w-.053,h-.104]
        elif number==7:bounds=[x+.032,y+.025,w-.050,h-.080]
        else:bounds=[x+.026,y+.040,w-.045,h-.105]
        ax=clean_axis(fig,bounds,CARD,fg);draw_component(ax,number,stats,fg)
    add_card(fig,[.015,.06,.32,.445],CARD)
    fig.text(.175,.476,'成本费用',ha='center',va='center',fontsize=14,color=fg)
    positions={1:[.023,.275,.148,.175],3:[.179,.275,.148,.175],4:[.023,.075,.148,.175],2:[.179,.075,.148,.175]}
    for number,b in positions.items():
        add_card(fig,b,CARD,edge='#7BBDD5',rounded=True)
        x,y,w,h=b;ax=clean_axis(fig,[x+.004,y+.004,w-.008,h-.008],CARD,fg);draw_component(ax,number,stats,fg)
    add_card(fig,[.015,.008,.97,.040],CARD)
    fig.text(.028,.028,f'{MANIFEST["year"]}年数据  ·  销量按销售明细记录数统计  ·  成本保持原表数值口径',va='center',fontsize=8,color=fg)
    return fig


def render_component(number,month=None,theme=None):
    if number not in COMPONENTS:raise ValueError('图号应为 1—11。')
    month=month or DEFAULTS['month'];theme=theme or DEFAULTS['theme'];fg=foreground(theme)
    fig=plt.figure(figsize=(6.4,4.4),facecolor=CARD)
    fig.text(.5,.94,COMPONENTS[number],ha='center',va='center',color=fg,fontsize=18)
    ax=clean_axis(fig,[.10,.13,.80,.69],CARD,fg);draw_component(ax,number,get_stats(month),fg)
    fig.text(.04,.04,month,color=fg,fontsize=8)
    return fig


def preview_states():
    return [(f'{month} · {theme}',{'month':month,'theme':theme}) for theme in THEMES for month in MANIFEST['months']]
