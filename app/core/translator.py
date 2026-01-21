from config import DEEPL_API_KEY

class BaseTranslator:
    def translate(self, text: str) -> str:
        raise NotImplementedError
    
    def translate_batch(self, texts: list[str]) -> list[str]:
        return [self.translate(t) for t in texts]


class GoogleTranslatorWrapper(BaseTranslator):
    def __init__(self, source, target):
        from deep_translator import GoogleTranslator
        self.translator = GoogleTranslator(source=source, target=target)

    def translate(self, text: str) -> str:
        try:
            return self.translator.translate(text)
        except Exception:
            return text

    def translate_batch(self, texts: list[str]) -> list[str]:
        joined = "\n".join(texts)
        translated = self.translator.translate(joined)
        return translated.split("\n")


class M2M100Translator(BaseTranslator):
    def __init__(self, source, target):
        from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
        import torch

        self.tokenizer = M2M100Tokenizer.from_pretrained("facebook/m2m100_418M")
        self.model = M2M100ForConditionalGeneration.from_pretrained("facebook/m2m100_418M")
        self.source = source
        self.target = target
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def translate_batch(self, texts: list[str]) -> list[str]:
        self.tokenizer.src_lang = self.source
        encoded = self.tokenizer(texts, return_tensors="pt", padding=True).to(self.device)

        generated = self.model.generate(
            **encoded,
            forced_bos_token_id=self.tokenizer.get_lang_id(self.target)
        )

        return self.tokenizer.batch_decode(generated, skip_special_tokens=True)

    def translate(self, text: str) -> str:
        return self.translate_batch([text])[0]


class NLLB200Translator(BaseTranslator):
    def __init__(self, source, target, model_name="facebook/nllb-200-distilled-600M", device="cuda"):
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        import torch

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

        self.source = source
        self.target = target

    def translate_batch(self, texts: list[str]) -> list[str]:
        self.tokenizer.src_lang = self.source

        encoded = self.tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        ).to(self.device)

        forced_bos_token_id = self.tokenizer.convert_tokens_to_ids(self.target)

        generated = self.model.generate(
            **encoded,
            forced_bos_token_id=forced_bos_token_id,
            max_length=512,
            num_beams=4
        )

        return self.tokenizer.batch_decode(generated, skip_special_tokens=True)

    def translate(self, text: str) -> str:
        return self.translate_batch([text])[0]
        
class DEEPLTranslator(BaseTranslator):
    def __init__(self, source, target):
        import deepl
        self.translator = deepl.Translator(DEEPL_API_KEY)
        self.source = source
        self.target = target

    def translate(self, text: str) -> str:
        try:
            return self.translator.translate_text(
                text,
                source_lang=self.source,
                target_lang=self.target
            ).text
        except Exception:
            return text

    def translate_batch(self, texts: list[str]) -> list[str]:
        try:
            results = self.translator.translate_text(
                texts,
                source_lang=self.source,
                target_lang=self.target
            )
            return [r.text for r in results]
        except Exception:
            return texts