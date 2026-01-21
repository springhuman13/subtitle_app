from dataclasses import dataclass
from PySide6.QtCore import QSettings

@dataclass
class ProcessingOptions:
    save_source_srt: bool = False
    save_target_srt: bool = False
    burn_hardsubs: bool = True


MODEL_SIZE = "large-v3"
DEVICE = "cuda"  # "cpu"

NO_SPEECH_THRESHOLD = 0.6
LOGPROB_THRESHOLD = -1.0

BATCH_SIZE = 10

SUPPORTED_FORMATS = ["mp4", "mkv", "avi", "mov", "webm"]

DEEPL_API_KEY = "d5937bed-78cf-4eba-8b5e-b5f1ce37be99:fx"

settings = QSettings("SubtitleApp", "SubtitleApp")

STATUS_PENDING = "▶️"
STATUS_WORKING = "⏳"
STATUS_DONE = "✅"
STATUS_ERROR = "❌"