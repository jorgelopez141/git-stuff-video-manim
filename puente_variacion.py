"""Puente de variación (waterfall) animado con Manim.

Ejecutar:
    uv run manim -pql puente_variacion.py PuenteVariacion    # vista rápida
    uv run manim -pqh puente_variacion.py PuenteVariacion    # calidad alta
"""

from manim import *
import pandas as pd

# --- Datos: reemplaza por tu propio análisis ---------------------------------
TITULO = "Ventas 2024 → 2025 (MM USD)"
INICIO = ("Ventas 2024", 100)
FIN_NOMBRE = "Ventas 2025"
DRIVERS = pd.DataFrame(
    {
        "driver": ["Precio", "Volumen", "Mix", "T. cambio", "Nuevos\nclientes"],
        "delta": [6, -14, -4, -5, 2],
        "explicacion": [
            "Aumento de precios del 6% en marzo",
            "Caída de volumen en el canal mayorista",
            "Más venta de productos de menor margen",
            "Depreciación de la moneda local",
            "Apertura de dos cuentas nuevas en Q4",
        ],
    }
)

# --- Estilo -------------------------------------------------------------------
COLOR_TOTAL = BLUE_D
COLOR_SUBE = GREEN_D
COLOR_BAJA = RED_D
Y_MIN = 70             # valor donde arranca el eje (0 = eje completo)
BASE_Y = -2.5          # posición vertical del inicio del eje
ALTO_MAX = 4.3         # alto en pantalla del valor máximo
ANCHO_BARRA = 1.0
PASO_X = 1.8


class PuenteVariacion(Scene):
    def construct(self):
        nombre_ini, valor_ini = INICIO
        valor_fin = valor_ini + DRIVERS.delta.sum()

        # Escala: valor máximo acumulado ocupa ALTO_MAX unidades
        acumulado = valor_ini + DRIVERS.delta.cumsum()
        maximo = max(valor_ini, acumulado.max(), valor_fin)
        escala = ALTO_MAX / (maximo - Y_MIN)

        def y(valor):
            return BASE_Y + (valor - Y_MIN) * escala

        n_barras = len(DRIVERS) + 2
        x0 = -PASO_X * (n_barras - 1) / 2

        def x(i):
            return x0 + i * PASO_X

        def barra(i, desde, hasta, color):
            bajo, alto = sorted([desde, hasta])
            rect = Rectangle(
                width=ANCHO_BARRA,
                height=max((alto - bajo) * escala, 0.01),
                fill_color=color, fill_opacity=0.9, stroke_width=0,
            )
            return rect.move_to([x(i), (y(bajo) + y(alto)) / 2, 0])

        def etiqueta_eje(i, texto):
            return Text(texto, font_size=18, line_spacing=0.8).move_to(
                [x(i), BASE_Y - 0.4, 0]
            )

        def conector(i, valor):
            return DashedLine(
                [x(i) + ANCHO_BARRA / 2, y(valor), 0],
                [x(i + 1) - ANCHO_BARRA / 2, y(valor), 0],
                dash_length=0.06, stroke_width=2, color=GREY_B,
            )

        # --- Título y eje base ---
        titulo = Text(TITULO, font_size=34).to_edge(UP, buff=0.4)
        eje = Line([x(0) - 0.9, BASE_Y, 0], [x(n_barras - 1) + 0.9, BASE_Y, 0],
                   color=GREY_B, stroke_width=2)
        self.play(Write(titulo), Create(eje))

        # --- Barra inicial ---
        b_ini = barra(0, Y_MIN, valor_ini, COLOR_TOTAL)
        v_ini = Text(f"{valor_ini}", font_size=24).next_to(b_ini, UP, buff=0.1)
        self.play(GrowFromEdge(b_ini, DOWN), FadeIn(etiqueta_eje(0, nombre_ini)))
        self.play(FadeIn(v_ini, shift=UP * 0.2))

        # --- Drivers, uno a uno con su explicación ---
        nivel = valor_ini
        leyenda = VMobject()
        barras_drivers = []  # (barra, etiqueta) de cada driver
        for k, fila in enumerate(DRIVERS.itertuples(), start=1):
            nuevo = nivel + fila.delta
            sube = fila.delta >= 0
            b = barra(k, nivel, nuevo, COLOR_SUBE if sube else COLOR_BAJA)
            signo = "+" if sube else "−"
            v = Text(f"{signo}{abs(fila.delta)}", font_size=24,
                     color=COLOR_SUBE if sube else COLOR_BAJA)
            v.next_to(b, UP if sube else DOWN, buff=0.1)

            nueva_leyenda = Text(fila.explicacion, font_size=24, slant=ITALIC,
                                 color=GREY_A).to_edge(DOWN, buff=0.3)

            self.play(Create(conector(k - 1, nivel)), run_time=0.4)
            self.play(
                # Las subidas crecen hacia arriba, las bajadas hacia abajo
                GrowFromEdge(b, DOWN if sube else UP),
                FadeIn(etiqueta_eje(k, fila.driver)),
                FadeTransform(leyenda, nueva_leyenda),
            )
            self.play(FadeIn(v, shift=(UP if sube else DOWN) * 0.2))
            self.wait(1.2)

            leyenda = nueva_leyenda
            barras_drivers.append(VGroup(b, v))
            nivel = nuevo

        # --- Barra final ---
        i_fin = n_barras - 1
        b_fin = barra(i_fin, Y_MIN, valor_fin, COLOR_TOTAL)
        v_fin = Text(f"{valor_fin}", font_size=24).next_to(b_fin, UP, buff=0.1)
        self.play(Create(conector(i_fin - 1, nivel)), FadeOut(leyenda), run_time=0.4)
        self.play(GrowFromEdge(b_fin, DOWN), FadeIn(etiqueta_eje(i_fin, FIN_NOMBRE)))
        self.play(FadeIn(v_fin, shift=UP * 0.2))

        # --- Remate: destacar el driver más grande ---
        idx = DRIVERS.delta.abs().idxmax()
        caja = SurroundingRectangle(barras_drivers[idx], color=YELLOW, buff=0.12)
        fila = DRIVERS.loc[idx]
        neto = valor_fin - valor_ini
        texto = f"{fila.driver.replace(chr(10), ' ')}: {fila.delta:+} de {neto:+} netos".replace("-", "−")
        conclusion = Text(texto, font_size=28, color=YELLOW).to_edge(DOWN, buff=0.3)
        self.play(Create(caja), Write(conclusion))
        self.play(Indicate(barras_drivers[idx][0], color=YELLOW, scale_factor=1.05))
        self.wait(2)
