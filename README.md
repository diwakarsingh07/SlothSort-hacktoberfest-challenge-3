# 🦥 SlothSort: Slow and Steady AI File Tidier

> *"Let the sloth tidy your chaotic desktop and downloads while you take a nap."*
>
> A submission for the **[Hacktoberfest Open-Source AI Challenge Week 3: Slow and Steady](https://dev.to/challenges/hacktoberfest-week3-2026-10-19)** (Celebrating International Sloth Day 🦥).

---

## 📖 What is SlothSort?

Everyone has a messy `Downloads` or `Desktop` folder filled with `Screenshot 2026-10-21.png`, `INV_98242_final_v2.txt`, random code snippets, coffee receipts, and untagged documents. Manually opening, reading, renaming, and filing them is the ultimate dread chore.

**SlothSort** is an intelligent, privacy-first file organizer that does the heavy lifting for you. It reads and understands the semantic content of documents, receipts, code, and images, generates descriptive, clean filenames, and organizes them into structured folders—all with 1-click execution and atomic rollback safety.

---

## ✨ Key Features

- **Multi-Provider AI Architecture**:
  - 🟢 **Ollama (Primary Local)**: Runs open-weight models (`llama3.2`, `qwen2.5`, `mistral`, `moondream`) directly on your machine.
  - 🔵 **Google Cloud AI / Gemini**: High-speed multimodal analysis via `gemini-1.5-flash` or `gemini-2.0-flash`.
  - ⚡ **Groq Backup**: Blazing fast cloud inference on open weights (`llama-3.3-70b-versatile`).
  - 🔒 **Built-in Offline Heuristic Engine**: Zero-configuration, zero-latency contextual classifier that works out-of-the-box on any machine without internet or API keys.
- **Deep Content Inspection**:
  - Ingests text files, PDF documents, Word `.docx`, spreadsheets, source code, and images.
  - Recognizes invoices, receipts, tax forms, resume credentials, error captures, and developer scripts.
- **Safe by Design (Atomic Undo)**:
  - **Dry-Run Preview**: Inspect every proposed rename, destination folder, confidence score, and AI explanation before anything moves.
  - **Instant Rollback**: Every operation is logged in `.slothsort_history.json`. Click "Undo" to restore all files back to their exact original positions.
- **Background Watcher Agent**:
  - Built-in `watchdog` daemon monitors target folders (like `Downloads`) and cleans up new arrivals lazily in the background.
- **Modern Web Dashboard & Rich CLI**:
  - Interactive Tailwind CSS web interface with instant demo-file generator.
  - Sleek terminal CLI powered by `rich`.

---

## 🚀 Quick Start

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/diwakar/slothsort.git
cd slothsort
pip install -r requirements.txt
```

### 2. Launch the Web Dashboard
```bash
python app.py
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

- Click **"1-Click: Create & Test Messy Demo Folder"** to generate realistic clutter in 2 seconds.
- Click **"Scan & Preview"** to watch the AI analyze and categorize the files.
- Click **"Tidy Up Now"** to organize everything.
- Click **"Undo Last Sort"** to test the 1-click restore!

---

## 💻 CLI Usage

Prefer the terminal? Run SlothSort directly from your shell:

```bash
# 1. Preview changes (Dry Run)
python cli.py --folder ./demo_messy_folder

# 2. Apply and organize files
python cli.py --folder ./demo_messy_folder --execute

# 3. Restore files back if you change your mind
python cli.py --folder ./demo_messy_folder --undo

# 4. Run autonomous background watcher
python watcher.py --folder "C:\Users\You\Downloads" --auto
```

---

## 🏛️ Architecture Overview

```
                      +-----------------------------+
                      |   Messy Folder / Downloads   |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |   Multi-Modal Inspector     |
                      | (PDF, docx, code, text, img)|
                      +--------------+--------------+
                                     |
            +------------------------+------------------------+
            |                        |                        |
            v                        v                        v
    +---------------+        +---------------+        +---------------+
    | Local Ollama  |        | Google Cloud  |        |  Groq Llama   |
    |  (Llama 3.2)  |        |   (Gemini)    |        |    (3.3 70B)  |
    +-------+-------+        +-------+-------+        +-------+-------+
            |                        |                        |
            +------------------------+------------------------+
                                     |
                                     v
                      +-----------------------------+
                      |     Semantic Classifier     |
                      | (Clean name, Category, Reason)|
                      +--------------+--------------+
                                     |
                         [Preview or Auto-Apply]
                                     |
                                     v
                      +-----------------------------+
                      |     Organized Categories    |
                      |   + Atomic Rollback Log     |
                      +-----------------------------+
```

---

## 🌐 Why Open Innovation Matters

- **100% Personal Privacy**: Financial tax filings, medical receipts, invoices, and sensitive work documents never leave your machine when running with local open-weight models (Ollama).
- **Zero Cost & Infinite Runs**: You can leave the background watcher running 24/7 without accumulating expensive token fees.
- **Offline Resilience**: Works on an airplane, in a cabin, or during internet outages.

---

## 📄 License
MIT License. Built for the Hacktoberfest 2026 Open-Source AI Challenge.
