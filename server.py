"""Dose-Safe Translator web app: the pages in web/ and a small JSON API.

Run it on your computer:   uvicorn server:app --port 7860   then open http://127.0.0.1:7860
The first start downloads the translation model (about 2.5 GB).
"""
import logging
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from dose_safe.checks import FORWARD_CHECKS
from dose_safe.languages import LANGUAGES, TESTED_LANGUAGES
from dose_safe.translator import MAX_TOKENS, translate_and_check

WEB_DIR = Path(__file__).parent / "web"
SAFER_CANDIDATES = 5  # translations to try in safer mode
log = logging.getLogger("dose_safe")


class CheckRequest(BaseModel):
    english: str = Field(max_length=2000)
    language: str
    safer: bool = True


def create_app(load_translator, load_in_background=True):
    """`load_translator` makes the translator. It runs once at startup, in the background by default,
    because the real model takes a minute or more to load and the page should answer meanwhile."""
    state = {"translator": None, "status": "warming_up"}

    def load():
        try:
            state["translator"] = load_translator()
            state["status"] = "ready"
        except Exception:
            log.exception("Could not load the translation model")
            state["status"] = "error"

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
        return {"status": state["status"],
                "languages": [{"name": name, "tested": name in TESTED_LANGUAGES} for name in LANGUAGES]}

    @app.post("/api/check")
    def check(request: CheckRequest):
        translator = state["translator"]
        if translator is None:
            raise HTTPException(503, detail=state["status"])
        if request.language not in LANGUAGES:
            raise HTTPException(400, detail="Unknown language")
        english = " ".join(request.english.split())
        if not english:
            raise HTTPException(422, detail="Type a medicine instruction in English first")
        answer = {"english": english, "language": request.language,
                  "language_tested": request.language in TESTED_LANGUAGES}
        if translator.token_count(english) > MAX_TOKENS:
            return {**answer, "verdict": "too_long"}

        started = time.perf_counter()
        n_candidates = SAFER_CANDIDATES if request.safer else 1
        result = translate_and_check(translator, [english], request.language, n_candidates)[0]
        chosen = result["safer"] if request.safer else result["baseline"]
        checks = [{"name": name, "ok": c["ok"], "detail": "" if c["ok"] else c["detail"],
                   "looks_at": "translation" if name in FORWARD_CHECKS else "back-translation"}
                  for name, c in chosen["checks"].items()]
        checks.sort(key=lambda c: c["ok"])  # failed checks first, otherwise in the usual order
        return {**answer,
                "verdict": "check" if chosen["failed"] else "no_problems_found",
                "translation": chosen["translation"],
                "back_translation": chosen["back"],
                "checks": checks,
                "candidates_tried": n_candidates,
                "changed": result["changed"],
                "seconds": round(time.perf_counter() - started, 1)}

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


app = create_app(_load_nllb)
