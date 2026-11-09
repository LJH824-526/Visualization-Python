from dashboard import *


def show_dashboard():
    try:
        import ipywidgets as widgets
        from IPython.display import display,clear_output
    except ImportError:
        figure=render_dashboard(**STATE);plt.show();plt.close(figure)
        print('当前环境未安装 ipywidgets，已显示默认看板。安装 requirements-notebook.txt 并重启内核后可交互。')
        return
    if 'mode' in DEFAULTS:
        controls={'mode':widgets.ToggleButtons(options=['模板复现','明细重算'],value=STATE['mode'],description='数据口径')}
    else:
        controls={'month':widgets.Dropdown(options=MANIFEST['months'],value=STATE['month'],description='月份'),
                  'theme':widgets.ToggleButtons(options=list(THEMES),value=STATE['theme'],description='配色')}
    def draw(**kwargs):
        STATE.update(kwargs)
        clear_output(wait=True)
        figure=render_dashboard(**STATE);display(figure);plt.close(figure)
    output=widgets.interactive_output(draw,controls)
    display(widgets.VBox([widgets.HBox(list(controls.values())),output]))
