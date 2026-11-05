"""数据治理和商业模型。所有统计以官方下载的同一份订单明细为依据。"""
from pathlib import Path
import hashlib
import json
import sqlite3
import urllib.request
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw/Sample_Superstore.xls'
CLEAN = ROOT / 'data/clean'
TABLES = ROOT / 'outputs/tables'
SOURCE_URL = 'https://www.tableau.com/sites/default/files/2021-05/Sample%20-%20Superstore.xls'
SEED = 42
SEGMENTS = {'111':'高价值活跃','110':'活跃高频低额','101':'活跃低频高额','100':'活跃低频低额',
            '011':'高价值沉睡','010':'沉睡高频低额','001':'沉睡低频高额','000':'沉睡低频低额'}

def write_json(obj, path):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding='utf-8')

def acquire():
    """仅下载指定的官方二进制文件，不获取网页，不解析网页。优先复用附带原件。"""
    RAW.parent.mkdir(parents=True, exist_ok=True)
    if not RAW.exists():
        urllib.request.urlretrieve(SOURCE_URL, RAW)
    sha = hashlib.sha256(RAW.read_bytes()).hexdigest()
    expected = '03d9e99f29755e641075b0caedf00d10e9416fda3668039dc7c9982500a329fc'
    if sha != expected:
        raise ValueError('原始文件版本与报告不一致，请核对 SHA256，禁止静默更换数据。')
    return {'source':SOURCE_URL, 'acquired_date':'2026-11-04', 'sha256':sha,
            'license':'官方公开教学样例；下载页未单列开放数据许可，不宣称 CC 或公有领域。',
            'nature':'虚构零售公司的教学数据，非真实企业交易', 'sampling':'全量，不抽样，不补造数据'}

def clean_data():
    CLEAN.mkdir(parents=True, exist_ok=True); TABLES.mkdir(parents=True, exist_ok=True)
    d = pd.read_excel(RAW, sheet_name='Orders')
    people = pd.read_excel(RAW, sheet_name='People')
    ret = pd.read_excel(RAW, sheet_name='Returns')
    audit = {'raw_rows':len(d), 'raw_columns':d.shape[1], 'exact_duplicates':int(d.duplicated().sum()),
             'postal_missing':int(d['Postal Code'].isna().sum()), 'returns_raw_rows':len(ret),
             'returns_unique_orders':ret['Order ID'].nunique()}
    d = d.drop_duplicates().copy()
    if d['Row ID'].duplicated().any():
        raise ValueError('Row ID 主键冲突，不可任意保留一行。')
    for c in ['Order Date','Ship Date']:
        d[c] = pd.to_datetime(d[c], errors='coerce')
    for c in ['Sales','Quantity','Discount','Profit']:
        d[c] = pd.to_numeric(d[c], errors='coerce')
    # 邮编是标识字段，不作为连续数值；缺失值明确标记。
    d['Postal Code'] = d['Postal Code'].map(lambda x: 'UNKNOWN' if pd.isna(x) else f'{int(x):05d}')
    critical = ['Order ID','Customer ID','Product ID','Order Date','Ship Date','Sales','Quantity','Discount','Profit']
    bad = d[critical].isna().any(axis=1) | (d['Sales'] <= 0) | (d['Quantity'] <= 0) | ~d['Discount'].between(0,1) | (d['Ship Date'] < d['Order Date'])
    audit['invalid_rows'] = int(bad.sum())
    d.loc[bad].to_csv(TABLES/'quarantined_rows.csv', index=False, encoding='utf-8-sig')
    d = d.loc[~bad].copy()
    audit['negative_profit_rows'] = int(d['Profit'].lt(0).sum())
    q1,q3=d['Sales'].quantile([.25,.75]); audit['sales_iqr_flags']=int(d['Sales'].gt(q3+1.5*(q3-q1)).sum())
    audit['product_name_conflict_ids'] = int(d.groupby('Product ID')['Product Name'].nunique().gt(1).sum())
    audit['returns_removed_duplicates'] = int(ret.duplicated('Order ID').sum())
    audit['unmatched_return_orders'] = int((~ret['Order ID'].isin(d['Order ID'])).sum())
    # Returns 只有订单级标识。去重后 m:1 关联，不能按明细重复关联，更不能推断退款金额。
    ret = ret[['Order ID','Returned']].drop_duplicates('Order ID')
    people = people.drop_duplicates()
    before = (len(d), d['Sales'].sum(), d['Profit'].sum())
    d = d.merge(ret, on='Order ID', how='left', validate='many_to_one')
    d['Returned'] = d['Returned'].eq('Yes')
    d = d.merge(people, on='Region', how='left', validate='many_to_one')
    assert d['Person'].notna().all(), '区域维表有未匹配项'
    after = (len(d), d['Sales'].sum(), d['Profit'].sum())
    assert before[0] == after[0] and np.allclose(before[1:],after[1:]), '多表关联改变了金额'
    d['Year'] = d['Order Date'].dt.year
    d['Month'] = d['Order Date'].dt.to_period('M').astype(str)
    d['Margin'] = d['Profit'] / d['Sales']
    d['Ship Days'] = (d['Ship Date']-d['Order Date']).dt.days
    d['Loss'] = d['Profit'] < 0
    customer_dim = d[['Customer ID','Customer Name','Segment']].drop_duplicates()
    assert not customer_dim['Customer ID'].duplicated().any()
    # 只导出一致的商品属性；有冲突的商品名保留在原始明细中，不任意建立一对一名称映射。
    product_dim = d[['Product ID','Category','Sub-Category']].drop_duplicates()
    assert not product_dim['Product ID'].duplicated().any()
    d.to_csv(CLEAN/'orders.csv',index=False,encoding='utf-8-sig')
    customer_dim.to_csv(CLEAN/'customers.csv',index=False,encoding='utf-8-sig')
    product_dim.to_csv(CLEAN/'products.csv',index=False,encoding='utf-8-sig')
    ret.to_csv(CLEAN/'returns.csv',index=False,encoding='utf-8-sig')
    with sqlite3.connect(CLEAN/'superstore.sqlite') as conn:
        d.to_sql('orders',conn,if_exists='replace',index=False)
        customer_dim.to_sql('customers',conn,if_exists='replace',index=False)
        product_dim.to_sql('products',conn,if_exists='replace',index=False)
    audit['clean_rows']=len(d); audit['join_amount_reconciled']=True
    write_json(audit,TABLES/'cleaning_audit.json')
    return d,audit

