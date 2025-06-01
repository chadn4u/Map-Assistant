# 🗺️ AI Location Assistant API

Sistem API berbasis **FastAPI** yang memanfaatkan **Ollama (Mistral model)** dan **Google Maps API** untuk memahami maksud pengguna dan memberikan informasi lokasi atau arah dengan respons alami.

---

## 🚀 Fitur

- 🎯 **Intent Recognition via LLM (Ollama)**

  - Menyimpulkan maksud user: pencarian tempat, arah jalan, rekomendasi, dsb.

- 📍 **Integrasi Google Maps API**

  - Cari tempat, rekomendasi lokasi, dan petunjuk arah otomatis.

- 🤖 **Respons Natural via LLM**

  - Jawaban dalam gaya percakapan, lengkap dengan tautan Maps.

- 🔁 **Follow-up Handling**
  - Mendeteksi jika informasi belum lengkap (contoh: asal tidak disebutkan).

---

## 🛠️ Tech Stack

- [FastAPI](https://fastapi.tiangolo.com/)
- [Ollama](https://ollama.com/)
- [Mistral LLM](https://ollama.com/library/mistral)
- [Google Maps API](https://console.cloud.google.com/)
- Python 3.13.1

---

## 📁 Struktur Proyek

```
.
├── main.py                # FastAPI entry point
├── utils/
│   └── gmaps.py           # Fungsi pemrosesan Google Maps
├── .env                   # Variabel API Key & model config
├── requirements.txt
└── README.md
```

---

## ⚙️ Cara Menjalankan

### 1. Clone Repo

```bash
git clone https://github.com/chadn4u/Map-Assistant.git
cd Map-Assistant
```

### 2. Install Dependensi

```bash
pip install -r requirements.txt
```

> Jika file tidak tersedia:
>
> ```bash
> pip install fastapi uvicorn requests python-dotenv
> ```

### 3. Buat file `.env`

```
GOOGLE_API_KEY=your_google_api_key
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

### 4. Jalankan Ollama + Model

```bash
ollama run mistral
```

> Atau ganti dengan model lain seperti `phi3`, `gemma`, dll.

### 5. Jalankan Server

```bash
uvicorn main:app --reload
```

---

## 📬 Contoh Request

### Endpoint: `POST /send-message`

```json
{
  "prompt": "Tunjukin arah ke Coffee shop terdekat dari rumah saya"
}
```

### Respons:

```json
{
  "llm_response": {
    "intent": "direction_request",
    "origin": "rumah saya",
    "destination": "Coffee shop terdekat dari rumah saya",
    "needs_origin": true
  },
  "gmap_result": {
    "message": "Origin Info not Found"
  },
  "response_followup": "Boleh tahu kamu mulai perjalanan dari mana? Misalnya 'Galaxy Bekasi'."
}
```

---

## 🔁 Supported Intent Types

- `store_locator`: cari lokasi toko
- `map_place_search`: cari tempat umum
- `place_recommendation`: minta saran tempat
- `direction_request`: minta petunjuk arah
- `general`: sapaan atau pesan tidak relevan

---

## ✅ Tips Penggunaan

- Tambahkan lebih banyak model Ollama via `ollama pull [model]`.
- Periksa `utils/gmaps.py` untuk penyesuaian Maps API.
- Format URL Google Maps sudah dikustom untuk clickable.

---

## 👨‍💻 Developer

Dibuat oleh Richard Mario
