#%%
import manim 

from manim import *
import pandas as pd

class EvolucionHistorica(Scene):
    def construct(self):
        # Datos de ejemplo; reemplaza por tu DataFrame
        df = pd.DataFrame({"anio": range(2000, 2025),
                           "valor": [i**1.5 for i in range(25)]})

        ax = Axes(
            x_range=[2000, 2024, 4], y_range=[0, 130, 20],
            x_length=10, y_length=5.5,
            axis_config={"include_numbers": True},
            x_axis_config={"decimal_number_config": {"group_with_commas": False, "num_decimal_places": 0}},
        )
        self.play(Create(ax))

        t = ValueTracker(2000)

        def linea():
            sub = df[df.anio <= t.get_value()]
            if len(sub) < 2:
                return VMobject()
            return ax.plot_line_graph(sub.anio, sub.valor,
                                      add_vertex_dots=False, line_color=BLUE)

        curva = always_redraw(linea)
        etiqueta = always_redraw(lambda: Text(str(int(t.get_value())), font_size=36)
                                 .to_corner(UR))
        self.add(curva, etiqueta)
        self.play(t.animate.set_value(2024), run_time=6, rate_func=linear)
        self.wait()
