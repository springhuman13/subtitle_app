from core.translator import GoogleTranslatorWrapper, M2M100Translator, NLLB200Translator
from dictionary.languages import GOOGLE_LANGS, M2M100_LANGS, NLLB200_LANGS, DEEPL_LANGS 

TRANSLATORS = {
    "Google Translate": {
        "factory": lambda src, tgt: GoogleTranslatorWrapper(src, tgt),
        "langs": GOOGLE_LANGS
    },
    "Local (M2M100)": {
        "factory": lambda src, tgt: M2M100Translator(src, tgt),
        "langs": M2M100_LANGS
    },
    "Local (NLLB200)": {
        "factory": lambda src, tgt: NLLB200Translator(src, tgt),
        "langs": NLLB200_LANGS
    },
    "DeepL (VPN)": {
        "factory": lambda src, tgt: NLLB200Translator(src, tgt),
        "langs": DEEPL_LANGS
    },
}

