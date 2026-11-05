"""19幅分析图：前10幅为描述分析，后9幅为模型图；教材复现另见templates.py。"""
from pathlib import Path
from io import BytesIO
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager, ticker
from .pipeline import ROOT

OUT=ROOT/'outputs/figures'
BLUE='#2676A9'; TEAL='#199C99'; GOLD='#E6AD42'; RED='#D55D60'; INK='#203549'
COLORS=[BLUE,TEAL,GOLD,RED,'#7C6AB1','#78A8BF','#A9BD83','#BA8670']
CAT={'Furniture':'家具','Office Supplies':'办公用品','Technology':'技术产品'}
REG={'Central':'中部','East':'东部','South':'南部','West':'西部'}
SEG={'Consumer':'个人消费者','Corporate':'企业客户','Home Office':'家庭办公'}
SUB={'Accessories':'配件','Appliances':'家电','Art':'美术用品','Binders':'装订用品','Bookcases':'书柜','Chairs':'椅子','Copiers':'复印机','Envelopes':'信封','Fasteners':'紧固件','Furnishings':'家居用品','Labels':'标签','Machines':'设备','Paper':'纸张','Phones':'电话','Storage':'收纳','Supplies':'耗材','Tables':'桌子'}

def setup():
    for p in (ROOT/'assets/fonts').glob('*.otf'):font_manager.fontManager.addfont(str(p))
    for p in Path('/root/.local/share/fonts').glob('*.otf'):font_manager.fontManager.addfont(str(p))
    available={f.name for f in font_manager.fontManager.ttflist}
    font=next((n for n in ['Course Report Sans','Microsoft YaHei','SimHei','Noto Sans CJK SC','Source Han Sans SC'] if n in available),'DejaVu Sans')
    plt.rcParams.update({'font.family':font,'axes.unicode_minus':False,'font.size':10,'axes.titlesize':14,
        'axes.titleweight':'bold','axes.labelcolor':INK,'text.color':INK,'axes.edgecolor':'#C5D2DB',
        'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','axes.facecolor':'white',
        'savefig.dpi':180,'axes.prop_cycle':matplotlib.cycler(color=COLORS)})

def fig_ax(title,ylabel='',size=(9.3,4.5)):
    fig,ax=plt.subplots(figsize=size);ax.set_title(title,loc='left',pad=16);ax.set_ylabel(ylabel)
    ax.grid(axis='y',alpha=.16);ax.set_axisbelow(True);return fig,ax

def save(fig,no,name,note='来源 官方 Superstore 教学样例  |  金额 USD  |  Python计算'):
    fig.text(.012,.012,note,fontsize=8,color='#677D8B')
    fig.tight_layout(rect=(0,.045,1,1));path=OUT/f'fig{no:02d}_{name}.png'
    buffer=BytesIO();fig.savefig(buffer,format='png');plt.close(fig)
    temp=path.with_suffix('.png.tmp');temp.write_bytes(buffer.getvalue());temp.replace(path)
    return path.name

