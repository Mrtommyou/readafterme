import os
import time

from kivy.utils import platform

if platform == 'android':
    from jnius import autoclass

    MediaRecorder = autoclass('android.media.MediaRecorder')
    AudioSource = autoclass('android.media.MediaRecorder$AudioSource')
    OutputFormat = autoclass('android.media.MediaRecorder$OutputFormat')
    AudioEncoder = autoclass('android.media.MediaRecorder$AudioEncoder')
else:
    try:
        import numpy as np
        import sounddevice as sd
        import soundfile as sf
        _HAS_SOUNDDEVICE = True
    except ImportError:
        _HAS_SOUNDDEVICE = False


class AudioRecorder:
    def __init__(self):
        self._recorder = None
        self._output_path = None
        self._start_time = None
        self._stream = None
        self._audio_data = []

    def start_recording(self, output_path):
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        self._output_path = output_path

        if platform == 'android':
            recorder = MediaRecorder()
            recorder.setAudioSource(AudioSource.MIC)
            recorder.setOutputFormat(OutputFormat.MPEG_4)
            recorder.setAudioEncoder(AudioEncoder.AAC)
            recorder.setAudioSamplingRate(16000)
            recorder.setOutputFile(output_path)
            recorder.prepare()
            recorder.start()
            self._recorder = recorder
        elif _HAS_SOUNDDEVICE:
            self._audio_data = []
            self._stream = sd.InputStream(
                samplerate=16000, channels=1, dtype='float32',
                callback=self._audio_callback,
            )
            self._stream.start()
        else:
            raise RuntimeError('No audio recording backend available')

        self._start_time = time.time()

    def _audio_callback(self, indata, frames, time_info, status):
        self._audio_data.append(indata.copy())

    def stop_recording(self):
        duration = 0
        if self._start_time:
            duration = time.time() - self._start_time

        if self._recorder is not None:
            try:
                self._recorder.stop()
            except Exception:
                pass
            try:
                self._recorder.release()
            except Exception:
                pass
            self._recorder = None
        elif self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
            if self._audio_data:
                audio = np.concatenate(self._audio_data, axis=0)
                sf.write(self._output_path, audio, 16000)

        self._start_time = None
        return duration

    def get_duration(self):
        if self._start_time:
            return time.time() - self._start_time
        return 0
