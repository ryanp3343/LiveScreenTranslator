import queue
import pytest
from unittest.mock import MagicMock, patch
from PyQt5.QtCore import QObject
from PyQt5.QtMultimedia import QMediaPlayer
from components.text_to_speech import TextToSpeech
LANGUAGES_GOOGLE = [
    ("Afrikaans", "af"),
    ("Albanian", "sq"),
    ("Amharic", "am"),
    ("Arabic", "ar"),
    ("Armenian", "hy"),
    ("Azerbaijani", "az"),
    ("Basque", "eu"),
    ("Belarusian", "be"),
    ("Bengali", "bn"),
    ("Bosnian", "bs"),
    ("Bulgarian", "bg"),
    ("Catalan", "ca"),
    ("Cebuano", "ceb"),
    ("Chinese (Simplified)", "zh-cn"),
    ("Chinese (Traditional)", "zh-tw"),
    ("Corsican", "co"),
    ("Croatian", "hr"),
    ("Czech", "cs"),
    ("Danish", "da"),
    ("Dutch", "nl"),
    ("English", "en"),
    ("Esperanto", "eo"),
    ("Estonian", "et"),
    ("Finnish", "fi"),
    ("French", "fr"),
    ("Frisian", "fy"),
    ("Galician", "gl"),
    ("Georgian", "ka"),
    ("German", "de"),
    ("Greek", "el"),
    ("Gujarati", "gu"),
    ("Haitian Creole", "ht"),
    ("Hausa", "ha"),
    ("Hawaiian", "haw"),
    ("Hebrew", "he"),
    ("Hindi", "hi"),
    ("Hungarian", "hu"),
    ("Icelandic", "is"),
    ("Igbo", "ig"),
    ("Indonesian", "id"),
    ("Irish", "ga"),
    ("Italian", "it"),
    ("Japanese", "ja"),
    ("Javanese", "jw"),
    ("Kannada", "kn"),
    ("Kazakh", "kk"),
    ("Khmer", "km"),
    ("Korean", "ko"),
    ("Kurdish (Kurmanji)", "ku"),
    ("Kyrgyz", "ky"),
    ("Lao", "lo"),
    ("Latin", "la"),
    ("Latvian", "lv"),
    ("Lithuanian", "lt"),
    ("Luxembourgish", "lb"),
    ("Macedonian", "mk"),
    ("Malagasy", "mg"),
    ("Malay", "ms"),
    ("Malayalam", "ml"),
    ("Maltese", "mt"),
    ("Maori", "mi"),
    ("Marathi", "mr"),
    ("Mongolian", "mn"),
    ("Nepali", "ne"),
    ("Norwegian", "no"),
    ("Pashto", "ps"),
    ("Persian", "fa"),
    ("Polish", "pl"),
    ("Portuguese", "pt"),
    ("Punjabi", "pa"),
    ("Romanian", "ro"),
    ("Russian", "ru"),
    ("Serbian", "sr"),
    ("Sesotho", "st"),
    ("Shona", "sn"),
    ("Sindhi", "sd"),
    ("Sinhala", "si"),
    ("Slovak", "sk"),
    ("Slovenian", "sl"),
    ("Somali", "so"),
    ("Spanish", "es"),
    ("Sundanese", "su"),
    ("Swahili", "sw"),
    ("Swedish", "sv"),
    ("Tagalog", "tl"),
    ("Tajik", "tg"),
    ("Tamil", "ta"),
    ("Telugu", "te"),
    ("Thai", "th"),
    ("Turkish", "tr"),
    ("Ukrainian", "uk"),
    ("Urdu", "ur"),
    ("Uzbek", "uz"),
    ("Vietnamese", "vi"),
    ("Welsh", "cy"),
    ("Xhosa", "xh"),
    ("Yiddish", "yi"),
    ("Yoruba", "yo"),
    ("Zulu", "zu"),
]

@pytest.fixture
def text_to_speech():
    parent = QObject()
    return TextToSpeech(parent)


def test_init(text_to_speech):
    assert isinstance(text_to_speech.media_player, QMediaPlayer)
    assert isinstance(text_to_speech.text_queue, queue.Queue)
    assert text_to_speech.playback_enabled


@patch("components.text_to_speech.tempfile.NamedTemporaryFile")
@patch("components.text_to_speech.gTTS")
@patch("components.text_to_speech.QUrl.fromLocalFile")
def test_play_next_audio(mock_qurl_from_local_file, mock_gtts, mock_tempfile, text_to_speech):
    mock_gtts_instance = MagicMock()
    mock_gtts.return_value = mock_gtts_instance
    mock_tempfile_instance = MagicMock()
    mock_tempfile.return_value = mock_tempfile_instance
    mock_qurl = MagicMock()
    mock_qurl_from_local_file.return_value = mock_qurl

    text_to_speech.text_queue.put(("Hello", "en"))

    text_to_speech.play_next_audio()
    mock_gtts.assert_called_once_with(text="Hello", lang="en")
    mock_tempfile.assert_called_once_with(delete=False, suffix=".mp3")
    mock_gtts_instance.save.assert_called_once_with(mock_tempfile_instance.name)
    mock_qurl_from_local_file.assert_called_once_with(mock_tempfile_instance.name)


@patch("components.text_to_speech.QFile")
def test_remove_temp_voice_file(mock_qfile, text_to_speech):
    text_to_speech.remove_temp_voice_file("test.mp3")

    mock_qfile.exists.assert_called_once_with("test.mp3")
    mock_qfile.remove.assert_called_once_with("test.mp3")


def test_stop_voice(text_to_speech):
    text_to_speech.stop_voice()
    assert not text_to_speech.playback_enabled
    assert text_to_speech.media_player.state() == QMediaPlayer.StoppedState
    assert text_to_speech.text_queue.empty()

@patch("components.text_to_speech.TextToSpeech.play_next_audio")
def test_play_text_voice_for_all_languages(mock_play_next_audio, text_to_speech):
    test_text = "Hello, World!"

    for language, code in LANGUAGES_GOOGLE:
        text_to_speech.play_text_voice(test_text, code)
        assert (test_text, code) in text_to_speech.text_queue.queue
    assert mock_play_next_audio.call_count == len(LANGUAGES_GOOGLE)


