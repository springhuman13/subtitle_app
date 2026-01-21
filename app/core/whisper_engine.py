import whisper

from config import MODEL_SIZE, DEVICE, NO_SPEECH_THRESHOLD, LOGPROB_THRESHOLD

_model = None


def get_model():
    global _model
    if _model is None:
        _model = whisper.load_model(MODEL_SIZE, device=DEVICE)
    return _model


def transcribe(video_path: str, source_lang: str):
    model = get_model()
    return model.transcribe(
        video_path,
        language=source_lang,
        fp16=(DEVICE == "cuda"),
        condition_on_previous_text=False,
        temperature=0,
        no_speech_threshold=NO_SPEECH_THRESHOLD,
        logprob_threshold=LOGPROB_THRESHOLD,
    )
