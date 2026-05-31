# Anki-Tan Deploy Qo'llanmasi

## API Kalit (Google Gemini)

1. https://aistudio.google.com ga kiring
2. "Get API Key" tugmasini bosing
3. Yangi API kalit yarating
4. Kalitni sayt ichidagi **API Settings** bo'limiga joylashtiring

> Kalit `main.py` ning `call_gemini_api()` funksiyasida ishlatiladi (75-qator).
> Foydalanuvchi brauzerdan kiritadi — backend serverda saqlanmaydi.

---

## 1-usul: Localhost (Eng oddiy)

```bash
# 1. Loyihani klonlash
git clone https://github.com/murtazoyev-ai/ankitan.git
cd ankitan

# 2. Virtual muhit yaratish
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Kutubxonalarni o'rnatish
pip install -r requirements.txt

# 4. Serverni ishga tushirish
python main.py
```

Brauzerda oching: **http://localhost:8000**

---

## 2-usul: Render.com (Bepul hosting)

### Qadam 1: GitHub repo tayyorlash
- Loyihani GitHub ga push qiling

### Qadam 2: Render.com da sozlash
1. https://render.com ga kiring (GitHub bilan login)
2. **"New +"** → **"Web Service"** tanlang
3. GitHub reponi ulang: `murtazoyev-ai/ankitan`
4. Sozlamalar:
   - **Name**: `ankitan`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app`
5. **"Create Web Service"** tugmasini bosing

5-10 daqiqada sayt tayyor bo'ladi.

---

## 3-usul: Cloudflare Pages + Workers

Cloudflare Python backend ni to'g'ridan-to'g'ri qo'llab-quvvatlamaydi,
shuning uchun **Cloudflare Tunnel** ishlatamiz:

### Qadam 1: Serverni localhost da ishga tushiring
```bash
python main.py
```

### Qadam 2: Cloudflare Tunnel o'rnatish
```bash
# cloudflared o'rnatish
# Linux:
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared

# Tunnel yaratish
./cloudflared tunnel login
./cloudflared tunnel create ankitan
./cloudflared tunnel route dns ankitan ankitan.yourdomain.com
./cloudflared tunnel run --url http://localhost:8000 ankitan
```

Endi `ankitan.yourdomain.com` orqali sayt ochiladi.

---

## 4-usul: Docker bilan deploy

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "main:app"]
```

```bash
docker build -t ankitan .
docker run -p 8000:8000 ankitan
```

---

## Loyiha tuzilmasi

```
AnkiTan/
├── main.py              # Backend (FastAPI + Gemini API)
├── requirements.txt     # Python kutubxonalar
├── Procfile             # Render/Heroku uchun
├── templates/
│   └── index.html       # Asosiy sahifa (frontend)
├── static/
│   └── images/
│       └── ankitan.svg  # Maskot rasmi
├── uploads/             # Vaqtinchalik PDF fayllar
└── output/              # Yaratilgan .txt, .apkg, .json fayllar
```
