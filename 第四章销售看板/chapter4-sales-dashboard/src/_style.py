from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle,FancyBboxPatch,Wedge

ROOT=Path(__file__).resolve().parents[1]
for path in (ROOT/'assets/fonts').glob('*.otf'):
    font_manager.fontManager.addfont(str(path))
available={f.name for f in font_manager.fontManager.ttflist}
FONT=next((f for f in ['Microsoft YaHei','微软雅黑','Noto Sans CJK SC','SimHei','PingFang SC'] if f in available),None)
if FONT is None:raise RuntimeError('请保留 assets/fonts 字体目录或安装微软雅黑。')
plt.rcParams.update({'font.family':FONT,'axes.unicode_minus':False,'figure.dpi':100,
                     'savefig.dpi':140,'axes.linewidth':.6,'svg.fonttype':'path'})
WHITE='#F2F2F2'


def add_card(fig,bounds,color,edge=None,rounded=False):
    if rounded:
        patch=FancyBboxPatch(bounds[:2],bounds[2],bounds[3],transform=fig.transFigure,
                            boxstyle='round,pad=0,rounding_size=.010',facecolor=color,
                            edgecolor=edge or color,lw=.7,zorder=0)
    else:
        patch=Rectangle(bounds[:2],bounds[2],bounds[3],transform=fig.transFigure,
                        facecolor=color,edgecolor=edge or color,lw=.6,zorder=0)
    fig.add_artist(patch)


def clean_axis(fig,bounds,face,fg=WHITE):
    ax=fig.add_axes(bounds,facecolor=face,zorder=2)
    for sp in ax.spines.values():sp.set_visible(False)
    ax.tick_params(colors=fg,labelsize=9,length=0,pad=4)
    ax.set_axisbelow(True)
    return ax


def pie_ring(ax,labels,values,palette,hole=.75,fg=WHITE,center='',subtitle='',legend=True):
    values=np.asarray(values,dtype=float)
    if values.sum()<=0:
        ax.text(.5,.5,'暂无数据',transform=ax.transAxes,ha='center',color=fg);ax.axis('off');return
    wedges,_,texts=ax.pie(values,colors=palette,startangle=90,counterclock=False,
                         radius=.92,center=(-.25,0),wedgeprops={'width':.92*(1-hole),'edgecolor':'none'},
                         autopct=lambda p:f'{p:.0f}%' if p else '',pctdistance=1.17,
                         textprops={'color':fg,'fontsize':9})
    ax.set_xlim(-1.43,1.9);ax.set_ylim(-1.24,1.24);ax.axis('off')
    if legend:
        leg=ax.legend(wedges,labels,loc='center left',bbox_to_anchor=(.74,.5),frameon=False,
                      fontsize=8.5,handlelength=.7,handletextpad=.45,labelspacing=1.05)
        for t in leg.get_texts():t.set_color(fg)
    if center:ax.text(-.25,.05,center,ha='center',va='center',fontsize=29,weight='bold',color=fg)
    if subtitle:ax.text(-.25,-.39,subtitle,ha='center',va='center',fontsize=10,color=fg)


def small_ring(ax,rate,label,color,fg=WHITE,width=.15):
    ax.set_aspect('equal');ax.set_xlim(-1.16,1.16);ax.set_ylim(-1.16,1.16);ax.axis('off')
    ax.add_patch(Wedge((0,0),1,0,360,width=width,facecolor='#535D7A',edgecolor='none'))
    clipped=float(np.clip(rate,0,1))
    if clipped:ax.add_patch(Wedge((0,0),1,90-360*clipped,90,width=width,facecolor=color,edgecolor='none'))
    ax.text(0,0,label,ha='center',va='center',fontsize=13,color=fg)
