"""Translating with NLLB-200 and checking every translation (from dose_safe.ipynb, sections 5-6).

Both translators below work the same way: translate(texts, src_code, tgt_code, n_candidates)
returns, for each text, its top n translations, best first.
- NllbTranslator runs Meta's NLLB-200 model (about 2.5 GB, downloaded on first use).
- FakeTranslator answers from a table, so tests run in a second without the model.
"""
import threading

from .checks import FORWARD_CHECKS, safety_checks
from .languages import LANGUAGES

MODEL_NAME = "facebook/nllb-200-distilled-600M"  # free translation model from Meta (200 languages)
ENGLISH_CODE = "eng_Latn"
MAX_TOKENS = 256  # longer input would be cut off by the model without warning, so we refuse it


class NllbTranslator:
    def __init__(self, model_name=MODEL_NAME, device=None):
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        self._torch = torch
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        if self.device == "cuda":
            model = model.half()  # half precision: faster on GPU
        self.model = model.to(self.device).eval()
        self._lock = threading.Lock()  # translate() sets tokenizer.src_lang, so one call at a time

    def token_count(self, text):
        return len(self.tokenizer(text)["input_ids"])

    def translate(self, texts, src_code, tgt_code, n_candidates=1, num_beams=4, batch_size=16):
        num_beams = max(num_beams, n_candidates)
        results = []
        with self._lock, self._torch.inference_mode():
            self.tokenizer.src_lang = src_code
            for start in range(0, len(texts), batch_size):
                batch = texts[start:start + batch_size]
                inputs = self.tokenizer(batch, return_tensors="pt", padding=True, truncation=True,
                                        max_length=MAX_TOKENS).to(self.device)
                output = self.model.generate(
                    **inputs, forced_bos_token_id=self.tokenizer.convert_tokens_to_ids(tgt_code),
                    num_beams=num_beams, num_return_sequences=n_candidates, max_length=MAX_TOKENS)
                decoded = self.tokenizer.batch_decode(output, skip_special_tokens=True)
                for i in range(len(batch)):
                    results.append(decoded[i * n_candidates:(i + 1) * n_candidates])
        return results


class FakeTranslator:
    """Answers from a table {(text, target code): [best translation, next best, ...]}.
    Text that isn't in the table comes back unchanged. Counts words instead of model tokens."""

    def __init__(self, table=None):
        self.table = table or {}

    def token_count(self, text):
        return len(text.split())

    def translate(self, texts, src_code, tgt_code, n_candidates=1, **_):
        return [list(self.table.get((text, tgt_code), [text]))[:n_candidates] for text in texts]


def translate_and_check(translator, texts, language, n_candidates):
    """Translate each English text, translate every candidate back, run the checks, and keep the
    model's first choice ("baseline") and the candidate that passes the most checks ("safer")."""
    spec = LANGUAGES[language]
    candidates = translator.translate(texts, ENGLISH_CODE, spec["code"], n_candidates=n_candidates)
    flat = [translation for options in candidates for translation in options]
    backs = [options[0] for options in translator.translate(flat, spec["code"], ENGLISH_CODE)]
    results, k = [], 0
    for source, options in zip(texts, candidates):
        scored = []
        for rank, translation in enumerate(options):
            checks = safety_checks(source, translation, backs[k], spec)
            scored.append({"rank": rank, "translation": translation, "back": backs[k], "checks": checks,
                           "failed": [name for name, c in checks.items() if not c["ok"]]})
            k += 1
        safer = min(scored, key=lambda option: (
            sum(name in FORWARD_CHECKS for name in option["failed"]),  # problems in the translation itself
            len(option["failed"]),                                     # then problems overall
            option["rank"]))                                           # then the model's own ranking
        results.append({"source": source, "baseline": scored[0], "safer": safer,
                        "changed": safer["rank"] != 0})
    return results
