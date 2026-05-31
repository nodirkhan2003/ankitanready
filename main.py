from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
import os
import shutil
import uuid
import re

import fitz  # PyMuPDF
import genanki
import json
import requests
from typing import List

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Anki-Tan API")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "images"), exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

ANKI_MODEL = genanki.Model(
    1607392319,
    'Anki-Tan Model',
    fields=[
        {'name': 'Question'},
        {'name': 'Answer'},
    ],
    templates=[{
        'name': 'Card 1',
        'qfmt': '{{Question}}',
        'afmt': '{{FrontSide}}<hr id="answer">{{Answer}}',
    }])

LANG_NAMES = {
    "en": "English", "ru": "Russian", "uz": "Uzbek",
    "de": "German", "fr": "French", "es": "Spanish",
    "ar": "Arabic", "tr": "Turkish", "zh": "Chinese",
    "ja": "Japanese", "ko": "Korean", "it": "Italian",
    "pt": "Portuguese", "hi": "Hindi", "fa": "Persian",
}


def call_gemini_api(api_key: str, text: str, source_lang: str, target_lang: str) -> list:
    src = LANG_NAMES.get(source_lang, source_lang)
    tgt = LANG_NAMES.get(target_lang, target_lang)

    prompt = f"""You are a language learning flashcard generator.
Given the following text in {src}, create flashcards for learning {tgt}.

Rules:
- Extract important words, phrases, and sentences from the text
- For each item, provide the original ({src}) as "front" and the translation ({tgt}) as "back"
- Create between 10 and 50 flashcards depending on text length
- Focus on useful vocabulary and key phrases
- Return ONLY a valid JSON array, no markdown, no explanation
- Format: [{{"front": "word/phrase in {src}", "back": "translation in {tgt}"}}]

Text:
{text[:15000]}"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 8192,
        }
    }

    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()

    data = response.json()
    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]

    json_match = re.search(r'\[.*\]', raw_text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())

    return json.loads(raw_text)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/api/generate")
async def handle_upload(
    file: UploadFile = File(...),
    from_page: int = Form(...),
    to_page: int = Form(...),
    source_lang: str = Form(...),
    target_lang: str = Form(...),
    api_key: str = Form(...),
):
    session_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{session_id}_{file.filename}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text_content = ""
    total_pages = 0
    try:
        doc = fitz.open(file_path)
        total_pages = len(doc)
        start = max(0, from_page - 1)
        end = min(total_pages, to_page)

        for page_num in range(start, end):
            text_content += doc[page_num].get_text()
        doc.close()
    except Exception as e:
        logger.error(f"PDF error: {e}")
        return JSONResponse({"error": f"PDF xatolik: {str(e)}"}, status_code=400)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    if not text_content.strip():
        return JSONResponse({"error": "PDF dan matn topilmadi"}, status_code=400)

    try:
        flashcards = call_gemini_api(api_key, text_content, source_lang, target_lang)
    except requests.exceptions.HTTPError as e:
        logger.error(f"Gemini API error: {e}")
        if e.response.status_code == 400:
            return JSONResponse({"error": "API kalit noto'g'ri yoki yaroqsiz"}, status_code=400)
        return JSONResponse({"error": f"Gemini API xatolik: {str(e)}"}, status_code=500)
    except Exception as e:
        logger.error(f"Generation error: {e}")
        return JSONResponse({"error": f"Flashcard yaratishda xatolik: {str(e)}"}, status_code=500)

    base_name = f"ankitan_{session_id}"

    txt_path = os.path.join(OUTPUT_DIR, f"{base_name}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        for card in flashcards:
            f.write(f"{card['front']}\t{card['back']}\n")

    json_path = os.path.join(OUTPUT_DIR, f"{base_name}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(flashcards, f, ensure_ascii=False, indent=2)

    deck = genanki.Deck(2059400110, f"Anki-Tan Deck")
    for card in flashcards:
        note = genanki.Note(model=ANKI_MODEL, fields=[card['front'], card['back']])
        deck.add_note(note)

    apkg_path = os.path.join(OUTPUT_DIR, f"{base_name}.apkg")
    genanki.Package(deck).write_to_file(apkg_path)

    return JSONResponse({
        "success": True,
        "card_count": len(flashcards),
        "files": {
            "txt": f"/download/{base_name}.txt",
            "json": f"/download/{base_name}.json",
            "apkg": f"/download/{base_name}.apkg",
        },
        "preview": flashcards[:5],
    })


@app.get("/download/{filename}")
async def download_file(filename: str):
    safe_name = os.path.basename(filename)
    file_path = os.path.join(OUTPUT_DIR, safe_name)
    if os.path.exists(file_path):
        return FileResponse(path=file_path, filename=safe_name)
    return JSONResponse({"error": "Fayl topilmadi"}, status_code=404)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
