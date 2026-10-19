"""Antes / después de una iniciativa, con contrafactual, animado con Manim.

Ejecutar:
    uv run manim -pql antes_despues_iniciativa.py AntesDespues    # vista rápida
    uv run manim -pqh antes_despues_iniciativa.py AntesDespues    # calidad alta
"""

from manim import *
import numpy as np
import pandas as pd

# --- Datos: reemplaza por tu propio análisis ---------------------------------
# "real" es lo observado; "contrafactual" es lo que habría pasado sin la
# iniciativa (en la práctica sale de un modelo: tendencia + estacionalidad,
# grupo de control, etc.). Aquí se simulan ambos.
rng = np.random.default_rng(7)
t = np.arange(36)
contrafactual = 80 + 0.4 * t + 5 * np.sin(2 * np.pi * t / 12)
LANZAMIENTO = 24  # índice del primer mes con la iniciativa
efecto = np.where(t >= LANZAMIENTO,
                  0.12 * contrafactual * np.minimum(1, (t - LANZAMIENTO + 1) / 4), 0)
DATOS = pd.DataFrame({
    "mes": pd.date_range("2023-01-01", periods=36, freq="MS"),
    "real": contrafactual + efecto + rng.normal(0, 1.5, len(t)),
    "contrafactual": contrafactual,
})

TITULO = "Ventas mensuales (MM USD)"
INICIATIVA = "Lanzamiento del\nprograma de fidelización"
Y_RANGO = (60, 130)
Y_MARCAS = [60, 80, 100, 120]

# --- Estilo -------------------------------------------------------------------
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
COLOR_REAL = BLUE_C
COLOR_CF = GREY_B
COLOR_IMPACTO = GREEN_C


class AntesDespues(Scene):
    def construct(self):
        n = len(DATOS)
        ax = Axes(
            x_range=[0, n - 1, 12], y_range=[*Y_RANGO, 10],
            x_length=11, y_length=5,
            tips=False, axis_config={"color": GREY_B, "stroke_width": 2},
        ).shift(DOWN * 0.3)

        # Etiquetas manuales (Text en vez de números LaTeX)
        etiquetas_y = VGroup(*[
            Text(str(v), font_size=18, color=GREY_A).next_to(ax.c2p(0, v), LEFT, buff=0.15)
            for v in Y_MARCAS
        ])
        etiquetas_x = VGroup(*[
            Text(f"{MESES[DATOS.mes[i].month - 1]} {DATOS.mes[i].year}", font_size=18, color=GREY_A)
            .next_to(ax.c2p(i, Y_RANGO[0]), DOWN, buff=0.15)
            for i in range(0, n, 12)
        ])
        titulo = Text(TITULO, font_size=32).to_edge(UP, buff=0.3)

        self.play(Write(titulo), Create(ax), FadeIn(etiquetas_x, etiquetas_y))

        def linea(col, desde, hasta, color):
            idx = list(range(desde, hasta))
            return ax.plot_line_graph(
                idx, DATOS[col].iloc[desde:hasta].values,
                add_vertex_dots=False, line_color=color, stroke_width=4,
            )["line_graph"]

        # --- 1. Historia antes de la iniciativa ---
        antes = linea("real", 0, LANZAMIENTO, COLOR_REAL)
        self.play(Create(antes), run_time=3, rate_func=linear)

        # --- 2. Marca de lanzamiento ---
        x_lanz = LANZAMIENTO - 0.5
        marca = DashedLine(ax.c2p(x_lanz, Y_RANGO[0]), ax.c2p(x_lanz, Y_RANGO[1]),
                           color=YELLOW, dash_length=0.1)
        texto_marca = Text(INICIATIVA, font_size=20, color=YELLOW, line_spacing=0.8)
        texto_marca.next_to(marca.get_top(), LEFT, buff=0.15).shift(DOWN * 0.3)
        self.play(Create(marca), FadeIn(texto_marca))

        # --- 3. Historia después de la iniciativa ---
        despues = linea("real", LANZAMIENTO - 1, n, COLOR_REAL)
        self.play(Create(despues), run_time=2, rate_func=linear)
        self.wait(0.5)

        # --- 4. La pregunta clave y el contrafactual ---
        pregunta = Text("¿Cuánto se debe a la iniciativa y cuánto a la tendencia?",
                        font_size=24, slant=ITALIC, color=GREY_A).to_edge(DOWN, buff=0.2)
        self.play(FadeIn(pregunta))
        self.wait(1)

        cf = DashedVMobject(linea("contrafactual", LANZAMIENTO - 1, n, COLOR_CF),
                            num_dashes=40)
        leyenda = VGroup(
            VGroup(Line(ORIGIN, RIGHT * 0.5, color=COLOR_REAL, stroke_width=4),
                   Text("Real", font_size=18)).arrange(RIGHT, buff=0.15),
            VGroup(DashedLine(ORIGIN, RIGHT * 0.5, color=COLOR_CF, dash_length=0.08),
                   Text("Sin iniciativa (estimado)", font_size=18)).arrange(RIGHT, buff=0.15),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        leyenda.next_to(ax.c2p(0, Y_RANGO[1]), DR, buff=0.2)
        self.play(Create(cf), FadeIn(leyenda), run_time=2)

        # --- 5. Área entre curvas = impacto ---
        post = DATOS.iloc[LANZAMIENTO:]
        idx_post = range(LANZAMIENTO, n)
        puntos = [ax.c2p(i, v) for i, v in zip(idx_post, post.real)]
        puntos += [ax.c2p(i, v) for i, v in zip(reversed(idx_post), post.contrafactual[::-1])]
        area = Polygon(*puntos, stroke_width=0, fill_color=COLOR_IMPACTO, fill_opacity=0.4)
        self.play(FadeIn(area))
        self.bring_to_front(despues, cf)  # líneas por encima del área

        impacto = (post.real - post.contrafactual).sum()
        pct = impacto / post.contrafactual.sum()
        texto_impacto = Text(f"+{impacto:.0f} MM USD\n(+{pct:.0%} vs. sin iniciativa)",
                             font_size=22, color=COLOR_IMPACTO, line_spacing=0.8)
        punto_area = ax.c2p(n - 4, (post.real.iloc[-4] + post.contrafactual.iloc[-4]) / 2)
        texto_impacto.next_to(ax.c2p(n - 1, Y_RANGO[0] + 5), UL, buff=0.1)
        flecha = Arrow(texto_impacto.get_top(), punto_area, buff=0.1,
                       color=COLOR_IMPACTO, stroke_width=3, tip_length=0.15)

        conclusion = Text(
            f"La iniciativa generó {impacto:.0f} MM USD adicionales en {len(post)} meses",
            font_size=26, color=COLOR_IMPACTO,
        ).to_edge(DOWN, buff=0.2)
        self.play(FadeIn(texto_impacto), GrowArrow(flecha),
                  FadeTransform(pregunta, conclusion))
        self.wait(2)
