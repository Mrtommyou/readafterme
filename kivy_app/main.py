"""
ReadAfterMe — Kivy mobile app entry point.
"""
import kivy

kivy.require('2.2.0')

from kivy.app import App  # noqa: E402
from kivy.core.window import Window  # noqa: E402
from kivy.uix.screenmanager import ScreenManager  # noqa: E402
from kivy.utils import platform  # noqa: E402
from screens.history_screen import HistoryScreen  # noqa: E402
from screens.import_screen import ImportScreen  # noqa: E402
from screens.practice_screen import PracticeScreen  # noqa: E402


class ReadAfterMeApp(App):
    def build(self):
        self.title = 'ReadAfterMe'
        self.icon = 'icon.png'

        if platform in ('android', 'ios'):
            Window.fullscreen = 'auto'
        else:
            Window.size = (420, 780)

        sm = ScreenManager()
        sm.add_widget(ImportScreen(name='import'))
        sm.add_widget(PracticeScreen(name='practice'))
        sm.add_widget(HistoryScreen(name='history'))

        sm.current = 'import'
        return sm


if __name__ == '__main__':
    ReadAfterMeApp().run()
