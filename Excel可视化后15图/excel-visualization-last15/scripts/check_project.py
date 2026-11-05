"""Validate the input, Notebook, source syntax and 15 rendered PNGs."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_SHA256 = '975a602b7d4752acd26226f42673b79cb69c29f9970c0e05ffc77bc8f3d69d59'


def main():
    inputs = list((ROOT / 'data').glob('*.xlsx'))
    assert len(inputs) == 1, '本独立项目只需要后 15 图工作簿。'
    data = ROOT / 'data' / '第二章 图表(后15).xlsx'
    print('Excel：', '原始版本' if hashlib.sha256(data.read_bytes()).hexdigest() == ORIGINAL_SHA256
          else '已更新，将使用当前数据')
    notebook = json.loads((ROOT / 'notebooks/last_15_charts.ipynb').read_text(encoding='utf-8'))
    assert notebook['nbformat'] == 4
    cells = [c for c in notebook['cells'] if c['cell_type'] == 'code']
    assert len(cells) == 16
    for cell in cells:
        source = '\n'.join(s for s in cell['source'].splitlines() if not s.startswith('%'))
        compile(source, '<notebook-cell>', 'exec')
        assert not any(o.get('output_type') == 'error' for o in cell['outputs'])
    for path in [*(ROOT / 'src').glob('*.py'), *(ROOT / 'scripts').glob('*.py')]:
        compile(path.read_text(encoding='utf-8'), str(path.name), 'exec')
    files = sorted((ROOT / 'outputs/charts').glob('*.png'))
    assert len(files) == 15, '请先运行 scripts/render_all.py 生成后 15 图。'
    for number, path in enumerate(files, 16):
        assert path.name.startswith(f'{number}_'), f'缺少图表 {number}'
        with Image.open(path) as image:
            rgb = image.convert('RGB')
            assert rgb.width >= 1000 and rgb.height >= 500
            assert rgb.getpixel((0, 0)) == (26, 30, 67)
            assert sum(ImageStat.Stat(rgb).var) > 100, f'{path.name} 可能为空白图'
    print('通过：1 份 Excel、16 个 Notebook 代码单元格和第 16—30 图全部检查通过。')


if __name__ == '__main__':
    main()
