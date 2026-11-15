"""Dose-Safe Translator web app: the pages in web/ and a small JSON API.

Run it on your computer:   uvicorn server:app --port 7860   then open http://127.0.0.1:7860
The first start downloads the translation model (about 2.5 GB).
"""
import base64
import binascii
import logging
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from dose_safe.checks import FORWARD_CHECKS
from dose_safe.languages import LANGUAGES, TESTED_LANGUAGES
from dose_safe.lookup import LabelNotFound, LabelSourceDown, search_terms
from dose_safe.ocr import instructions_from_lines, looks_english
from dose_safe.translator import MAX_TOKENS, translate_and_check

WEB_DIR = Path(__file__).parent / "web"
SAFER_CANDIDATES = 5  # translations to try in safer mode
MAX_LINES = 20  # label lines checked in one request (photo mode sends one label section at a time)
log = logging.getLogger("dose_safe")


class CheckRequest(BaseModel):
    english: str = Field(max_length=2000)
    language: str
    safer: bool = True


class LinesRequest(BaseModel):
    lines: list[Annotated[str, Field(max_length=2000)]] = Field(min_length=1, max_length=MAX_LINES)
    language: str
    safer: bool = True


class LabelRequest(BaseModel):
    image: str | None = Field(None, max_length=15_000_000)  # a photo, as a base64 data: URL
    code: str | None = Field(None, max_length=40)  # or the barcode / NDC number, typed


def check_lines(translator, texts, language, safer):
    """Translate and check each English line; one answer per line, in order."""
    answers = [None] * len(texts)
    todo = []
    for i, text in enumerate(texts):
        if translator.token_count(text) > MAX_TOKENS:
            answers[i] = {"english": text, "verdict": "too_long"}
        else:
            todo.append(i)
    n_candidates = SAFER_CANDIDATES if safer else 1
    results = translate_and_check(translator, [texts[i] for i in todo], language, n_candidates) if todo else []
    for i, result in zip(todo, results):
        chosen = result["safer"] if safer else result["baseline"]
        checks = [{"name": name, "ok": c["ok"], "detail": "" if c["ok"] else c["detail"],
                   "looks_at": "translation" if name in FORWARD_CHECKS else "back-translation"}
                  for name, c in chosen["checks"].items()]
        checks.sort(key=lambda c: c["ok"])  # failed checks first, otherwise in the usual order
        answers[i] = {"english": texts[i],
                      "verdict": "check" if chosen["failed"] else "no_problems_found",
                      "translation": chosen["translation"],
                      "back_translation": chosen["back"],
                      "checks": checks,
                      "candidates_tried": n_candidates,
                      "changed": result["changed"]}
    return answers


def label_from_the_internet(code):
    """The label for a barcode or NDC number, from openFDA and DailyMed."""
    import requests

    from dose_safe.labels import active_ingredients, label_sections
    from dose_safe.lookup import fetch_label_xml, find_label

    product = find_label(code, requests)
    root = fetch_label_xml(product["set_id"], requests)
    return {"product": product, "active_ingredients": active_ingredients(root),
            "sections": label_sections(root)}