def rfm_model(d):
    """RFM 固定采用最后一个观测年份；F 数独立订单，不能数明细行。"""
    asof = d['Order Date'].max().normalize()+pd.Timedelta(days=1)
    start = pd.Timestamp(year=d['Year'].max(),month=1,day=1)
    recent=d[d['Order Date'].between(start,asof,inclusive='left')]
    g=recent.groupby('Customer ID').agg(Last=('Order Date','max'),F=('Order ID','nunique'),M=('Sales','sum'),Profit=('Profit','sum'))
    g['R']=(asof-g.pop('Last')).dt.days
    med=g[['R','F','M']].median()
    # 等于中位数归入高组，以使并列客户得到一致分类。
    g['R_high']=(g['R']<=med['R']).astype(int)
    g['F_high']=(g['F']>=med['F']).astype(int)
    g['M_high']=(g['M']>=med['M']).astype(int)
    g['Code']=g[['R_high','F_high','M_high']].astype(str).agg(''.join,axis=1)
    g['Group']=g['Code'].map(SEGMENTS)
    g=g.reset_index()
    summary=g.groupby(['Code','Group']).agg(Customers=('Customer ID','size'),Sales=('M','sum'),Profit=('Profit','sum')).reset_index()
    summary['Customer Share']=summary['Customers']/len(g)
    summary['Sales Share']=summary['Sales']/summary['Sales'].sum()
    thresholds={'asof':str(asof.date()),'start':str(start.date()),'R':float(med['R']),'F':float(med['F']),'M':float(med['M']),
                'active_customers':len(g),'inactive_customers':d['Customer ID'].nunique()-len(g)}
    g.to_csv(TABLES/'rfm_customers.csv',index=False,encoding='utf-8-sig')
    summary.to_csv(TABLES/'rfm_groups.csv',index=False,encoding='utf-8-sig')
    write_json(thresholds,TABLES/'rfm_thresholds.json')
    return g,summary,thresholds

