"""Descomposición de un KPI (Ingreso = Clientes × Frecuencia × Ticket) con Manim.

Ejecutar:
    uv run manim -pql descomposicion_kpi.py DescomposicionKPI    # vista rápida
    uv run manim -pqh descomposicion_kpi.py DescomposicionKPI    # calidad alta
"""

from manim import *
import numpy as np

# --- Datos: reemplaza por tu propio análisis ---------------------------------
# Cada factor: (nombre, valor periodo anterior, valor periodo actual, formato)
KPI = "Ingreso"
UNIDAD_KPI = "MM USD"
FACTORES = [
    ("Clientes", 50_000, 52_000, "{:,.0f}"),
    ("Frecuencia", 4.0, 3.4, "{:.1f}"),
    ("Ticket", 500, 510, "${:,.0f}"),
]
# Segundo nivel: se abre el factor con mayor aporte negativo
SUBFACTORES = [
    ("% clientes recurrentes", 0.70, 0.58, "{:.0%}"),
    ("Compras por recurrente", 4.0 / 0.70, 3.4 / 0.58, "{:.1f}"),
]
CONCLUSION = "El problema es de retención: menos clientes vuelven a comprar"

# --- Estilo -------------------------------------------------------------------
COLOR_SUBE = GREEN_C
COLOR_BAJA = RED_C
MENOS = "−"  # signo menos tipográfico


def pct(x):
    return f"{x:+.0%}".replace("-", MENOS)


def mm(x):
    return f"{x:+.1f}".replace("-", MENOS)


def color(x):
    return COLOR_SUBE if x >= 0 else COLOR_BAJA


def ficha(antes, despues, formato, aporte=None):
    """Columna bajo un factor: valores, variación % y aporte en MM."""
    var = despues / antes - 1
    filas = [
        Text(f"{formato.format(antes)} → {formato.format(despues)}",
             font_size=20, color=GREY_A),
        Text(pct(var), font_size=32, color=color(var), weight=BOLD),
    ]
    if aporte is not None:
        filas.append(Text(f"aporte {mm(aporte)} MM", font_size=18, color=color(aporte)))
    return VGroup(*filas).arrange(DOWN, buff=0.15)


class DescomposicionKPI(Scene):
    def construct(self):
        antes = np.prod([f[1] for f in FACTORES]) / 1e6
        despues = np.prod([f[2] for f in FACTORES]) / 1e6
        delta = despues - antes
        var_kpi = despues / antes - 1

        # Aporte de cada factor en MM (descomposición logarítmica: suma exacta)
        aportes = [delta * np.log(f[2] / f[1]) / np.log(despues / antes)
                   for f in FACTORES]

        # --- 1. La pregunta ---
        pregunta = Text(f"¿Por qué cayó el {KPI.lower()} {pct(var_kpi)}?",
                        font_size=40).to_edge(UP, buff=0.5)
        kpi = Text(KPI, font_size=44, weight=BOLD)
        valor = Text(f"{antes:.0f} → {despues:.0f} {UNIDAD_KPI}  ({pct(var_kpi)})",
                     font_size=28, color=color(var_kpi)).next_to(kpi, DOWN)
        self.play(Write(pregunta))
        self.play(FadeIn(kpi, scale=1.3), FadeIn(valor, shift=UP * 0.2))
        self.wait(1)

        # --- 2. La ecuación se arma ---
        piezas = [Text(KPI, font_size=44, weight=BOLD), Text("=", font_size=44)]
        for i, (nombre, *_rest) in enumerate(FACTORES):
            if i:
                piezas.append(Text("×", font_size=44))
            piezas.append(Text(nombre, font_size=44))
        ecuacion = VGroup(*piezas).arrange(RIGHT, buff=0.35).shift(UP * 1.4)
        nombres = [p for p in piezas[2:] if p.text != "×"]

        self.play(
            ReplacementTransform(kpi, piezas[0]),
            valor.animate.scale(0.8).next_to(piezas[0], DOWN, buff=0.3),
        )
        self.play(LaggedStart(*[Write(p) for p in piezas[1:]], lag_ratio=0.3))
        self.wait(0.5)

        # --- 3. Variación de cada factor, una a una ---
        fichas = []
        for nombre_mob, (_, a, d, fmt), aporte in zip(nombres, FACTORES, aportes):
            f = ficha(a, d, fmt, aporte).next_to(nombre_mob, DOWN, buff=0.3)
            self.play(Indicate(nombre_mob, color=YELLOW, scale_factor=1.1),
                      FadeIn(f, shift=DOWN * 0.2))
            self.wait(0.8)
            fichas.append(f)

        # --- 4. Foco en el factor que explica la caída ---
        k = int(np.argmin(aportes))
        caja = SurroundingRectangle(VGroup(nombres[k], fichas[k]), color=YELLOW, buff=0.15)
        otros = VGroup(*[p for p in piezas if p is not nombres[k]],
                       *[f for j, f in enumerate(fichas) if j != k], valor)
        self.play(Create(caja), otros.animate.set_opacity(0.3))
        self.wait(1)

        # --- 5. Se abre ese factor en sus componentes ---
        subnombres = VGroup(*[Text(s[0], font_size=24) for s in SUBFACTORES])
        subfichas = [ficha(a, d, fmt) for _, a, d, fmt in SUBFACTORES]
        columnas = VGroup(*[VGroup(n, f).arrange(DOWN, buff=0.2)
                            for n, f in zip(subnombres, subfichas)])
        columnas.arrange(RIGHT, buff=1.5).next_to(caja, DOWN, buff=0.8)
        columnas.set_x(caja.get_x())
        # Mantener dentro del cuadro si el factor está en un borde
        if columnas.get_left()[0] < -config.frame_x_radius + 0.3:
            columnas.to_edge(LEFT, buff=0.3)
        if columnas.get_right()[0] > config.frame_x_radius - 0.3:
            columnas.to_edge(RIGHT, buff=0.3)
        ramas = VGroup(*[Line(caja.get_bottom(), c.get_top(), buff=0.1, color=GREY_B)
                         for c in columnas])
        self.play(LaggedStart(*[Create(r) for r in ramas], lag_ratio=0.3))
        self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.2) for c in columnas],
                              lag_ratio=0.4))
        self.wait(1)

        # Resaltar el subfactor con mayor caída
        var_sub = [d / a - 1 for _, a, d, _ in SUBFACTORES]
        s = int(np.argmin(var_sub))
        caja_sub = SurroundingRectangle(columnas[s], color=COLOR_BAJA, buff=0.12)
        conclusion = Text(CONCLUSION, font_size=26, color=YELLOW).to_edge(DOWN, buff=0.3)
        resto = VGroup(*[c for j, c in enumerate(columnas) if j != s])
        self.play(Create(caja_sub), resto.animate.set_opacity(0.4))
        self.play(Write(conclusion))
        self.wait(2)