def photo_bytes(data_url):
    try:
        return base64.b64decode(data_url.split(",", 1)[-1], validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(422, detail="That photo didn't upload properly. Try taking it again.")


def create_app(load_translator, load_in_background=True, find_label=label_from_the_internet,
               load_photo_reader=None):
    """`load_translator` makes the translator. It runs once at startup, in the background by default,
    because the real model takes a minute or more to load and the page should answer meanwhile.
    `find_label(code)` looks a barcode up (tests pass a stand-in that doesn't use the internet).
    `load_photo_reader()` makes `read(image_bytes) -> lines of (word, confidence)`, which reads the
    printed text of a box without a usable barcode; it loads after the translator. Without it, photo
    mode only reads barcodes."""
    state = {"translator": None, "status": "warming_up", "photo_reader": None,
             "photo_status": "off" if load_photo_reader is None else "warming_up"}
    labels_seen = {}  # barcode -> label, so showing the same box again doesn't download it again
    photo_lock = threading.Lock()  # one photo is read at a time

    def load():
        try:
            state["translator"] = load_translator()
            state["status"] = "ready"
        except Exception:
            log.exception("Could not load the translation model")
            state["status"] = "error"
        if load_photo_reader is not None:
            try:
                state["photo_reader"] = load_photo_reader()
                state["photo_status"] = "ready"
            except Exception:
                log.exception("Could not start the reader for printed text")
                state["photo_status"] = "off"

    @asynccontextmanager
    async def lifespan(_app):
        if load_in_background:
            threading.Thread(target=load, daemon=True).start()
        else:
            load()
        yield

    app = FastAPI(title="Dose-Safe Translator", lifespan=lifespan, docs_url=None, redoc_url=None)

    @app.get("/api/status")
    def status():
        return {"status": state["status"], "photo_reader": state["photo_status"],
                "languages": [{"name": name, "tested": name in TESTED_LANGUAGES} for name in LANGUAGES]}

    def ready_translator(language):
        translator = state["translator"]
        if translator is None:
            raise HTTPException(503, detail=state["status"])
        if language not in LANGUAGES:
            raise HTTPException(400, detail="Unknown language")
        return translator

    @app.post("/api/check")
    def check(request: CheckRequest):
        translator = ready_translator(request.language)
        english = " ".join(request.english.split())
        if not english:
            raise HTTPException(422, detail="Type a medicine instruction in English first")
        started = time.perf_counter()
        answer = check_lines(translator, [english], request.language, request.safer)[0]
        answer = {**answer, "language": request.language,
                  "language_tested": request.language in TESTED_LANGUAGES}
        if answer["verdict"] != "too_long":
            answer["seconds"] = round(time.perf_counter() - started, 1)
        return answer

    @app.post("/api/check-lines")
    def check_many(request: LinesRequest):
        """Photo mode: every line of one label section, translated together (faster than one by one)."""
        translator = ready_translator(request.language)
        lines = [" ".join(line.split()) for line in request.lines]
        if not all(lines):
            raise HTTPException(422, detail="One of the lines is empty")
        started = time.perf_counter()
        results = check_lines(translator, lines, request.language, request.safer)
        return {"language": request.language, "language_tested": request.language in TESTED_LANGUAGES,
                "results": results, "seconds": round(time.perf_counter() - started, 1)}

    def official_label(code):
        """The label for a barcode or NDC number. Raises ValueError (not a barcode), LabelNotFound or
        LabelSourceDown."""
        search_terms(code)  # is it a barcode or NDC number at all?
        if code not in labels_seen:
            found = find_label(code)
            if len(labels_seen) >= 200:
                labels_seen.clear()
            labels_seen[code] = found
        return {"source": "label", "barcode": code, **labels_seen[code]}

    def printed_text(image_bytes, code, note):
        """The photo's printed text, joined into instructions, for the pharmacist to check before it's
        translated. `code` is a barcode the photo also had, and `note` why it found no label."""
        read = state["photo_reader"]
        if read is None:
            if state["photo_status"] == "warming_up":
                raise HTTPException(503, detail=(note or "No barcode found in the photo.") + " The reader "
                                    "for printed text is still starting; try this photo again in a minute.")
            if note:
                raise HTTPException(404, detail=note)
            raise HTTPException(422, detail="No barcode found in the photo. Hold the box closer so the "
                                            "barcode fills about half the picture, with no glare on it, "
                                            "or type the number under the barcode.")
        with photo_lock:
            lines = read(image_bytes)
        if lines is None:
            raise HTTPException(422, detail="That photo couldn't be opened. Take it again, or use a JPEG "
                                            "or PNG picture.")
        instructions = instructions_from_lines(lines)
        if not instructions:
            if note:
                raise HTTPException(404, detail=f"{note} To use this box anyway, photograph its Directions "
                                                "panel: the printed text is read, and you check it before "
                                                "it's translated.")
            raise HTTPException(422, detail="No barcode or printed directions could be read in this photo. "
                                            "Photograph the barcode, or the Directions panel up close, "
                                            "flat and in focus, with no glare.")
        return {"source": "photo_text", "barcode": code, "barcode_note": note,
                "instructions": instructions, "looks_english": looks_english(instructions)}

    @app.post("/api/label")
    def label(request: LabelRequest):
        """Photo mode: the official label for the barcode in a photo, or for a typed number. When a photo
        has no barcode, or one the FDA's database doesn't have, its printed text is read instead."""
        if request.image:
            from dose_safe.barcode import read_barcode

            image_bytes = photo_bytes(request.image)
            code = read_barcode(image_bytes)
            note = None
            if code:
                try:
                    return official_label(code)
                except (ValueError, LabelNotFound) as error:
                    note = str(error)
                except LabelSourceDown as error:
                    raise HTTPException(502, detail=str(error))
            return printed_text(image_bytes, code, note)
        if not (request.code and request.code.strip()):
            raise HTTPException(422, detail="Take a photo of the barcode, or type its number.")
        try:
            return official_label(request.code.strip())
        except ValueError as error:
            raise HTTPException(422, detail=str(error))
        except LabelNotFound as error:
            raise HTTPException(404, detail=str(error))
        except LabelSourceDown as error:
            raise HTTPException(502, detail=str(error))

    @app.get("/", include_in_schema=False)
    def landing_page():
        page = WEB_DIR / "index.html"
        return FileResponse(page) if page.exists() else RedirectResponse("/translate")

    @app.get("/translate", include_in_schema=False)
    def translator_page():
        return FileResponse(WEB_DIR / "translate.html")

    app.mount("/static", StaticFiles(directory=WEB_DIR, check_dir=False), name="static")
    return app


def _load_nllb():
    from dose_safe.translator import NllbTranslator
    return NllbTranslator()


def _load_easyocr():
    from dose_safe.ocr import load_reader, read_lines
    reader = load_reader()
    return lambda image_bytes: read_lines(reader, image_bytes)


app = create_app(_load_nllb, load_photo_reader=_load_easyocr)
