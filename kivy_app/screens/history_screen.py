from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from services.api_service import ApiService
from theme import COLORS


class HistoryCard(BoxLayout):
    def __init__(self, item, **kwargs):
        super().__init__(
            orientation='vertical', size_hint_y=None, height=dp(80),
            padding=[dp(14), dp(10), dp(14), dp(10)],
            spacing=dp(4),
            **kwargs
        )

        score = item.get('score', 0)
        if score >= 80:
            badge_color = COLORS['emerald']
            level_text = '优秀'
        elif score >= 60:
            badge_color = COLORS['amber']
            level_text = '良好'
        else:
            badge_color = COLORS['rose']
            level_text = '继续加油'

        top_row = BoxLayout(orientation='horizontal', size_hint_y=0.5)
        date_label = Label(
            text=item.get('date', ''),
            halign='left', valign='middle',
            font_size=sp(11), color=COLORS['slate_400'],
            size_hint_x=0.5,
        )
        date_label.bind(size=date_label.setter('text_size'))

        score_label = Label(
            text=f"{score} 分",
            halign='right', valign='middle',
            font_size=sp(12), bold=True, color=badge_color,
            size_hint_x=0.5,
        )
        score_label.bind(size=score_label.setter('text_size'))
        top_row.add_widget(date_label)
        top_row.add_widget(score_label)

        video_label = Label(
            text=item.get('video', ''),
            halign='left', valign='middle',
            font_size=sp(13), color=COLORS['slate_700'],
            size_hint_y=0.3,
        )
        video_label.bind(size=video_label.setter('text_size'))

        bottom_row = BoxLayout(orientation='horizontal', size_hint_y=0.2, spacing=dp(8))
        sentences_label = Label(
            text=f"句子: {item.get('sentences', 0)}",
            font_size=sp(10), color=COLORS['slate_400'],
            halign='left', valign='middle',
            size_hint_x=0.4,
        )
        sentences_label.bind(size=sentences_label.setter('text_size'))
        level_label = Label(
            text=level_text,
            font_size=sp(10), bold=True,
            color=badge_color, halign='left', valign='middle',
            size_hint_x=0.6,
        )
        level_label.bind(size=level_label.setter('text_size'))
        bottom_row.add_widget(sentences_label)
        bottom_row.add_widget(level_label)

        self.add_widget(top_row)
        self.add_widget(video_label)
        self.add_widget(bottom_row)


class HistoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api = ApiService()
        self.history = []

        root = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        header = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(56))
        header.add_widget(Label(
            text='学习记录', halign='left', valign='middle',
            font_size=sp(20), bold=True, color=COLORS['slate_700'],
            size_hint_y=0.6,
        ))
        header.add_widget(Label(
            text='查看你的练习历史和评分趋势',
            halign='left', valign='top',
            font_size=sp(12), color=COLORS['slate_400'],
            size_hint_y=0.4,
        ))

        self.empty_label = Label(
            text='暂无学习记录', halign='center', valign='middle',
            font_size=sp(14), color=COLORS['slate_400'],
            size_hint_y=None, height=dp(100),
        )

        scroll = ScrollView()
        self.card_list = GridLayout(
            cols=1, spacing=dp(8), size_hint_y=None,
            padding=[0, 0, 0, 0],
        )
        self.card_list.bind(minimum_height=self.card_list.setter('height'))
        scroll.add_widget(self.card_list)

        root.add_widget(header)
        root.add_widget(self.empty_label)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_enter(self):
        self.load_history()

    def load_history(self):
        try:
            self.history = self.api.get_history()
            self._refresh_list()
        except Exception as e:
            self.empty_label.text = f'加载失败: {e}'

    def _refresh_list(self):
        self.card_list.clear_widgets()
        if not self.history:
            self.empty_label.text = '暂无学习记录'
            return

        self.empty_label.text = ''
        for item in self.history:
            card = HistoryCard(item)
            self.card_list.add_widget(card)
