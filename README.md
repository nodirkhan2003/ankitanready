# Anki-Tan | Flashcard Generator

Bu loyiha PDF kitoblardan avtomatik ravishda Anki flashcardlarini yaratish uchun mo'ljallangan.

## Xususiyatlari
- PDF dan matn ajratib olish (sahifalar oralig'i bilan)
- .txt, .apkg va .json formatlarida natija olish
- Ko'p tilli interfeys (UZ, EN, RU)
- Anki-Tan yordamchi personaji

## O'rnatish

1. Kerakli kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```

2. Anki-Tan personaji rasmini `static/images/anki-tan.png` joyiga qo'ying.

3. Loyihani ishga tushiring:
   ```bash
   python main.py
   ```

4. Brauzerda `http://127.0.0.1:8000` manziliga kiring.

## Eslatma
Hozirda matnni tarjima qilish qismi mock (namuna) sifatida ishlamoqda. Uni o'zingizning API'ngizga `main.py` faylidagi `handle_upload` funksiyasi orqali ulashingiz mumkin.
