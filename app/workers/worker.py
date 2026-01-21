from PySide6.QtCore import QThread, Signal
from pathlib import Path

from core.whisper_engine import transcribe
from core.subtitle_writer import build_subtitles, save_srt, delete_srt
from core.video_burner import burn
from config import ProcessingOptions


class VideoWorker(QThread):
    progress = Signal(str)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, video_path, whisper_lang, source_lang, target_lang, translator, options: ProcessingOptions, output_dir=None):
        super().__init__()
        self.video_path = Path(video_path)
        self.whisper_lang = whisper_lang
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.translator = translator
        self.options = options

        if output_dir is None:
            self.output_dir = self.video_path.parent
        else:
            self.output_dir = Path(output_dir)

    def run(self):
        try:
            self.progress.emit("Transcribing…")
            result = transcribe(str(self.video_path), self.whisper_lang)
            self.progress.emit("Translating…")
            src, tgt = build_subtitles(
                result["segments"],
                self.translator,
                self.progress.emit
            )

            base = self.output_dir / self.video_path.stem

            if self.options.save_source_srt:
                save_srt(src, str(base.with_suffix(f".{self.source_lang}.srt")))

            save_srt(tgt, str(base.with_suffix(f".{self.target_lang}.srt")))

            if self.options.burn_hardsubs:
                self.progress.emit("Burning subtitles…")
                burn(
                    str(self.video_path),
                    str(base.with_suffix(f".{self.target_lang}.srt")),
                    str(base.with_name(f"{base.name}_{self.target_lang}.mp4"))
                )

            if not self.options.save_target_srt:
                delete_srt(str(base.with_suffix(f".{self.target_lang}.srt")))

            self.finished.emit("Done")

        except Exception as e:
            self.error.emit(str(e))
