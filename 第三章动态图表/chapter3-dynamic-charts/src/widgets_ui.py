"""Jupyter controls; plotting functions remain runnable without widgets."""
from dynamic_charts import *


def show_example(number):
    try:
        import ipywidgets as widgets
        from IPython.display import display,clear_output
    except ImportError:
        figure=FUNCTIONS[number](**DEFAULTS[number]);plt.show();plt.close(figure)
        print('当前环境未安装 ipywidgets，已显示默认图。安装 requirements-notebook.txt 后重新运行即可交互。')
        return

    extra=[]
    if number==1:
        options=month_options(1)
        control=widgets.Dropdown(options=options,value=DEFAULTS[1]['month'],description='月份')
        player=widgets.Play(min=0,max=len(options)-1,value=options.index(control.value),interval=1200)
        widgets.jslink((player,'value'),(control,'index'))
        controls={'month':control};extra=[player]
    elif number==2:
        controls={'month':widgets.Dropdown(options=month_options(2),value=DEFAULTS[2]['month'],description='月份')}
    elif number in (3,6):
        controls={'period':widgets.ToggleButtons(options=period_options(number),value=DEFAULTS[number]['period'],description='周期')}
    elif number==4:
        controls={key:widgets.Checkbox(value=True,description=label,indent=False)
                  for key,label in [('sales','销售额'),('profit','利润'),('margin','利润率')]}
    elif number==5:
        options=department_options()
        selector=widgets.SelectMultiple(options=options,value=tuple(DEFAULTS[5]['departments']),description='部门',rows=7)
        all_button=widgets.Button(description='全选');none_button=widgets.Button(description='清空')
        all_button.on_click(lambda _:setattr(selector,'value',tuple(options)))
        none_button.on_click(lambda _:setattr(selector,'value',()))
        controls={'departments':selector};extra=[widgets.VBox([all_button,none_button])]
    elif number==7:
        axis=widgets.ToggleButtons(options=['月份','区域'],value='月份',description='查看方式')
        frame=load_data(7)
        selector=widgets.Dropdown(options=frame.columns[1:].tolist(),description='筛选项')
        def change_axis(change):
            selector.options=frame.columns[1:].tolist() if change['new']=='月份' else frame['区域'].tolist()
        axis.observe(change_axis,names='value')
        controls={'axis':axis,'selection':selector}
    else:raise ValueError('图号应为 1—7。')

    def draw(**kwargs):
        if any(value is None for key,value in kwargs.items() if key!='departments'):return
        clear_output(wait=True)
        figure=FUNCTIONS[number](**kwargs)
        display(figure);plt.close(figure)
    output=widgets.interactive_output(draw,controls)
    display(widgets.VBox([widgets.HBox([*controls.values(),*extra]),output]))
