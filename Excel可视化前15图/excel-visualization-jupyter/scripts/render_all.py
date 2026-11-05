"""Generate all 15 charts, or one chart, from the original Excel workbook."""
from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def main():
    parser = argparse.ArgumentParser(description='从 Excel 生成前 15 张模板图表。')
    parser.add_argument('--chart', type=int, choices=range(1, 16), help='只绘制指定编号。')
    args = parser.parse_args()

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import charts
    numbers = [args.chart] if args.chart is not None else list(range(1, 16))
    for number in numbers:
        figure = getattr(charts, f'chart_{number:02d}')(show=False)
        plt.close(figure)
        print(f'已生成图表 {number:02d}')
    print(f'完成：{ROOT / "outputs" / "charts"}')


if __name__ == '__main__':
    main()
