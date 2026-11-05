"""Extract only the datasets needed by the seven visualizations."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]


def import_workbook(source):
    source = Path(source).resolve()
    out = ROOT / 'data'
    out.mkdir(exist_ok=True)
    sheet_names = pd.ExcelFile(source, engine='openpyxl').sheet_names
    specs = [
        ('01_monthly_sales.csv', sheet_names[0], 'B:H', 2, 6),
        ('02_department_months.csv', sheet_names[1], 'B:F', 2, 6),
        ('03_traffic_periods.csv', sheet_names[2], 'B:G', 2, 2),
        ('06_yujue_periods.csv', sheet_names[6], 'B:F', 2, 2),
        ('07_region_months.csv', sheet_names[7], 'B:H', 1, 6),
    ]
    for filename, sheet, cols, header, nrows in specs:
        frame = pd.read_excel(source, sheet_name=sheet, usecols=cols, header=header,
                              nrows=nrows, engine='openpyxl')
        frame.columns = [str(c).strip() for c in frame.columns]
        frame.to_csv(out / filename, index=False, encoding='utf-8-sig')

    raw = pd.read_excel(source, sheet_name=sheet_names[3], usecols='B:F', header=2,
                        nrows=3, engine='openpyxl').set_index('类别')
    products = pd.DataFrame({'商品': raw.columns, '销售额': raw.loc['销售额'].to_numpy(),
                            '利润': raw.loc['利润'].to_numpy()})
    products.to_csv(out / '04_products.csv', index=False, encoding='utf-8-sig')

    # 原切片器仅按部门筛选、按学历汇总平均月收入。
    # 保留人数与收入合计即可精确重算任意部门组合，无需员工号或逐人明细。
    hr = pd.read_excel(source, sheet_name=sheet_names[4], engine='openpyxl',
                       usecols=['部门', '学历', '月收入'])
    grouped = hr.groupby(['部门', '学历'], sort=True).agg(
        人数=('月收入', 'size'), 月收入合计=('月收入', 'sum')).reset_index()
    grouped.to_csv(out / '05_hr_department_education.csv', index=False, encoding='utf-8-sig')

    book = load_workbook(source, read_only=True, data_only=True)
    months = pd.read_csv(out/'01_monthly_sales.csv').iloc[:, 0].tolist()
    default_month = months[max(0, min(len(months)-1, int(book[sheet_names[0]]['J3'].value)-1))]
    department_month = book[sheet_names[1]]['Q5'].value
    if department_month not in ['1月', '2月', '3月', '4月']:
        department_month = '1月'
    period_index = int(book[sheet_names[2]]['I3'].value or 1)-1
    periods = pd.read_csv(out/'03_traffic_periods.csv')['周期'].tolist()
    default_period = periods[max(0, min(len(periods)-1, period_index))]
    yujue_period = book[sheet_names[6]]['H3'].value
    target_mean = float(book[sheet_names[5]]['C9'].value)
    means = hr.groupby('部门')['月收入'].mean()
    selected_department = (means-target_mean).abs().idxmin()
    if abs(means[selected_department]-target_mean) > 1e-6:
        selected_departments = sorted(hr['部门'].unique().tolist())
    else:
        selected_departments = [selected_department]
    education_order = [book[sheet_names[5]].cell(i, 2).value for i in range(4, 9)]
    book.close()

    ns = {'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart',
          'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
    styles = {}
    with zipfile.ZipFile(source) as archive:
        for number in range(1, 8):
            chart = ET.fromstring(archive.read(f'xl/charts/chart{number}.xml'))
            layout = chart.find('c:chart/c:plotArea/c:layout/c:manualLayout', ns)
            coords = {x.tag.split('}')[-1]: x.get('val') for x in layout} if layout is not None else {}
            plot = [float(coords[k]) for k in ['x', 'y', 'w', 'h']] if all(k in coords for k in ['x','y','w','h']) else None
            hole = chart.find('.//c:holeSize', ns)
            styles[str(number)] = {'plot': plot,
                'hole': int(hole.get('val'))/100 if hole is not None else None,
                'background': '#1A1E43'}
    (out/'styles.json').write_text(json.dumps(styles, ensure_ascii=False, indent=2), encoding='utf-8')
    manifest = {
        'source_file': source.name, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'source_sheets': sheet_names, 'example_count': 7, 'employee_count': len(hr),
        'education_order': education_order,
        'hr_export': 'department × education counts and income sums; no employee-level records',
        'defaults': {'1': {'month': default_month}, '2': {'month': department_month},
            '3': {'period': default_period}, '4': {'sales': True, 'profit': True, 'margin': True},
            '5': {'departments': selected_departments}, '6': {'period': yujue_period},
            '7': {'axis': '月份', 'selection': '1月'}},
        'original_pivot': {'department': selected_departments, 'overall_average': target_mean},
    }
    (out/'source_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'已提取 7 组数据；人力资源仅保存汇总分组，覆盖 {len(hr)} 条记录。')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='从本地原始 xlsm 更新本项目数据；不执行宏。')
    parser.add_argument('excel', type=Path)
    import_workbook(parser.parse_args().excel)
