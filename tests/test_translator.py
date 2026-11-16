"""NllbTranslator can use a model that is already loaded (the notebook's website does)."""
import sys
import types

from dose_safe import translator as translator_module
from dose_safe.translator import NllbTranslator


class FakeModel:
    def __init__(self):
        self.calls = []

    def eval(self):
        self.calls.append("eval")
        return self

    def half(self):  # must not be called: the model is already set up by whoever loaded it
        raise AssertionError("a model passed in must not be changed")

    def to(self, device):
        raise AssertionError("a model passed in must not be moved")


def test_a_loaded_model_is_used_as_it_is(monkeypatch):
    loaded = []

    class FakeAutoTokenizer:
        @staticmethod
        def from_pretrained(name):
            loaded.append(("tokenizer", name))
            return object()

    class FakeAutoModel:
        @staticmethod
        def from_pretrained(name):
            raise AssertionError("the model must not be loaded again")

    fake_transformers = types.SimpleNamespace(AutoTokenizer=FakeAutoTokenizer,
                                              AutoModelForSeq2SeqLM=FakeAutoModel)
    monkeypatch.setitem(sys.modules, "transformers", fake_transformers)
    model = FakeModel()
    made = NllbTranslator(device="cpu", model=model)
    assert made.model is model and model.calls == ["eval"]
    assert loaded == [("tokenizer", translator_module.MODEL_NAME)]