def abc_model(d):
    p=d.groupby('Product ID').agg(Sales=('Sales','sum'),Profit=('Profit','sum'),Quantity=('Quantity','sum')).reset_index()
    p=p.sort_values(['Sales','Product ID'],ascending=[False,True]).reset_index(drop=True)
    p['Rank']=np.arange(1,len(p)+1); p['Sales Share']=p['Sales']/p['Sales'].sum(); p['Cum Share']=p['Sales Share'].cumsum()
    # 按前一项累计份额分类：跨过80%和95%的那一项分别归入A和B，保证覆盖目标。
    before=p['Cum Share']-p['Sales Share']
    p['ABC']=np.select([before<.8,before<.95],['A','B'],default='C')
    a=p.groupby('ABC').agg(Products=('Product ID','size'),Sales=('Sales','sum'),Profit=('Profit','sum')).reindex(['A','B','C']).reset_index()
    a['Product Share']=a['Products']/len(p); a['Sales Share']=a['Sales']/p['Sales'].sum()
    p.to_csv(TABLES/'abc_products.csv',index=False,encoding='utf-8-sig'); a.to_csv(TABLES/'abc_summary.csv',index=False,encoding='utf-8-sig')
    return p,a

def cohort_model(d):
    active=d[['Customer ID','Month']].drop_duplicates().copy()
    active['Period']=pd.PeriodIndex(active['Month'],freq='M')
    first=active.groupby('Customer ID')['Period'].min()
    active['Cohort']=active['Customer ID'].map(first)
    active['Age']=(active['Period'].astype('int64')-pd.PeriodIndex(active['Cohort'],freq='M').asi8).astype(int)
    counts=active.pivot_table(index='Cohort',columns='Age',values='Customer ID',aggfunc='nunique',fill_value=0).astype(float)
    last=active['Period'].max()
    # 未来尚未观测的单元格为 NaN，不得填0。
    for cohort in counts.index:
        counts.loc[cohort,counts.columns>last.ordinal-cohort.ordinal]=np.nan
    sizes=counts[0].copy(); rates=counts.div(sizes,axis=0)
    weighted=[]
    for age in range(13):
        eligible=(last.ordinal-counts.index.asi8)>=age
        denom=sizes.loc[eligible].sum(); num=counts.loc[eligible,age].sum()
        weighted.append({'Age':age,'Rate':float(num/denom),'Eligible Customers':int(denom),'Returning Customers':int(num)})
    counts.to_csv(TABLES/'cohort_counts.csv',encoding='utf-8-sig');rates.to_csv(TABLES/'cohort_rates.csv',encoding='utf-8-sig')
    pd.DataFrame(weighted).to_csv(TABLES/'cohort_weighted.csv',index=False,encoding='utf-8-sig')
    return rates,pd.DataFrame(weighted)

def forecast_model(d):
    y=d.groupby('Month')['Sales'].sum();y.index=pd.to_datetime(y.index); y=y.asfreq('MS')
    assert y.notna().all(), '月度时间序列缺月'
    train,test=y.iloc[:-12],y.iloc[-12:]
    def fit(s):
        return ExponentialSmoothing(s,trend='add',damped_trend=True,seasonal='add',seasonal_periods=12,initialization_method='estimated').fit(optimized=True,use_brute=True)
    fit_train=fit(train); predicted=fit_train.forecast(12)
    naive=pd.Series(train.iloc[-12:].values,index=test.index)
    def metrics(a,b):
        return {'MAPE':float((abs((a-b)/a)).mean()*100),'RMSE':float(np.sqrt(((a-b)**2).mean()))}
    metrics_ets=metrics(test,predicted); metrics_naive=metrics(test,naive)
    full=fit(y); fc=full.forecast(6)
    # Bootstrap 重采样已中心化拟合残差，模拟误差传播，给出逐期预测区间。
    residual=np.asarray(full.resid); residual=residual-residual.mean()
    rng=np.random.RandomState(SEED)
    errors=rng.choice(residual,size=(6,3000),replace=True)
    sims=np.asarray(full.simulate(nsimulations=6,repetitions=3000,anchor='end',random_errors=errors))
    lo,hi=np.quantile(sims,[.025,.975],axis=1)
    future=pd.DataFrame({'Month':fc.index.strftime('%Y-%m'),'Forecast':fc.values,'Lower95':lo,'Upper95':hi})
    back=pd.DataFrame({'Month':test.index.strftime('%Y-%m'),'Actual':test.values,'ETS':predicted.values,'Seasonal Naive':naive.values})
    future.to_csv(TABLES/'forecast.csv',index=False,encoding='utf-8-sig');back.to_csv(TABLES/'backtest.csv',index=False,encoding='utf-8-sig')
    meta={'model':'加性阻尼趋势 加性季节 Holt Winters','period':12,'train_months':len(train),'test_months':12,'horizon':6,
          'bootstrap_repetitions':3000,'seed':SEED,'ets':metrics_ets,'seasonal_naive':metrics_naive,
          'interval':'条件于固定拟合参数的残差bootstrap 95%预测区间，不含参数不确定性；仅教学历史外推'}
    write_json(meta,TABLES/'forecast_metrics.json')
    return y,back,future,meta

