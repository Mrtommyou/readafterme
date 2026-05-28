import os

import requests

SERVER_URL = os.environ.get('API_URL', 'http://localhost:9004')


class ApiService:
    def __init__(self, base_url=SERVER_URL):
        self.base_url = base_url

    def health_check(self):
        try:
            resp = requests.get(f'{self.base_url}/health', timeout=5)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def get_videos(self):
        resp = requests.get(f'{self.base_url}/api/videos', timeout=10)
        resp.raise_for_status()
        return resp.json().get('videos', [])

    def upload_video(self, file_path):
        file_name = os.path.basename(file_path)
        with open(file_path, 'rb') as f:
            resp = requests.post(
                f'{self.base_url}/api/upload',
                files={'file': (file_name, f, 'video/mp4')},
                timeout=300,
            )
        resp.raise_for_status()
        return resp.json()

    def get_sentences(self, video_id):
        resp = requests.get(
            f'{self.base_url}/api/videos/{video_id}/sentences', timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def get_video_url(self, video_id):
        return f'{self.base_url}/api/videos/{video_id}/file'

    def score_recording(self, video_id, sentence_index, audio_path):
        file_name = os.path.basename(audio_path)
        with open(audio_path, 'rb') as f:
            resp = requests.post(
                f'{self.base_url}/api/score',
                data={'video_id': video_id, 'sentence_index': sentence_index},
                files={'file': (file_name, f, 'audio/wav')},
                timeout=60,
            )
        resp.raise_for_status()
        return resp.json()

    def get_history(self):
        resp = requests.get(f'{self.base_url}/api/history', timeout=10)
        resp.raise_for_status()
        return resp.json().get('history', [])
