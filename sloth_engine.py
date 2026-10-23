"""
SlothSort: Multi-Provider AI Reasoning & Organization Engine
Supports:
1. Ollama (Local open-weight models: llama3.2, qwen2.5, mistral, etc.)
2. Google Cloud AI / Gemini (gemini-1.5-flash, gemini-2.0-flash)
3. Groq (High-speed open models: llama-3.3-70b-versatile, llama-3.1-8b-instant)
4. Built-in Offline Heuristic Engine (zero config, instant fallback)
"""

import os
import re
import json
import time
import shutil
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

class SlothEngine:
    """Manages AI reasoning, batch classification, execution, and rollback."""

    HISTORY_FILE = ".slothsort_history.json"

    def __init__(
        self,
        provider: str = "auto",
        ollama_url: str = "http://localhost:11434",
        ollama_model: str = "llama3.2",
        gemini_api_key: Optional[str] = None,
        gemini_model: str = "gemini-1.5-flash",
        groq_api_key: Optional[str] = None,
        groq_model: str = "llama-3.3-70b-versatile"
    ):
        self.provider = provider
        self.ollama_url = ollama_url.rstrip("/")
        self.ollama_model = ollama_model

        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.gemini_model = gemini_model

        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.groq_model = groq_model

        # Fast connection pre-check (cached per engine instance to avoid per-file timeout delays)
        self.is_ollama_online = self._ping_ollama()

    def _ping_ollama(self) -> bool:
        """Quick 300ms healthcheck for local Ollama."""
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags", headers={"User-Agent": "SlothSort"})
            with urllib.request.urlopen(req, timeout=0.4) as resp:
                return resp.status == 200
        except Exception:
            return False

    def check_ollama_status(self) -> Dict[str, Any]:
        """Tests if local Ollama server is running and lists installed models."""
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags", headers={"User-Agent": "SlothSort"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = [m.get("name") for m in data.get("models", [])]
                    self.is_ollama_online = True
                    return {"online": True, "models": models, "url": self.ollama_url}
        except Exception as e:
            self.is_ollama_online = False
            return {"online": False, "models": [], "error": str(e), "url": self.ollama_url}
        return {"online": False, "models": [], "url": self.ollama_url}

    def get_available_providers(self) -> Dict[str, Any]:
        """Returns the readiness status of all AI backends."""
        ollama_status = self.check_ollama_status()
        return {
            "ollama": {
                "available": ollama_status["online"],
                "models": ollama_status["models"],
                "current_model": self.ollama_model,
                "url": self.ollama_url
            },
            "gemini": {
                "available": bool(self.gemini_api_key),
                "model": self.gemini_model
            },
            "groq": {
                "available": bool(self.groq_api_key),
                "model": self.groq_model
            },
            "builtin_heuristic": {
                "available": True,
                "description": "Zero-dependency offline contextual classifier"
            }
        }

    def classify_file(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classifies a file using the configured provider or cascading fallback:
        1. Ollama (if selected or auto-online)
        2. Google Cloud AI / Gemini (if key available)
        3. Groq (if key available)
        4. Built-in Offline Heuristic (guaranteed fallback)
        """
        if self.provider == "ollama" and self.is_ollama_online:
            res = self._classify_with_ollama(file_info)
            if res:
                return res
        elif self.provider == "gemini" and self.gemini_api_key:
            res = self._classify_with_gemini(file_info)
            if res:
                return res
        elif self.provider == "groq" and self.groq_api_key:
            res = self._classify_with_groq(file_info)
            if res:
                return res
        elif self.provider == "builtin":
            return self._classify_with_heuristic(file_info)

        # Auto Cascading Mode
        # 1. Try Ollama local if online
        if self.is_ollama_online:
            res = self._classify_with_ollama(file_info)
            if res:
                return res

        # 2. Try Google Gemini
        if self.gemini_api_key:
            res = self._classify_with_gemini(file_info)
            if res:
                return res

        # 3. Try Groq backup
        if self.groq_api_key:
            res = self._classify_with_groq(file_info)
            if res:
                return res

        # 4. Built-in Heuristic
        return self._classify_with_heuristic(file_info)

    def _build_prompt(self, file_info: Dict[str, Any]) -> str:
        snippet = (file_info.get("content_snippet") or "").strip()
        hints = ", ".join(file_info.get("visual_hints", []))

        return f"""You are SlothSort, an intelligent file tidier.
Analyze this messy file and suggest:
1. A clean, meaningful semantic filename (preserve original extension).
2. A clean category subfolder name (e.g. Financial_and_Receipts, Dev_Projects, Screenshots, Invoices, Media_and_Memes, Documents, Career, Meeting_Notes).
3. A short sloth-themed explanation.

File Details:
- Current Name: {file_info.get('name')}
- Extension: {file_info.get('ext')}
- File Type: {file_info.get('group')}
- File Size: {file_info.get('size_readable')}
- Hints: {hints if hints else 'None'}
- Content Snippet:
\"\"\"
{snippet[:1000] if snippet else 'No text content available'}
\"\"\"

Respond STRICTLY in JSON format with these exact keys:
{{
  "new_name": "clean_descriptive_name{file_info.get('ext')}",
  "target_folder": "Category_Name",
  "reasoning": "Short 1-sentence explanation of what this file is and why it was named this way.",
  "confidence": 0.95
}}
"""

    def _classify_with_ollama(self, file_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Queries local Ollama open-weight model."""
        prompt = self._build_prompt(file_info)
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.2}
        }
        try:
            req = urllib.request.Request(
                f"{self.ollama_url}/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                response_text = data.get("response", "{}")
                parsed = json.loads(response_text)
                return self._sanitize_classification(parsed, file_info, f"Ollama ({self.ollama_model})")
        except Exception:
            return None

    def _classify_with_gemini(self, file_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Queries Google Cloud AI / Gemini."""
        if not self.gemini_api_key:
            return None
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel(self.gemini_model)
            prompt = self._build_prompt(file_info) + "\nOutput raw JSON only. Do not wrap in markdown tags."
            response = model.generate_content(prompt)
            text = response.text.strip()
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                return self._sanitize_classification(parsed, file_info, f"Google Gemini ({self.gemini_model})")
        except Exception:
            return None
        return None

    def _classify_with_groq(self, file_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Queries Groq open-weight inference."""
        if not self.groq_api_key:
            return None
        try:
            from groq import Groq
            client = Groq(api_key=self.groq_api_key)
            prompt = self._build_prompt(file_info)
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a file classifier. Respond ONLY with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                model=self.groq_model,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            content = chat_completion.choices[0].message.content
            parsed = json.loads(content)
            return self._sanitize_classification(parsed, file_info, f"Groq ({self.groq_model})")
        except Exception:
            return None

    def _classify_with_heuristic(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligent, zero-latency local fallback engine.
        Uses contextual patterns, content semantics, and metadata to organize files.
        """
        name = file_info.get("name", "")
        stem = file_info.get("stem", "")
        ext = file_info.get("ext", "").lower()
        snippet = (file_info.get("content_snippet") or "").lower()
        group = file_info.get("group", "other")
        date_str = datetime.now().strftime("%Y-%m")

        target_folder = "Miscellaneous"
        new_name = name
        reasoning = "Classified based on file characteristics and structure."
        confidence = 0.85

        # Check Meeting Notes first
        meeting_keywords = ["meeting", "agenda", "minutes", "action items", "all-hands", "sync", "attendees"]
        if (group == "documents" or ext in {".txt", ".md"}) and (any(k in name.lower() for k in meeting_keywords) or any(k in snippet for k in ["agenda", "action items", "attendees"])):
            target_folder = "Meeting_Notes"
            new_name = f"Meeting_{date_str}_{re.sub(r'[^a-zA-Z0-9]+', '_', stem)[:25]}{ext}"
            reasoning = "Identified meeting agenda, minutes, and action items."
            confidence = 0.93

        # Career / Resume
        elif (group == "documents" or ext in {".txt", ".md", ".pdf", ".docx"}) and any(k in snippet for k in ["resume", "curriculum vitae", "work experience", "education:", "skills:"]):
            target_folder = "Career_and_Resume"
            new_name = f"Resume_{re.sub(r'[^a-zA-Z0-9]+', '_', stem)[:30]}{ext}"
            reasoning = "Detected professional resume and credentials."
            confidence = 0.95

        # Financial & Receipts & Invoices
        elif any(k in name.lower() for k in ["invoice", "receipt", "billing", "payment", "tax", "statement", "w2", "payroll"]) or any(k in snippet for k in ["invoice #", "billed to:", "receipt total:", "amount due:", "subtotal:", "tax:"]):
            target_folder = "Financial_and_Receipts"
            date_match = re.search(r"20\d{2}[-_]\d{2}", name) or re.search(r"20\d{2}", snippet)
            year_tag = date_match.group(0) if date_match else date_str
            clean_title = re.sub(r"[^a-zA-Z0-9]+", "_", stem.split(".")[0]).strip("_")
            if "invoice" in snippet or "invoice" in name.lower():
                new_name = f"Invoice_{year_tag}_{clean_title[:25]}{ext}"
                reasoning = "Identified invoice/billing tokens; formatted with standard accounting prefix."
            elif "receipt" in snippet or "receipt" in name.lower():
                new_name = f"Receipt_{year_tag}_{clean_title[:25]}{ext}"
                reasoning = "Identified payment confirmation / receipt details."
            else:
                new_name = f"Finance_{year_tag}_{clean_title[:25]}{ext}"
                reasoning = "Categorized under Financial records based on document text."
            confidence = 0.94

        # Screenshots
        elif group == "images" and any(k in name.lower() for k in ["screenshot", "screen shot", "capture", "snip"]):
            target_folder = "Screenshots"
            new_name = f"Screenshot_{date_str}_{stem[-8:]}{ext}"
            reasoning = "Grouped screen captures with clean chronological stamp."
            confidence = 0.92

        # Memes
        elif group == "images" and any(k in name.lower() for k in ["meme", "funny", "cat", "dog", "joke", "dank"]):
            target_folder = "Media_and_Memes"
            new_name = f"Meme_{re.sub(r'[^a-zA-Z0-9]+', '_', stem)[:30]}{ext}"
            reasoning = "Saved for leisure: visual content moved to Media folder."
            confidence = 0.88

        # Photos
        elif group == "images":
            target_folder = "Images_and_Photos"
            new_name = f"Image_{date_str}_{re.sub(r'[^a-zA-Z0-9]+', '_', stem)[:30]}{ext}"
            reasoning = "Image file organized by standard timestamp and descriptive stem."
            confidence = 0.85

        # Code
        elif group == "code":
            target_folder = "Developer_Code"
            clean_name = stem.replace(" ", "_").lower()
            new_name = f"{clean_name}{ext}"
            reasoning = "Identified source code file and standardized naming for developer repository."
            confidence = 0.95

        # Documents & Notes
        elif group == "documents":
            target_folder = "Documents"
            new_name = f"Doc_{re.sub(r'[^a-zA-Z0-9]+', '_', stem)[:35]}{ext}"
            reasoning = "Archived into primary Documents category."
            confidence = 0.90

        # Spreadsheets
        elif group == "spreadsheets":
            target_folder = "Data_and_Sheets"
            new_name = f"Data_{re.sub(r'[^a-zA-Z0-9]+', '_', stem)[:30]}{ext}"
            reasoning = "Structured dataset/spreadsheet cataloged under Data."
            confidence = 0.91

        # Archives
        elif group == "archives":
            target_folder = "Archives_and_Zips"
            new_name = f"Archive_{stem.replace(' ', '_')[:30]}{ext}"
            reasoning = "Compressed bundle filed into Archives."
            confidence = 0.92
        elif group == "installers":
            target_folder = "Installers_and_Setups"
            new_name = f"Setup_{stem.replace(' ', '_')[:30]}{ext}"
            reasoning = "Installer executable moved to dedicated Setups location."
            confidence = 0.93

        else:
            clean_name = re.sub(r"[^\w\-.]", "_", name)
            new_name = clean_name
            target_folder = "Unsorted_Archive"
            reasoning = "Generic file filed under Unsorted Archive with sanitized filename."
            confidence = 0.75

        return {
            "new_name": new_name,
            "target_folder": target_folder,
            "reasoning": reasoning,
            "confidence": confidence,
            "provider": "Built-in Heuristic AI (Offline)"
        }

    def _sanitize_classification(self, parsed: Dict[str, Any], file_info: Dict[str, Any], provider_name: str) -> Dict[str, Any]:
        """Ensures the LLM output is valid, safe, and retains extension."""
        ext = file_info.get("ext", "")
        new_name = parsed.get("new_name", file_info.get("name", "unnamed"))
        target_folder = parsed.get("target_folder", "General")
        reasoning = parsed.get("reasoning", "Organized by AI analysis.")
        confidence = float(parsed.get("confidence", 0.9))

        new_name = re.sub(r'[\\/*?:"<>|]', "", new_name).strip()
        if not new_name.lower().endswith(ext.lower()):
            new_name += ext

        target_folder = re.sub(r'[\\/*?:"<>|]', "", target_folder).strip()
        if not target_folder:
            target_folder = "General"

        return {
            "new_name": new_name,
            "target_folder": target_folder,
            "reasoning": reasoning,
            "confidence": confidence,
            "provider": provider_name
        }

    def scan_directory(self, folder_path: str, inspect_callback=None) -> List[Dict[str, Any]]:
        """Scans a directory for non-hidden files and runs AI classification."""
        from file_inspector import FileInspector

        target_dir = Path(folder_path).resolve()
        if not target_dir.exists() or not target_dir.is_dir():
            raise ValueError(f"Directory not found: {folder_path}")

        plans = []
        for entry in os.scandir(target_dir):
            if entry.is_file() and not entry.name.startswith("."):
                file_info = FileInspector.inspect(entry.path)
                classification = self.classify_file(file_info)

                target_folder = classification["target_folder"]
                new_name = classification["new_name"]
                dest_dir = target_dir / target_folder
                dest_path = dest_dir / new_name

                counter = 1
                while dest_path.exists() and dest_path != Path(entry.path):
                    stem = Path(new_name).stem
                    ext = Path(new_name).suffix
                    new_name = f"{stem}_{counter}{ext}"
                    dest_path = dest_dir / new_name
                    counter += 1

                plan_item = {
                    "source_path": entry.path,
                    "original_name": entry.name,
                    "target_folder": target_folder,
                    "new_name": new_name,
                    "dest_path": str(dest_path),
                    "size_readable": file_info["size_readable"],
                    "group": file_info["group"],
                    "reasoning": classification["reasoning"],
                    "confidence": classification["confidence"],
                    "provider": classification.get("provider", "Unknown"),
                    "status": "pending"
                }
                plans.append(plan_item)
                if inspect_callback:
                    inspect_callback(plan_item)

        return plans

    def execute_sort(self, plans: List[Dict[str, Any]], folder_path: str) -> Dict[str, Any]:
        """Executes file moves atomically and logs history for 100% reliable Undo."""
        target_dir = Path(folder_path).resolve()
        history_path = target_dir / self.HISTORY_FILE

        history = []
        if history_path.exists():
            try:
                with open(history_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []

        batch_record = {
            "batch_id": f"batch_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "operations": []
        }

        moved_count = 0
        errors = []

        for item in plans:
            src = Path(item["source_path"])
            dest = Path(item["dest_path"])

            if not src.exists():
                errors.append(f"Source missing: {src.name}")
                continue

            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dest))
                batch_record["operations"].append({
                    "original_path": str(src),
                    "sorted_path": str(dest)
                })
                moved_count += 1
            except Exception as e:
                errors.append(f"Failed to move {src.name}: {str(e)}")

        if batch_record["operations"]:
            history.append(batch_record)
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)

        return {
            "success": True,
            "moved_count": moved_count,
            "errors": errors,
            "batch_id": batch_record["batch_id"]
        }

    def rollback_last_sort(self, folder_path: str) -> Dict[str, Any]:
        """Restores the most recent sort batch back to its original layout and names."""
        target_dir = Path(folder_path).resolve()
        history_path = target_dir / self.HISTORY_FILE

        if not history_path.exists():
            return {"success": False, "message": "No sort history found to undo."}

        try:
            with open(history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception as e:
            return {"success": False, "message": f"Error reading history: {str(e)}"}

        if not history:
            return {"success": False, "message": "Sort history is empty."}

        last_batch = history.pop()
        restored_count = 0
        errors = []

        for op in reversed(last_batch.get("operations", [])):
            sorted_path = Path(op["sorted_path"])
            orig_path = Path(op["original_path"])

            if not sorted_path.exists():
                errors.append(f"Cannot restore {sorted_path.name}: file not found.")
                continue

            try:
                orig_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(sorted_path), str(orig_path))
                restored_count += 1

                parent_dir = sorted_path.parent
                if parent_dir != target_dir and not any(parent_dir.iterdir()):
                    try:
                        parent_dir.rmdir()
                    except Exception:
                        pass
            except Exception as e:
                errors.append(f"Failed to restore {sorted_path.name}: {str(e)}")

        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

        return {
            "success": True,
            "restored_count": restored_count,
            "remaining_batches": len(history),
            "errors": errors
        }