def analyze(d):
    r,rs,rt=rfm_model(d);p,a=abc_model(d);co,weighted=cohort_model(d); y,back,future,fcmeta=forecast_model(d)
    annual=d.groupby('Year').agg(Sales=('Sales','sum'),Profit=('Profit','sum'),Orders=('Order ID','nunique'))
    annual['Margin']=annual['Profit']/annual['Sales'];annual['YoY']=annual['Sales'].pct_change()
    monthly=d.groupby('Month').agg(Sales=('Sales','sum'),Profit=('Profit','sum'),Orders=('Order ID','nunique'))
    monthly['MoM']=monthly['Sales'].pct_change();monthly['YoY']=monthly['Sales'].pct_change(12)
    sub=d.groupby('Sub-Category').agg(Sales=('Sales','sum'),Profit=('Profit','sum'))
    sub['Margin']=sub['Profit']/sub['Sales']
    disc=d.assign(Band=pd.cut(d['Discount'],[-.001,0,.2,.4,1],labels=['无折扣','0至20%','20至40%','40%以上']))
    ds=disc.groupby('Band',observed=False).agg(Lines=('Row ID','size'),Sales=('Sales','sum'),Profit=('Profit','sum'))
    ds['Margin']=ds['Profit']/ds['Sales']
    for name,df in [('annual',annual),('monthly',monthly),('subcategories',sub),('discount_bands',ds)]:df.to_csv(TABLES/f'{name}.csv',encoding='utf-8-sig')
    order_flags=d.groupby('Order ID')['Returned'].max()
    all_order_profit=d.groupby('Order ID')['Profit'].sum()
    summary={'rows':len(d),'orders':d['Order ID'].nunique(),'customers':d['Customer ID'].nunique(),'products':d['Product ID'].nunique(),
             'date_min':str(d['Order Date'].min().date()),'date_max':str(d['Order Date'].max().date()),
             'sales':d['Sales'].sum(),'profit':d['Profit'].sum(),'margin':d['Profit'].sum()/d['Sales'].sum(),
             'loss_lines':int(d['Profit'].lt(0).sum()),'loss_line_share':float(d['Profit'].lt(0).mean()),
             'negative_profit_total':d.loc[d['Profit']<0,'Profit'].sum(),'loss_orders':int(all_order_profit.lt(0).sum()),
             'returned_orders':int(order_flags.sum()),'returned_order_share':float(order_flags.mean()),
             'q4_sales_share':d.loc[d['Order Date'].dt.quarter==4,'Sales'].sum()/d['Sales'].sum(),
             'recent_rfm':rt, 'forecast':fcmeta}
    write_json(summary,TABLES/'summary.json')
    return {'d':d,'rfm':r,'rfm_groups':rs,'rfm_thresholds':rt,'abc':p,'abc_summary':a,'cohort':co,'retention':weighted,
            'y':y,'back':back,'future':future,'forecast_meta':fcmeta,'annual':annual,'monthly':monthly,'sub':sub,'discount':ds,'summary':summary}

def run_analysis():
    provenance=acquire();write_json(provenance,RAW.parent/'provenance.json')
    d,audit=clean_data(); result=analyze(d)
    print(f"原始/清洗明细 {audit['raw_rows']}/{len(d)}；订单 {d['Order ID'].nunique()}；客户 {d['Customer ID'].nunique()}")
    print(f"销售额 {d['Sales'].sum():,.2f}；利润 {d['Profit'].sum():,.2f}")
    return result

if __name__=='__main__':run_analysis()
