"""Render charts 16—30 from the single supplied workbook."""
from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def main():
    parser = argparse.ArgumentParser(description='生成后 15 张图（16—30）。')
    parser.add_argument('--chart', type=int, choices=range(16, 31), help='只生成指定图号。')
    args = parser.parse_args()
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import charts
    numbers = [args.chart] if args.chart is not None else range(16, 31)
    for number in numbers:
        figure = getattr(charts, f'chart_{number}')(show=False)
        plt.close(figure)
        print(f'已生成图表 {number}')
    print(f'完成：{ROOT / "outputs" / "charts"}')


if __name__ == '__main__':
    main()
