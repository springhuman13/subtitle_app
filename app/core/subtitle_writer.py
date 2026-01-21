import srt
from datetime import timedelta
from pathlib import Path
from config import BATCH_SIZE

def build_subtitles(segments, translator=None, progress_cb=None):
    source_subs = []
    target_subs = []

    texts = []
    meta = []

    idx = 1
    for seg in segments:
        text = seg["text"].strip()
        if not text:
            continue

        start = timedelta(seconds=seg["start"])
        end = timedelta(seconds=seg["end"])

        source_subs.append(srt.Subtitle(idx, start, end, text))

        texts.append(text)
        meta.append((idx, start, end))
        idx += 1

    total = len(texts)

    if translator:
        for i in range(0, total, BATCH_SIZE):
            batch_texts = texts[i:i + BATCH_SIZE]
            translated = translator.translate_batch(batch_texts)

            for (idx, start, end), text in zip(meta[i:i + BATCH_SIZE], translated):
                target_subs.append(srt.Subtitle(idx, start, end, text))

            if progress_cb:
                progress_cb(f"Translating {min(i + BATCH_SIZE, total)}/{total}")

    return source_subs, target_subs

def save_srt(subs, path: Path):
    path = Path(path)
    path.write_text(srt.compose(subs), encoding="utf-8")


def delete_srt(path: Path):
    try:
        Path(path).unlink()
    except FileNotFoundError:
        pass