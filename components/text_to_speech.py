import tempfile
import queue
from gtts import gTTS
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, QFile, QTimer


class TextToSpeech:
    """
    TextToSpeech Component for MainWindow, gets the translated text and puts them in a queue
    saves text as a temp mp3 file once finished file is deleted and made again with new mp3
    """

    def __init__(self, parent):
        """init with parent widget set queue, timer, and media player"""
        self.parent = parent
        self.media_player = QMediaPlayer(self.parent)
        self.text_queue = queue.Queue()
        self.queue_timer = QTimer(self.parent)
        self.queue_timer.setSingleShot(True)
        self.playback_enabled = True
        self.queue_timer.timeout.connect(self.check_queue)
        self.media_player.mediaStatusChanged.connect(self.handle_media_status_change)

    def play_text_voice(self, text, lang):
        """Adds text and language code to queue and plays"""
        self.playback_enabled = True
        self.text_queue.put((text, lang))
        if self.media_player.state() == QMediaPlayer.StoppedState:
            self.play_next_audio()

    def play_next_audio(self):
        """Playes next audio in queue and creats temp mp3 file"""
        if self.text_queue.empty():
            return

        text, lang = self.text_queue.get()
        tts = gTTS(text=text, lang=lang)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(temp_file.name)
        temp_file.close()
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(temp_file.name)))
        self.media_player.play()

    def remove_temp_voice_file(self, file_name):
        """Removes tempo file"""
        if QFile.exists(file_name):
            QFile.remove(file_name)

    def handle_media_status_change(self, status):
        """When mp3 is done playing delete and go to next audio in the queue"""
        if status == QMediaPlayer.EndOfMedia:
            self.remove_temp_voice_file(
                self.media_player.currentMedia().canonicalUrl().toLocalFile()
            )
            self.play_next_audio()
        elif status == QMediaPlayer.StoppedState:
            self.queue_timer.start(1000)

    def check_queue(self):
        """checks if the player has stopped and plays next in queue if true"""
        if self.media_player.state() == QMediaPlayer.StoppedState and self.playback_enabled:
            self.play_next_audio()

    def stop_voice(self):
        """Stops tts and clears the queue"""
        self.playback_enabled = False
        self.media_player.stop()
        self.text_queue.queue.clear()

