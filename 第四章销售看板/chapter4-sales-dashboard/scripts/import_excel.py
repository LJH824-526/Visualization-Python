from pathlib import Path
import argparse,json,hashlib
import numpy as np
import pandas as pd
from openpyxl import load_workbook

ROOT=Path(__file__).resolve().parents[1]


def import_workbook(path):
    path=Path(path).resolve()
    frame=pd.read_excel(path,sheet_name='销售明细',engine='openpyxl')
    costs=pd.read_excel(path,sheet_name='成本明细',engine='openpyxl')
    for col in ['订单额','利润额']:frame[col]=pd.to_numeric(frame[col],errors='raise')
    if frame[['订单额','利润额','月份_销售']].isna().any().any():raise ValueError('销售汇总所需字段存在空值。')
    out=ROOT/'data';out.mkdir(exist_ok=True)
    frame=frame.rename(columns={'月份_销售':'月份'})
    monthly=frame.groupby('月份',sort=False).agg(销量=('订单额','size'),销售额=('订单额','sum'),利润额=('利润额','sum')).reset_index()
    monthly['月份序号']=monthly['月份'].str.extract(r'(\d+)').astype(int)
    monthly=monthly.sort_values('月份序号').drop(columns='月份序号')
    monthly.to_csv(out/'monthly.csv',index=False,encoding='utf-8-sig')
    for column,filename in [('区域','region_month.csv'),('快递公司','courier_month.csv'),('产品类别','category_month.csv')]:
        grouped=frame.groupby(['月份',column],sort=False).size().rename('销量').reset_index()
        grouped.to_csv(out/filename,index=False,encoding='utf-8-sig')
    products=frame.groupby(['月份','产品名称'],sort=False).agg(销量=('订单额','size'),销售额=('订单额','sum'),利润额=('利润额','sum')).reset_index()
    products.to_csv(out/'product_month.csv',index=False,encoding='utf-8-sig')
    costs=costs.rename(columns={'月份_成本':'月份'})
    costs.to_csv(out/'cost_month.csv',index=False,encoding='utf-8-sig')
    book=load_workbook(path,read_only=True,data_only=True);sheet=book['统计数据']
    default=sheet['D2'].value
    manifest={'source_file':path.name,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
              'records':len(frame),'year':int(pd.to_datetime(frame['订单日期']).dt.year.mode().iloc[0]),
              'date_min':str(pd.to_datetime(frame['订单日期']).min().date()),'date_max':str(pd.to_datetime(frame['订单日期']).max().date()),
              'months':monthly['月份'].tolist(),'default_month':default,'default_theme':'展示参考',
              'regions':[sheet[f'D{i}'].value for i in range(9,15)],
              'couriers':[sheet[f'D{i}'].value for i in range(18,24)],
              'categories':[sheet[f'J{i}'].value for i in range(13,16)],
              'costs':[sheet[f'D{i}'].value for i in range(27,31)],
              'reference':{'month':default,'volume':int(sheet['I2'].value),'revenue_wan':float(sheet['K2'].value),
                           'profit_wan':float(sheet['M2'].value),'profit_margin':float(sheet['N3'].value),'cost':float(sheet['G2'].value)},
              'volume_definition':'count of sales detail rows, matching COUNTIFS in workbook',
              'cost_unit':'not explicitly specified in source; preserve original values',
              'export':'monthly and dimension aggregates; order identifiers and individual records excluded'}
    book.close();(out/'source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'已汇总 {len(frame)} 条销售记录、{len(monthly)} 个月；不导出订单单号或逐单记录。')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('excel',type=Path)
    import_workbook(parser.parse_args().excel)
