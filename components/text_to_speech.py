import tempfile
import queue
from gtts import gTTS
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, QIODevice, QFile, QTimer

class TextToSpeech:
    def __init__(self, parent):
        self.parent = parent
        self.media_player = QMediaPlayer(self.parent)
        self.text_queue = queue.Queue()
        self.queue_timer = QTimer(self.parent)
        self.queue_timer.timeout.connect(self.check_queue)
        self.queue_timer.start(1000)  # Check the queue every 1000 ms (1 second)

    def play_text_voice(self, text, lang):
        self.text_queue.put((text, lang))
        if self.media_player.state() == QMediaPlayer.StoppedState:
            self.play_next_audio()

    def play_next_audio(self):
        if self.text_queue.empty():
            return

        text, lang = self.text_queue.get()
        tts = gTTS(text=text, lang=lang)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(temp_file.name)
        temp_file.close()

        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(temp_file.name)))
        self.media_player.play()

        self.media_player.mediaStatusChanged.connect(lambda status: self.remove_temp_voice_file(status, temp_file.name))
        self.media_player.mediaStatusChanged.connect(self.handle_media_state_change)

    def remove_temp_voice_file(self, status, file_name):
        if status == QMediaPlayer.EndOfMedia:
            if QFile.exists(file_name):
                QFile.remove(file_name)

    def handle_media_state_change(self, state):
        if state == QMediaPlayer.StoppedState:
            self.play_next_audio()

    def check_queue(self):
        if self.media_player.state() == QMediaPlayer.StoppedState:
            self.play_next_audio()


