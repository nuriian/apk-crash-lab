# MoneyPrinterTurbo via GitHub Action

Generate video MoneyPrinterTurbo tanpa install apa pun di lokal.
Tinggal isi form di tab Actions → video jadi → download dari Artifacts.

Upstream: https://github.com/harry0703/MoneyPrinterTurbo
(Workflow ini checkout upstream `main` setiap run, jadi selalu versi terbaru.)

## Setup sekali saja (5 menit)

1. **Buat repo baru** di GitHub (private disarankan, karena pakai API key),
   lalu upload semua file dari template ini ke repo tersebut
   (atau push via git).
2. Daftar API key yang dibutuhkan:
   - **LLM** (pilih salah satu, untuk generate script):
     - Gemini — https://aistudio.google.com/app/apikey (ada free tier)
     - Groq — https://console.groq.com/keys (ada free tier)
     - DeepSeek — https://platform.deepseek.com/api_keys (murah)
     - OpenAI / OpenRouter / Moonshot / lainnya
   - **Footage** (pilih salah satu, untuk素材 video):
     - Pexels — https://www.pexels.com/api/ (gratis)
     - Pixabay — https://pixabay.com/api/docs/ (gratis)
   - Voice pakai Edge TTS — **gratis, tanpa key**.
3. Masukkan key ke repo: **Settings → Secrets and variables → Actions →
   New repository secret**:
   | Secret | Isi | Wajib |
   |---|---|---|
   | `LLM_API_KEY` | API key LLM | Ya |
   | `PEXELS_API_KEY` | API key Pexels | Salah satu footage |
   | `PIXABAY_API_KEY` | API key Pixabay | Salah satu footage |
4. Selesai. Tidak ada file config berisi key di repo ini —
   `config.toml` dibuat otomatis di dalam runner setiap run.

## Cara generate video

1. Buka tab **Actions** → **Generate Video (MoneyPrinterTurbo)** →
   **Run workflow**.
2. Isi form. Ada **2 mode**:
   - **Mode A — Hermes yang generate (tanpa LLM key):**
     minta script + terms ke Hermes ("buatkan video_script dan
     video_terms untuk topik X, bahasa Indonesia"), lalu isi:
     - `video_subject` — judul/label (wajib diisi GitHub).
     - `video_script` — script narasi jadi dari Hermes.
     - `video_terms` — search terms dari Hermes (**wajib** di mode ini).
     - `llm_api_key` — kosongkan. LLM tidak dipanggil sama sekali.
   - **Mode B — LLM di Action yang generate (butuh LLM key):**
     - `video_subject` — topik video.
     - `video_script` + `video_terms` — kosongkan.
     - `llm_provider` — harus sesuai dengan key (default `gemini`).
     - `llm_api_key` — isi per-run, atau simpan di secret `LLM_API_KEY`.
     - `llm_model` — kosongkan = pakai default upstream.
   - **Input umum (kedua mode):**
   - `video_language` — `auto` / `id-ID` / `en-US`.
   - `pexels_api_key` / `pixabay_api_key` — isi per-run,
     atau simpan di secret (salah satu footage wajib ada).
   - `video_source` — `pexels` / `pixabay` (harus punya key-nya).
   - `video_aspect` — `9:16` (Shorts/TikTok) / `16:9` / `1:1`.
   - `paragraph_number` — 1–5 (makin banyak makin lama prosesnya).
   - `video_count` — 1–3.
   - `voice_name` — default `id-ID-GadisNeural`.
     English: `en-US-AriaNeural`, `en-US-GuyNeural`, dll.
     Tanpa voiceover: isi `no-voice`.
   - `bgm_type` — `random` / `none`.
   - `stop_at` — biarkan `video` (full). Pilihan lain
     (`script`, `audio`, ...) hanya untuk debug.
3. Klik **Run workflow**, tunggu 5–15 menit.
4. Saat job selesai, download hasil di bagian **Artifacts**
   (`video-N`): file `video-1.mp4` (+ `manifest.json`, `run.log`).
   Artifact tersimpan 7 hari.

## Struktur repo template

```
.github/workflows/generate.yml  # workflow utama (form input + pipeline)
scripts/make_config.py           # bikin config.toml dari secrets + inputs
scripts/collect_results.py       # salin final-*.mp4 ke output/
```

## Catatan

- Setiap run memakai GitHub-hosted runner (`ubuntu-latest`) — gratis
  2000 menit/bulan untuk akun free. Satu video pendek ≈ 5–15 menit.
- Timeout job 60 menit.
- `resource/songs` dan font bawaan upstream dipakai apa adanya.
- Kalau butuh opsi CLI lain (subtitle style, bgm custom, dsb),
  edit `generate.yml` — semua flag `cli.py` upstream didukung pola yang sama.
