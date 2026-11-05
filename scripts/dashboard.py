"""启动：python -m streamlit run dashboard.py 。筛选器驱动所有组件的同一份数据。"""
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='Superstore经营分析',page_icon='📊',layout='wide')
st.title('Superstore零售经营分析')
st.caption('官方虚构教学样例 · 2018—2021年历史数据 · 金额 USD · 全部图表由Python生成')

@st.cache_data
def load():
    return pd.read_csv(ROOT/'data/clean/orders.csv',parse_dates=['Order Date','Ship Date'])

df=load()
st.sidebar.header('联动筛选')
dates=st.sidebar.date_input('订单日期范围',(df['Order Date'].min().date(),df['Order Date'].max().date()),
    min_value=df['Order Date'].min().date(),max_value=df['Order Date'].max().date())
regions=st.sidebar.multiselect('区域',sorted(df.Region.unique()),default=sorted(df.Region.unique()))
categories=st.sidebar.multiselect('品类',sorted(df.Category.unique()),default=sorted(df.Category.unique()))
segments=st.sidebar.multiselect('客户类型',sorted(df.Segment.unique()),default=sorted(df.Segment.unique()))
if len(dates)!=2:
    st.info('请选择开始与结束日期。');st.stop()
f=df[df['Order Date'].between(pd.Timestamp(dates[0]),pd.Timestamp(dates[1])+pd.Timedelta(days=1),inclusive='left') & df.Region.isin(regions) & df.Category.isin(categories) & df.Segment.isin(segments)].copy()
if f.empty:
    st.info('当前条件没有记录，请调整筛选。');st.stop()
sales=f.Sales.sum();profit=f.Profit.sum();orders=f['Order ID'].nunique()
cols=st.columns(4)
for col,label,value in zip(cols,['销售额 USD','利润 USD','综合利润率','订单数'],[f'{sales:,.2f}',f'{profit:,.2f}',f'{profit/sales:.2%}',f'{orders:,}']):col.metric(label,value)
st.caption(f'当前范围：{len(f):,}条明细，{f["Customer ID"].nunique():,}位客户。所有下方组件均随侧栏条件更新。')
c1,c2=st.columns([1.45,1])
monthly=f.groupby('Month',as_index=False)[['Sales','Profit']].sum()
with c1:
    st.subheader('月度经营趋势')
    st.plotly_chart(px.line(monthly,x='Month',y=['Sales','Profit'],labels={'value':'金额 USD','variable':'指标'},color_discrete_sequence=['#2676A9','#199C99']),width='stretch',key='trend')
with c2:
    st.subheader('品类销售结构')
    cg=f.groupby('Category',as_index=False).Sales.sum()
    st.plotly_chart(px.pie(cg,names='Category',values='Sales',hole=.6,color_discrete_sequence=['#2676A9','#199C99','#E6AD42']),width='stretch',key='category')
c3,c4=st.columns(2)
with c3:
    st.subheader('区域规模与盈利')
    rg=f.groupby('Region',as_index=False).agg(Sales=('Sales','sum'),Profit=('Profit','sum'),Quantity=('Quantity','sum'))
    st.plotly_chart(px.scatter(rg,x='Sales',y='Profit',size='Quantity',color='Region',text='Region',labels={'Sales':'销售额 USD','Profit':'利润 USD'}),width='stretch',key='region')
with c4:
    st.subheader('子品类利润排名')
    sg=f.groupby('Sub-Category',as_index=False).Profit.sum().sort_values('Profit')
    st.plotly_chart(px.bar(sg,x='Profit',y='Sub-Category',orientation='h',color='Profit',color_continuous_scale='RdBu',color_continuous_midpoint=0,labels={'Profit':'利润 USD'}),width='stretch',key='ranking')
c5,c6=st.columns(2)
with c5:
    st.subheader('客户销售贡献')
    cust=f.groupby('Customer ID',as_index=False).agg(Sales=('Sales','sum'),Profit=('Profit','sum'),Orders=('Order ID','nunique'))
    st.plotly_chart(px.scatter(cust,x='Sales',y='Profit',size='Orders',hover_name='Customer ID',color='Profit',color_continuous_scale='RdBu',color_continuous_midpoint=0,labels={'Sales':'销售额 USD','Profit':'利润 USD'}),width='stretch',key='customers')
with c6:
    st.subheader('折扣与利润率')
    f['折扣区间']=pd.cut(f.Discount,[-.001,0,.2,.4,1],labels=['无折扣','0至20%','20至40%','40%以上'])
    dg=f.groupby('折扣区间',observed=True).agg(Sales=('Sales','sum'),Profit=('Profit','sum')).reset_index()
    dg['利润率 %']=dg.Profit/dg.Sales*100
    st.plotly_chart(px.bar(dg,x='折扣区间',y='利润率 %',color='利润率 %',color_continuous_scale='RdBu',color_continuous_midpoint=0),width='stretch',key='discount')
st.subheader('当前筛选明细')
st.dataframe(f[['Order ID','Order Date','Region','Category','Sub-Category','Customer ID','Sales','Profit','Discount','Returned']],hide_index=True,width='stretch')
st.download_button('下载当前筛选数据 CSV',f.to_csv(index=False).encode('utf-8-sig'),'filtered_orders.csv','text/csv')
st.caption('退货标识不等于退款金额；利润沿用原始字段，未对退货重复扣减。折扣与利润率的关系为描述性相关。')

with st.expander('教材模板复现对照 30幅'):
    mapping=pd.read_csv(ROOT/'outputs/tables/template_mapping.csv',dtype={'页内图块':str})
    options=(mapping['编号']+' '+mapping['模板名称']).tolist()
    chosen=st.selectbox('选择教材模板',options)
    row=mapping.iloc[options.index(chosen)]
    st.caption(f'参考PPT第{row["PPT页码"]}页 图块{row["页内图块"]}。模板图采用图中注明的历史范围，上方经营筛选不改写模板的统计口径。')
    left,right=st.columns(2)
    with left:st.image(str(ROOT/'assets/reference'/row['参考图片']),caption='教材参考图',width='stretch')
    with right:st.image(str(ROOT/'outputs/templates'/row['复现图片']),caption='Python复现图',width='stretch')
    st.write('指标口径：'+row['指标口径'])
    st.write('适配说明：'+row['适配说明'])
