from kivy.graphics import Color, Ellipse, Line
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from theme import COLORS


class ScoreRing(BoxLayout):
    def __init__(self, pct, label, color, **kwargs):
        super().__init__(
            orientation='vertical', spacing=dp(4),
            size_hint=(None, None), size=(dp(100), dp(120)),
            **kwargs
        )

        self._pct = pct
        self._ring_color = color

        ring_container = FloatLayout(size_hint_y=0.75)

        with ring_container.canvas.before:
            Color(0.95, 0.91, 0.87, 1)
            Ellipse(
                pos=(ring_container.x + dp(8), ring_container.y + dp(8)),
                size=(dp(84), dp(84)),
            )

        with ring_container.canvas:
            Color(*self._hex_to_rgba(color))
            self._ring = Line(
                circle=(ring_container.center_x, ring_container.center_y, dp(38)),
                width=dp(6),
                cap='round',
            )

        pct_label = Label(
            text=f'{pct}%',
            halign='center', valign='middle',
            font_size=sp(16), bold=True,
            color=color,
        )
        ring_container.add_widget(pct_label)

        text_label = Label(
            text=label,
            halign='center', valign='middle',
            font_size=sp(11),
            color=COLORS['slate_500'],
            size_hint_y=0.25,
        )

        self.add_widget(ring_container)
        self.add_widget(text_label)

    def _hex_to_rgba(self, hex_color):
        h = hex_color.lstrip('#')
        r, g, b = tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        return r, g, b, 1