def create_figures(z):
    OUT.mkdir(parents=True,exist_ok=True);setup();d=z['d'];m=z['monthly'];a=z['annual'];sub=z['sub'];index=[]
    def done(fig,n,name,kind,model='',note=None):
        filename=save(fig,n,name,**({'note':note} if note else {}));index.append({'编号':f'fig{n:02d}','文件':filename,'图形结构':kind,'对应模型':model,'图表类别':'描述分析图' if n<=10 else '业务模型图'})
    fig,ax=fig_ax('月度销售额及三个月移动平均','销售额 万USD')
    x=pd.to_datetime(m.index);ax.plot(x,m.Sales/1e4,label='月度销售额',lw=1.7);ax.plot(x,m.Sales.rolling(3).mean()/1e4,label='3个月移动平均',lw=2,color=GOLD)
    ax.legend(frameon=False,loc='upper left');done(fig,1,'销售趋势','双折线图','趋势')
    fig,ax=fig_ax('年度销售额与利润对比','金额 万USD');x=np.arange(len(a));w=.32
    ax.bar(x-w/2,a.Sales/1e4,w,label='销售额');ax.bar(x+w/2,a.Profit/1e4,w,label='利润',color=TEAL)
    ax.set_xticks(x,a.index);ax.legend(frameon=False)
    for i,v in enumerate(a.Sales/1e4):ax.text(i-w/2,v+.6,f'{v:.1f}',ha='center',fontsize=9)
    done(fig,2,'年度对比','分组柱形图','同比')
    ss=sub.sort_values('Profit');fig,ax=fig_ax('商品子品类利润排名','子品类',size=(9.3,5.7))
    ax.barh([SUB.get(n,n) for n in ss.index],ss.Profit/1e3,color=[RED if v<0 else BLUE for v in ss.Profit]);ax.set_xlabel('利润 千USD');ax.set_ylabel('');ax.axvline(0,color=INK,lw=.7)
    done(fig,3,'子品类利润','正负条形图')
    c=pd.crosstab(d.Region,d.Category,values=d.Sales,aggfunc='sum').fillna(0)
    fig,ax=fig_ax('区域销售结构','销售额 万USD');bottom=np.zeros(len(c))
    for i,col in enumerate(c.columns):ax.bar([REG[n] for n in c.index],c[col]/1e4,bottom=bottom,label=CAT[col],color=COLORS[i]);bottom+=c[col].values/1e4
    ax.legend(frameon=False,ncol=3,loc='upper left');done(fig,4,'区域品类结构','堆积柱形图')
    s=d.groupby('Segment').Sales.sum();fig,ax=plt.subplots(figsize=(9.3,4.5));ax.set_title('客户类型销售额占比',loc='left',weight='bold',pad=16)
    wedges,_,_=ax.pie(s.values,colors=COLORS[:3],wedgeprops={'width':.32,'edgecolor':'white'},autopct='%1.1f%%',pctdistance=.82,textprops={'fontsize':11})
    ax.text(0,0,f'{s.sum()/1e4:.1f}\n万USD',ha='center',va='center',weight='bold',fontsize=16)
    ax.legend(wedges,[SEG[n] for n in s.index],loc='center left',bbox_to_anchor=(1, .5),frameon=False);done(fig,5,'客户结构','环形图')
    bands=pd.cut(d.Discount,[-.001,0,.2,.4,1],labels=['无折扣','0至20%','20至40%','40%以上'])
    groups=[d.loc[bands.eq(g),'Margin']*100 for g in bands.cat.categories]
    fig,ax=fig_ax('折扣区间与明细利润率分布','明细利润率 %');b=ax.boxplot(groups,tick_labels=bands.cat.categories,patch_artist=True,showfliers=False)
    for patch,col in zip(b['boxes'],COLORS):patch.set_facecolor(col);patch.set_alpha(.65)
    ax.axhline(0,color=RED,lw=.9,ls='--');done(fig,6,'折扣利润率','箱线图',note='来源 官方教学样例 | 须区分相关与因果 | 箱线图不显示离群点 原始数据未删减')
    cols=['Sales','Profit','Quantity','Discount','Ship Days'];labels=['销售额','利润','数量','折扣','发货天数'];corr=d[cols].corr()
    fig,ax=fig_ax('数值指标相关系数矩阵');im=ax.imshow(corr,vmin=-1,vmax=1,cmap='RdBu_r');ax.set_xticks(range(5),labels);ax.set_yticks(range(5),labels);ax.grid(False)
    for i in range(5):
        for j in range(5):ax.text(j,i,f'{corr.iloc[i,j]:.2f}',ha='center',va='center',color='white' if abs(corr.iloc[i,j])>.65 else INK)
    fig.colorbar(im,ax=ax,label='Pearson r');done(fig,7,'相关热力','热力图')
    p=z['abc'];fig,ax=fig_ax('单品累计销售额分布','商品数量')
    ax.hist(p.Sales,bins=np.geomspace(p.Sales.min(),p.Sales.max(),25),color=BLUE,edgecolor='white');ax.set_xscale('log');ax.set_xlabel('单品累计销售额 USD 对数刻度');done(fig,8,'商品分布','对数直方图')
    vals=d.groupby('Category').Sales.sum();fig,ax=plt.subplots(figsize=(9.3,4.5),subplot_kw={'projection':'polar'})
    theta=np.linspace(0,2*np.pi,3,endpoint=False);ax.bar(theta,vals/1e4,width=1.3,color=COLORS[:3],alpha=.9)
    ax.set_xticks(theta,[CAT[n] for n in vals.index]);ax.set_title('品类销售规模极坐标对比',loc='left',pad=23,weight='bold');ax.set_ylabel('万USD',labelpad=25);done(fig,9,'品类极坐标','极坐标柱形图')
    reg=d.groupby('Region').Profit.sum();fig,ax=fig_ax('区域利润贡献分解','利润 万USD');total=0
    for i,(name,v) in enumerate(reg.items()):
        ax.bar(i,v/1e4,bottom=total/1e4,color=COLORS[i]);ax.text(i,(total+v/2)/1e4,f'{v/1e4:.1f}',ha='center',va='center',color='white');total+=v
    ax.bar(4,total/1e4,color=INK);ax.set_xticks(range(5),[REG[n] for n in reg.index]+['合计']);done(fig,10,'利润瀑布','瀑布图')
    r=z['rfm'];rt=z['rfm_thresholds'];fig,ax=fig_ax('2021年客户活跃度与购买频次','订单频次 次')
    scatter=ax.scatter(r.R,r.F,s=20+240*r.M/r.M.max(),c=r.Profit,cmap='RdYlBu',alpha=.65,edgecolors='white',lw=.3)
    ax.axvline(rt['R'],color=RED,ls='--');ax.axhline(rt['F'],color=RED,ls='--');ax.set_xlabel('距末次购买天数 天 越低越活跃');fig.colorbar(scatter,ax=ax,label='客户利润 USD')
    done(fig,11,'RFM气泡','气泡散点图','RFM',note='2021年客户 | 气泡面积按M线性缩放 | 虚线为R与F中位数 | RFM不代表盈利分层')
    rs=z['rfm_groups'].sort_values('Sales');fig,ax=fig_ax('RFM八类客户的销售与利润贡献','',size=(9.3,5.2));x=np.arange(len(rs))
    ax.barh(x-.16,rs.Sales/1e4,.32,label='销售额');ax.barh(x+.16,rs.Profit/1e4,.32,label='利润',color=TEAL);ax.set_yticks(x,rs.Group);ax.set_xlabel('金额 万USD');ax.legend(frameon=False)
    done(fig,12,'RFM贡献','分组条形图','RFM')
    fig,ax=fig_ax('商品销售额帕累托曲线','累计销售占比 %');ax.plot(p.Rank/len(p)*100,p['Cum Share']*100,lw=2)
    for limit,col in [(.8,TEAL),(.95,GOLD)]:
        n=p.loc[p['Cum Share']>=limit,'Rank'].iloc[0];ax.axhline(limit*100,color=col,ls='--');ax.axvline(n/len(p)*100,color=col,ls='--');ax.text(n/len(p)*100+1,limit*100-6,f'{n}个商品',color=col)
    ax.set_xlabel('按销售额降序累计商品占比 %');ax.set_ylim(0,104);done(fig,13,'ABC帕累托','帕累托曲线','ABC')
    abc=z['abc_summary'];fig,ax=fig_ax('ABC商品数量占比与销售占比','占比 %');x=np.arange(3)
    ax.bar(x-.17,abc['Product Share']*100,.34,label='商品数量占比');ax.bar(x+.17,abc['Sales Share']*100,.34,label='销售额占比',color=TEAL);ax.set_xticks(x,abc.ABC);ax.legend(frameon=False)
    done(fig,14,'ABC结构','分组柱形图','ABC')
    co=z['cohort'].iloc[:24,:13];fig,ax=fig_ax('前24个首购同期群的月度复购留存','首购月份',size=(9.3,6.9))
    masked=np.ma.masked_invalid(co.to_numpy());im=ax.imshow(masked,aspect='auto',vmin=0,vmax=1,cmap='YlGnBu');ax.grid(False);ax.set_xticks(range(13),range(13));ax.set_xlabel('距首购月份 月');ax.set_yticks(range(len(co)),co.index.astype(str));ax.tick_params(labelsize=8)
    for i in range(len(co)):
        for j in range(13):
            if pd.notna(co.iloc[i,j]):ax.text(j,i,f'{co.iloc[i,j]:.0%}',ha='center',va='center',fontsize=7,color='white' if co.iloc[i,j]>.45 else INK)
    fig.colorbar(im,ax=ax,format=ticker.PercentFormatter(1));done(fig,15,'同期群热力','留存热力图','同期群',note='同一客户每月仅计一次 | 月0为首购月 | 全48个同期群含右删失数据见结果表')
    w=z['retention'];fig,ax=fig_ax('首购后1至12个月的加权复购留存','当月复购留存率 %');ax.plot(w.Age.iloc[1:],w.Rate.iloc[1:]*100,marker='o',color=TEAL);ax.set_xticks(range(1,13));ax.set_xlabel('距首购月份 月');ax.set_ylim(0,16)
    for i in [1,3,6,12]:ax.annotate(f'{w.loc[i,"Rate"]:.1%}\nn={w.loc[i,"Eligible Customers"]}',(i,w.loc[i,'Rate']*100),xytext=(4,12),textcoords='offset points',fontsize=8)
    done(fig,16,'留存曲线','加权留存折线','同期群',note='分母只纳入可观察到对应月龄的首购客户 | 指定月份的复购率 非连续留存或流失概率')
    last=m.iloc[-12:];fig,ax=fig_ax('2021年月度销售额同比与环比','增长率 %');x=np.arange(12)
    ax.bar(x-.17,last.MoM*100,.34,label='环比',color=TEAL);ax.bar(x+.17,last.YoY*100,.34,label='同比',color=BLUE);ax.set_xticks(x,[s[5:]+'月' for s in last.index]);ax.axhline(0,color=INK,lw=.8);ax.legend(frameon=False)
    done(fig,17,'同比环比','正负分组柱形图','趋势')
    y=z['y'];future=z['future'];fx=pd.to_datetime(future.Month);fig,ax=fig_ax('历史销售与未来六个月教学预测','销售额 万USD');ax.plot(y.index,y/1e4,label='历史观测');ax.plot(fx,future.Forecast/1e4,color=TEAL,ls='--',marker='o',label='Holt Winters点预测');ax.fill_between(fx,future.Lower95/1e4,future.Upper95/1e4,color=TEAL,alpha=.18,label='95%预测区间');ax.legend(frameon=False,loc='upper left',fontsize=9)
    done(fig,18,'销售预测','预测区间图','Holt Winters',note='历史数据截至2021年 | 残差bootstrap3000次 seed42 | 条件预测区间不含参数不确定性')
    b=z['back'];fig,ax=fig_ax('2021年留出集回测对比','销售额 万USD');bx=pd.to_datetime(b.Month)
    ax.plot(bx,b.Actual/1e4,label='实际',marker='o');ax.plot(bx,b.ETS/1e4,label='Holt Winters',ls='--');ax.plot(bx,b['Seasonal Naive']/1e4,label='季节朴素基线',ls=':',color=GOLD);ax.legend(frameon=False)
    metrics=z['forecast_meta']['ets'];done(fig,19,'预测回测','回测对比图','Holt Winters',note=f'仅用2018至2020年训练 2021年测试 | MAPE {metrics["MAPE"]:.2f}% | RMSE {metrics["RMSE"]:,.0f} USD')
    pd.DataFrame(index).to_csv(ROOT/'outputs/tables/figure_index.csv',index=False,encoding='utf-8-sig')
    print(f'图表生成完成 {len(index)} 张，分辨率180dpi。')

if __name__=='__main__':
    from .pipeline import run_analysis
    create_figures(run_analysis())
