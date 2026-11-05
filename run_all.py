"""命令行 python run_all.py；可在 VS Code 终端或 Jupyter 中运行。"""
from scripts.pipeline import run_analysis
from scripts.visuals import create_figures
from scripts.templates import create_templates

if __name__ == '__main__':
    result=run_analysis()
    create_figures(result)
    create_templates(result)
    print('已生成30幅教材模板复现图及19幅分析图，其中9幅对应商业模型。大屏启动：python -m streamlit run dashboard.py')
