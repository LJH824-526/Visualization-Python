"""Check the source data, Notebook format, and all rendered images."""
from pathlib import Path
import hashlib
import json
import sys

from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_INPUT_SHA256 = 'd8e1be8d09e0c6f854e09148f17838203e698cab7733edbbb09ba074bba7acd0'


def main():
    path = ROOT / 'data' / '第二章 图表(前15).xlsx'
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    print('输入文件：', '原始版本' if actual == EXPECTED_INPUT_SHA256 else '已更新，将使用当前数据')

    notebook = json.loads((ROOT / 'notebooks/01_first_15_charts.ipynb').read_text(encoding='utf-8'))
    assert notebook['nbformat'] == 4, 'Notebook 格式不正确'
    cells = [c for c in notebook['cells'] if c['cell_type'] == 'code']
    assert len(cells) == 16, '应有 1 个公共设置单元格和 15 个图表单元格'
    for cell in cells:
        code = '\n'.join(s for s in cell['source'].splitlines() if not s.startswith('%'))
        compile(code, '<notebook-cell>', 'exec')

    files = sorted((ROOT / 'outputs/charts').glob('*.png'))
    assert len(files) == 15, f'期望 15 张 PNG，实际为 {len(files)}。先运行 scripts/render_all.py。'
    for number, path in enumerate(files, 1):
        assert path.name.startswith(f'{number:02d}_'), f'缺少图表编号 {number:02d}'
        with Image.open(path) as image:
            image.load()
            assert image.width >= 1000 and image.height >= 500, f'{path.name} 分辨率异常'
            rgb = image.convert('RGB')
            assert rgb.getpixel((0, 0)) == (26, 30, 67), f'{path.name} 背景颜色不符'
            assert sum(ImageStat.Stat(rgb).var) > 100, f'{path.name} 可能为空白图'
    print('通过：16 个 Notebook 代码单元格语法正确；15 张 PNG 编号、分辨率、底色和非空检查通过。')


if __name__ == '__main__':
    main()
