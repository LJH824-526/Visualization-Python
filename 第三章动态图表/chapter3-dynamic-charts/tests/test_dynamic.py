from pathlib import Path
import sys
import unittest
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import dynamic_charts as c


class DynamicTests(unittest.TestCase):
    def tearDown(self):
        plt.close('all')

    def test_month_switch_and_axis_bounds(self):
        for month in c.month_options(1):
            labels,values=c.row_values(1,month,'月份')
            fig=c.chart_1(month)
            np.testing.assert_allclose([b.get_height() for b in fig.axes[0].patches],values)
            self.assertGreaterEqual(fig.axes[0].get_ylim()[1],values.max())
            plt.close(fig)
        self.assertNotEqual(c.row_values(1,'1月','月份')[1].tolist(),c.row_values(1,'6月','月份')[1].tolist())

    def test_department_month_total(self):
        data=c.load_data(2)
        for month in c.month_options(2):
            fig=c.chart_2(month)
            self.assertTrue(any(f'{data[month].sum():g}' in t.get_text() for t in fig.texts))
            self.assertEqual(len(fig.axes[0].patches),len(data))
            plt.close(fig)

    def test_traffic_periods(self):
        for period in c.period_options(3):
            _,values=c.row_values(3,period,'周期')
            self.assertAlmostEqual(values.sum(),1)
            fig=c.chart_3(period)
            self.assertEqual(len(fig.axes[0].patches),5)
            plt.close(fig)

    def test_metric_toggles(self):
        for _,config in c.state_options(4):
            fig=c.chart_4(**config)
            self.assertEqual(len(fig.axes[0].patches),4*(config['sales']+config['profit']))
            self.assertEqual(len(fig.axes),2 if config['margin'] else 1)
            if not any(config.values()):
                self.assertTrue(any('请选择' in t.get_text() for t in fig.axes[0].texts))
            plt.close(fig)

    def test_hr_weighted_means_and_empty_selection(self):
        raw=c.load_data(5)
        self.assertNotIn('员工号',raw.columns)
        self.assertEqual(int(raw['人数'].sum()),c.MANIFEST['employee_count'])
        selected=c.DEFAULTS[5]['departments']
        summary=c.hr_summary(selected)
        self.assertAlmostEqual(summary.iloc[-1]['平均月收入'],c.MANIFEST['original_pivot']['overall_average'])
        all_summary=c.hr_summary(None)
        self.assertAlmostEqual(all_summary.iloc[-1]['平均月收入'],raw['月收入合计'].sum()/raw['人数'].sum())
        self.assertTrue(c.hr_summary([]).empty)
        pair=c.department_options()[:2]
        subset=raw.loc[raw['部门'].isin(pair)]
        self.assertAlmostEqual(c.hr_summary(pair).iloc[-1]['平均月收入'],subset['月收入合计'].sum()/subset['人数'].sum())

    def test_yujue_period_changes_angles(self):
        ends=[]
        for period in c.period_options(6):
            _,values=c.row_values(6,period,'周期')
            fig=c.chart_6(period)
            self.assertAlmostEqual(fig.axes[0].patches[0].theta1,90-values[0]/.5*360)
            ends.append(fig.axes[0].patches[-1].theta1)
            plt.close(fig)
        self.assertNotEqual(*ends)

    def test_month_region_transpose(self):
        raw=c.load_data(7)
        for month in raw.columns[1:]:
            labels,values=c.slider_values('月份',month)
            self.assertEqual(labels,raw['区域'].tolist())
            np.testing.assert_allclose(values,raw[month].to_numpy())
        for region in raw['区域']:
            labels,values=c.slider_values('区域',region)
            self.assertEqual(labels,raw.columns[1:].tolist())
            expected=raw.set_index('区域').loc[region].to_numpy(float)
            np.testing.assert_allclose(values,expected)
            fig=c.chart_7('区域',region)
            for index,(collection,value) in enumerate(zip(fig.axes[0].collections,values)):
                np.testing.assert_allclose(collection.get_offsets()[0],[value,index])
            plt.close(fig)

    def test_unknown_selection_is_not_silent(self):
        with self.assertRaises(ValueError):c.chart_1('13月')
        with self.assertRaises(ValueError):c.slider_values('其他','1月')
        with self.assertRaises(ValueError):c.hr_summary(['不存在的部门'])


if __name__=='__main__':
    unittest.main()
