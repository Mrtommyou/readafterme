from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform
from services.api_service import ApiService
from theme import COLORS


class VideoCard(BoxLayout):
    def __init__(self, video_info, on_practice, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height=dp(64), **kwargs)
        self.video_id = video_info['id']
        self.video_name = video_info['name']

        icon = Label(
            text='🎬', size_hint_x=None, width=dp(36),
            halign='center', valign='middle',
            font_size=sp(18),
        )
        icon.bind(size=icon.setter('text_size'))

        info_box = BoxLayout(orientation='vertical', size_hint_x=0.6)
        name_label = Label(
            text=video_info['name'],
            halign='left', valign='middle',
            font_size=sp(13),
            color=COLORS['slate_700'],
            shorten=True,
        )
        name_label.bind(size=name_label.setter('text_size'))
        duration_label = Label(
            text=f"时长 {video_info['duration']}",
            halign='left', valign='middle',
            font_size=sp(11),
            color=COLORS['slate_400'],
            size_hint_y=None, height=dp(16),
        )
        duration_label.bind(size=duration_label.setter('text_size'))
        info_box.add_widget(name_label)
        info_box.add_widget(duration_label)

        status_label = Label(
            text=video_info['status'],
            size_hint_x=None, width=dp(50),
            halign='center', valign='middle',
            font_size=sp(11),
            color=COLORS['emerald'],
        )
        status_label.bind(size=status_label.setter('text_size'))

        practice_btn = Button(
            text='练习', size_hint_x=None, width=dp(50),
            font_size=sp(12),
            color=COLORS['coral_dark'],
            background_normal='',
            background_color=(0.98, 0.93, 0.95, 1),
        )
        practice_btn.bind(on_release=lambda btn: on_practice(self.video_id, self.video_name))

        self.add_widget(icon)
        self.add_widget(info_box)
        self.add_widget(status_label)
        self.add_widget(practice_btn)


class ImportScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api = ApiService()
        self.videos = []

        root = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        header = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(60))
        header.add_widget(Label(
            text='导入视频', halign='left', valign='middle',
            font_size=sp(20), bold=True, color=COLORS['slate_700'],
            size_hint_y=0.6,
        ))
        header.add_widget(Label(
            text='上传英语视频，自动生成跟读句子',
            halign='left', valign='top',
            font_size=sp(12), color=COLORS['slate_400'],
            size_hint_y=0.4,
        ))

        self.upload_btn = Button(
            text='📂  点击上传或拖拽视频文件到此',
            size_hint_y=None, height=dp(120),
            font_size=sp(14), color=COLORS['slate_500'],
            background_normal='',
            background_color=(1, 1, 1, 1),
            border=(2, 2, 2, 2),
        )
        self.upload_btn.bind(on_release=self.pick_file)

        self.status_label = Label(
            text='', size_hint_y=None, height=dp(30),
            font_size=sp(12), color=COLORS['slate_400'],
            halign='center',
        )

        list_header = Label(
            text='已导入视频', halign='left', valign='middle',
            font_size=sp(14), bold=True, color=COLORS['slate_600'],
            size_hint_y=None, height=dp(30),
        )

        scroll = ScrollView()
        self.video_list = GridLayout(
            cols=1, spacing=dp(6), size_hint_y=None,
            padding=[0, 0, 0, 0],
        )
        self.video_list.bind(minimum_height=self.video_list.setter('height'))
        scroll.add_widget(self.video_list)

        root.add_widget(header)
        root.add_widget(self.upload_btn)
        root.add_widget(self.status_label)
        root.add_widget(list_header)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_enter(self):
        self.load_videos()

    def load_videos(self):
        try:
            self.videos = self.api.get_videos()
            self._refresh_list()
        except Exception as e:
            self.status_label.text = f'连接失败: {e}'
            Clock.schedule_once(lambda dt: self._retry_connect(), 3)

    def _retry_connect(self):
        if self.api.health_check():
            self.status_label.text = ''
            self.load_videos()
        else:
            self.status_label.text = '无法连接到服务器，请检查API服务'
            Clock.schedule_once(lambda dt: self._retry_connect(), 5)

    def _refresh_list(self):
        self.video_list.clear_widgets()
        if not self.videos:
            empty = Label(
                text='暂无视频，请上传', size_hint_y=None, height=dp(60),
                font_size=sp(12), color=COLORS['slate_400'],
                halign='center', valign='middle',
            )
            empty.bind(size=empty.setter('text_size'))
            self.video_list.add_widget(empty)
            return

        for v in self.videos:
            card = VideoCard(v, self.go_to_practice)
            self.video_list.add_widget(card)

    def pick_file(self, btn):
        if platform == 'android':
            from plyer import filechooser
            filechooser.open_file(
                filters=['*.mp4', '*.avi', '*.mov', '*.mkv', '*.webm'],
                on_selection=self._on_file_selected,
            )
        else:
            from plyer import filechooser
            filechooser.open_file(
                filters=['*.mp4', '*.avi', '*.mov', '*.mkv', '*.webm'],
                on_selection=self._on_file_selected,
            )

    def _on_file_selected(self, selection):
        if selection:
            self.upload_video(selection[0])

    def upload_video(self, path):
        self.status_label.text = '正在上传和处理视频...'
        Clock.schedule_once(lambda dt: self._do_upload(path), 0.1)

    def _do_upload(self, path):
        try:
            self.api.upload_video(path)
            self.status_label.text = '上传成功'
            self.load_videos()
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', ''), 2)
        except Exception as e:
            self.status_label.text = f'上传失败: {e}'

    def go_to_practice(self, video_id, video_name):
        practice_screen = self.manager.get_screen('practice')
        practice_screen.set_video(video_id, video_name)
        self.manager.current = 'practice'
