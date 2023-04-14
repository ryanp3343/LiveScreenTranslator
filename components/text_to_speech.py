import tempfile
from gtts import gTTS
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, QIODevice, QFile

class TextToSpeech:
    def __init__(self, parent):
        self.parent = parent
        self.media_player = QMediaPlayer(self.parent)

    def play_text_voice(self, text, lang):
        tts = gTTS(text=text, lang=lang)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(temp_file.name)
        temp_file.close()

        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(temp_file.name)))
        self.media_player.play()

        self.media_player.mediaStatusChanged.connect(lambda status: self.remove_temp_voice_file(status, temp_file.name))

    def remove_temp_voice_file(self, status, file_name):
        if status == QMediaPlayer.EndOfMedia:
            if QFile.exists(file_name):
                QFile.remove(file_name)
