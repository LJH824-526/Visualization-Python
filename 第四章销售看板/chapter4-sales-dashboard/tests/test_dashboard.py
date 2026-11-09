from pathlib import Path
import sys,unittest
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import dashboard as d


class SalesTests(unittest.TestCase):
    def tearDown(self):plt.close('all')

    def test_default_matches_workbook_cache(self):
        reference=d.MANIFEST['reference'];stats=d.get_stats(reference['month'])
        self.assertEqual(stats['volume'],reference['volume'])
        self.assertAlmostEqual(stats['revenue']/10000,reference['revenue_wan'])
        self.assertAlmostEqual(stats['profit']/10000,reference['profit_wan'])
        self.assertAlmostEqual(stats['margin'],reference['profit_margin'])
        self.assertAlmostEqual(stats['cost_total'],reference['cost'])

    def test_every_month_reconciles(self):
        monthly=d.read_data('monthly.csv')
        self.assertEqual(int(monthly['销量'].sum()),d.MANIFEST['records'])
        for month in d.MANIFEST['months']:
            stats=d.get_stats(month)
            for key in ['region','courier','category']:
                self.assertEqual(int(stats[key].sum()),stats['volume'])
            products=d.read_data('product_month.csv');selected=products.loc[products['月份']==month]
            self.assertEqual(int(selected['销量'].sum()),stats['volume'])
            self.assertAlmostEqual(selected['销售额'].sum(),stats['revenue'])
            self.assertAlmostEqual(selected['利润额'].sum(),stats['profit'])
            self.assertTrue(stats['top3']['销售额'].is_monotonic_decreasing)
            self.assertAlmostEqual(float((stats['costs']/stats['cost_total']).sum()),1)

    def test_month_over_month_and_first_month(self):
        stats=d.get_stats('9月')
        self.assertEqual(stats['previous'],'8月')
        self.assertAlmostEqual(stats['growth'],751/714-1)
        first=d.get_stats(d.MANIFEST['months'][0])
        self.assertIsNone(first['previous']);self.assertIsNone(first['growth'])

    def test_component_uses_selected_month(self):
        for month in ['1月','9月']:
            stats=d.get_stats(month)
            figure=d.render_component(6,month=month)
            np.testing.assert_array_equal([p.get_height() for p in figure.axes[0].patches],stats['region'].to_numpy())
            plt.close(figure)

    def test_theme_and_no_order_identifiers(self):
        self.assertNotEqual(d.foreground('展示参考'),d.foreground('原生白字'))
        with self.assertRaises(ValueError):d.get_stats('13月')
        with self.assertRaises(ValueError):d.foreground('未知')
        for path in (ROOT/'data').glob('*.csv'):
            self.assertNotIn('订单单号',path.read_text(encoding='utf-8-sig'))


if __name__=='__main__':unittest.main()
