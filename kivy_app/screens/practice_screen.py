import os
import tempfile

from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.video import Video
from kivy.utils import platform
from services.api_service import ApiService
from services.audio_recorder import AudioRecorder
from theme import COLORS
from widgets.score_ring import ScoreRing


class SentenceCard(BoxLayout):
    def __init__(self, sentence, index, is_active, on_click, **kwargs):
        super().__init__(
            orientation='vertical', size_hint_y=None, height=dp(78),
            padding=[dp(12), dp(8), dp(12), dp(8)],
            **kwargs
        )
        self.index = index

        bg = (0.98, 0.93, 0.95, 1) if is_active else (1, 1, 1, 1)
        self.md_bg = bg

        en_label = Label(
            text=sentence['en'],
            halign='left', valign='middle',
            font_size=sp(13),
            color=COLORS['slate_700'] if is_active else COLORS['slate_600'],
            bold=is_active,
            size_hint_y=0.5,
        )
        en_label.bind(size=en_label.setter('text_size'))

        zh_label = Label(
            text=sentence.get('zh', ''),
            halign='left', valign='middle',
            font_size=sp(11),
            color=COLORS['slate_500'] if is_active else COLORS['slate_400'],
            size_hint_y=0.3,
        )
        zh_label.bind(size=zh_label.setter('text_size'))

        time_label = Label(
            text=f"{sentence['start']:.1f}s - {sentence['end']:.1f}s",
            halign='left', valign='middle',
            font_size=sp(9),
            color=COLORS['slate_300'],
            size_hint_y=0.2,
        )
        time_label.bind(size=time_label.setter('text_size'))

        self.add_widget(en_label)
        self.add_widget(zh_label)
        self.add_widget(time_label)

        touch_btn = Button(
            size_hint=(1, 1), opacity=0,
        )
        touch_btn.bind(on_release=lambda btn: on_click(self.index))
        self.add_widget(touch_btn)


class PracticeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api = ApiService()
        self.recorder = AudioRecorder()
        self.video_id = None
        self.video_name = ''
        self.sentences = []
        self.active_idx = 0
        self.recorded_audio_path = None
        self.scores = None
        self.is_recording = False

        root = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(6))

        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        self.title_label = Label(
            text='跟读练习', halign='left', valign='middle',
            font_size=sp(18), bold=True, color=COLORS['slate_700'],
            size_hint_x=0.7,
        )
        self.title_label.bind(size=self.title_label.setter('text_size'))
        switch_btn = Button(
            text='切换视频', size_hint_x=None, width=dp(80),
            font_size=sp(11), color=COLORS['slate_400'],
            background_normal='', background_color=(0, 0, 0, 0),
        )
        switch_btn.bind(on_release=self.switch_video)
        header.add_widget(self.title_label)
        header.add_widget(switch_btn)
        root.add_widget(header)

        self.video_player = Video(
            size_hint_y=None, height=dp(200),
            state='stop', volume=1.0,
            options={'allow_stretch': True},
        )
        root.add_widget(self.video_player)

        control_bar = BoxLayout(
            orientation='horizontal', size_hint_y=None, height=dp(50),
            spacing=dp(8), padding=[dp(8), dp(4), dp(8), dp(4)],
        )

        self.rec_btn = Button(
            text='🔴  录音', font_size=sp(13),
            size_hint_x=None, width=dp(80),
            color=COLORS['coral_dark'],
            background_normal='', background_color=(0.98, 0.93, 0.95, 1),
        )
        self.rec_btn.bind(on_release=self.toggle_recording)

        self.play_btn = Button(
            text='▶  播放', font_size=sp(13),
            size_hint_x=None, width=dp(80),
            color='#38bdf8',
            background_normal='', background_color=(0.94, 0.98, 1, 1),
            disabled=True,
        )
        self.play_btn.bind(on_release=self.play_recording)

        self.score_btn = Button(
            text='评分', font_size=sp(13),
            size_hint_x=None, width=dp(60),
            color=COLORS['coral_dark'],
            background_normal='', background_color=(0.98, 0.93, 0.95, 1),
            disabled=True,
        )
        self.score_btn.bind(on_release=self.submit_scoring)

        control_bar.add_widget(self.rec_btn)
        control_bar.add_widget(self.play_btn)
        control_bar.add_widget(self.score_btn)
        root.add_widget(control_bar)

        self.score_container = BoxLayout(
            orientation='vertical', size_hint_y=None, height=dp(160),
        )

        no_video_msg = BoxLayout(orientation='vertical')
        no_video_msg.add_widget(Label(
            text='🎯', font_size=sp(40), halign='center',
            size_hint_y=0.4,
        ))
        no_video_msg.add_widget(Label(
            text='请先导入一个视频', font_size=sp(16),
            color=COLORS['slate_600'], halign='center', bold=True,
            size_hint_y=0.2,
        ))
        no_video_msg.add_widget(Label(
            text='上传视频后才能开始跟读练习', font_size=sp(12),
            color=COLORS['slate_400'], halign='center',
            size_hint_y=0.2,
        ))
        go_import_btn = Button(
            text='去导入视频', size_hint=(None, None),
            size=(dp(160), dp(44)),
            font_size=sp(13), color=COLORS['white'],
            background_normal='', background_color=(0.98, 0.55, 0.67, 1),
            pos_hint={'center_x': 0.5},
        )
        go_import_btn.bind(on_release=self.go_to_import)
        no_video_msg.add_widget(go_import_btn)

        self.no_video_widget = no_video_msg

        scroll = ScrollView()
        self.sentence_list = GridLayout(
            cols=1, spacing=dp(4), size_hint_y=None,
            padding=[0, 0, 0, 0],
        )
        self.sentence_list.bind(minimum_height=self.sentence_list.setter('height'))
        scroll.add_widget(self.sentence_list)

        root.add_widget(self.score_container)
        root.add_widget(scroll)
        self.add_widget(root)

    def set_video(self, video_id, video_name):
        self.video_id = video_id
        self.video_name = video_name
        self.scores = None
        self.recorded_audio_path = None
        self.score_container.clear_widgets()
        self.load_sentences()

    def load_sentences(self):
        if not self.video_id:
            self.sentence_list.clear_widgets()
            return

        try:
            data = self.api.get_sentences(self.video_id)
            self.sentences = data.get('sentences', [])
            self.title_label.text = self.video_name
            self.active_idx = 0
            self._refresh_sentence_list()

            video_url = self.api.get_video_url(self.video_id)
            self.video_player.source = video_url
            self.video_player.state = 'stop'
        except Exception as e:
            self.sentence_list.clear_widgets()
            self.sentence_list.add_widget(Label(
                text=f'加载失败: {e}', font_size=sp(12),
                color=COLORS['rose'], halign='center',
                size_hint_y=None, height=dp(60),
            ))

    def _refresh_sentence_list(self):
        self.sentence_list.clear_widgets()
        for i, s in enumerate(self.sentences):
            card = SentenceCard(
                s, i, i == self.active_idx, self.on_sentence_click,
            )
            self.sentence_list.add_widget(card)

    def on_sentence_click(self, index):
        if index < 0 or index >= len(self.sentences):
            return
        self.active_idx = index
        self._refresh_sentence_list()
        sentence = self.sentences[index]
        self.video_player.seek(sentence['start'])
        self.video_player.state = 'play'
        self.scores = None
        self.score_container.clear_widgets()

    def toggle_recording(self, btn):
        if not self.video_id or not self.sentences:
            return

        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.rec_btn.text = '⏹  停止'
        self.is_recording = True
        self.scores = None
        self.score_container.clear_widgets()
        self.score_btn.disabled = True
        self.play_btn.disabled = True

        audio_dir = os.path.join(tempfile.gettempdir(), 'readafterme_recordings')
        os.makedirs(audio_dir, exist_ok=True)
        ext = '.wav' if platform != 'android' else '.m4a'
        self.recorded_audio_path = os.path.join(
            audio_dir, f'recording_{self.active_idx:04d}{ext}'
        )
        try:
            self.recorder.start_recording(self.recorded_audio_path)
        except Exception:
            self.rec_btn.text = '🔴  录音'
            self.is_recording = False

    def stop_recording(self):
        self.rec_btn.text = '🔴  录音'
        self.is_recording = False
        try:
            self.recorder.stop_recording()
            self.play_btn.disabled = False
            self.score_btn.disabled = False
        except Exception:
            pass

    def play_recording(self, btn):
        if self.recorded_audio_path and os.path.exists(self.recorded_audio_path):
            if platform == 'android':
                from jnius import autoclass
                MediaPlayer = autoclass('android.media.MediaPlayer')
                player = MediaPlayer()
                player.setDataSource(self.recorded_audio_path)
                player.prepare()
                player.start()
            else:
                import subprocess as sp
                sp.Popen(['ffplay', '-nodisp', '-autoexit', self.recorded_audio_path],
                         stdout=sp.DEVNULL, stderr=sp.DEVNULL)

    def submit_scoring(self, btn):
        if not self.recorded_audio_path or not os.path.exists(self.recorded_audio_path):
            return
        if not self.video_id:
            return

        self.score_btn.text = '评分中...'
        self.score_btn.disabled = True

        Clock.schedule_once(lambda dt: self._do_score(), 0.1)

    def _do_score(self):
        try:
            result = self.api.score_recording(
                self.video_id, self.active_idx, self.recorded_audio_path,
            )
            self.scores = result
            self._show_scores(result)
        except Exception as e:
            self.score_container.clear_widgets()
            self.score_container.add_widget(Label(
                text=f'评分失败: {e}', font_size=sp(12),
                color=COLORS['rose'], halign='center',
            ))
        finally:
            self.score_btn.text = '评分'
            self.score_btn.disabled = False

    def _show_scores(self, scores):
        self.score_container.clear_widgets()
        overall_label = Label(
            text=f"综合评分: {scores['overall']}/100",
            font_size=sp(16), bold=True,
            color=COLORS['coral_dark'], halign='center',
            size_hint_y=None, height=dp(30),
        )
        self.score_container.add_widget(overall_label)

        rings = BoxLayout(
            orientation='horizontal', size_hint_y=None, height=dp(130),
            spacing=dp(8), padding=[dp(4), 0],
        )
        rings.add_widget(ScoreRing(scores['pronunciation'], '发音准确度', COLORS['coral']))
        rings.add_widget(ScoreRing(scores['fluency'], '流利度', COLORS['amber']))
        rings.add_widget(ScoreRing(scores['timing'], '节奏匹配', '#34d399'))
        self.score_container.add_widget(rings)

    def switch_video(self, btn):
        self.video_player.state = 'stop'
        self.video_player.source = ''
        self.video_id = None
        self.sentences = []
        self.scores = None
        self.score_container.clear_widgets()
        self.sentence_list.clear_widgets()
        self.title_label.text = '跟读练习'
        self.manager.current = 'import'

    def go_to_import(self, btn):
        self.manager.current = 'import'
