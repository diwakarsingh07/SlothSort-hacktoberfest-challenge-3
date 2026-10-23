"""
SlothSort: Multi-Modal File Inspector
Inspects and extracts text, metadata, and visual context from chaotic files.
"""

import os
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional

class FileInspector:
    """Inspects files to extract structured information for the AI reasoning engine."""

    MAX_TEXT_SAMPLE = 2500

    EXT_CATEGORIES = {
        "images": {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg", ".ico"},
        "documents": {".pdf", ".docx", ".doc", ".txt", ".md", ".rtf", ".odt", ".pages"},
        "spreadsheets": {".csv", ".xlsx", ".xls", ".tsv"},
        "presentations": {".pptx", ".ppt", ".key"},
        "code": {".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".json", ".yaml", ".yml",
                 ".sql", ".rs", ".go", ".c", ".cpp", ".java", ".sh", ".ps1", ".bat", ".xml"},
        "archives": {".zip", ".tar", ".gz", ".7z", ".rar", ".bz2"},
        "installers": {".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm"},
        "media": {".mp4", ".mkv", ".mov", ".avi", ".mp3", ".wav", ".flac", ".ogg", ".m4a"}
    }

    @classmethod
    def get_file_type_group(cls, ext: str) -> str:
        ext = ext.lower()
        for cat, exts in cls.EXT_CATEGORIES.items():
            if ext in exts:
                return cat
        return "other"

    @classmethod
    def inspect(cls, file_path: str) -> Dict[str, Any]:
        """Analyzes a file and returns rich metadata and sample content for classification."""
        path = Path(file_path)
        if not path.exists():
            return {"error": "File not found", "path": file_path}

        stat = path.stat()
        ext = path.suffix.lower()
        mime_type, _ = mimetypes.guess_type(str(path))
        group = cls.get_file_type_group(ext)

        result: Dict[str, Any] = {
            "name": path.name,
            "stem": path.stem,
            "ext": ext,
            "size_bytes": stat.st_size,
            "size_readable": cls._format_size(stat.st_size),
            "modified_time": stat.st_mtime,
            "mime_type": mime_type or "application/octet-stream",
            "group": group,
            "content_snippet": "",
            "visual_hints": []
        }

        if group in {"documents", "spreadsheets", "code"} or ext in {".txt", ".md", ".json", ".csv", ".log"}:
            result["content_snippet"] = cls._read_text_content(path, ext)
        elif group == "images":
            result["visual_hints"] = cls._inspect_image_hints(path)

        return result

    @classmethod
    def _read_text_content(cls, path: Path, ext: str) -> str:
        """Safely extract readable snippet from text or document formats."""
        try:
            if ext in {".txt", ".md", ".py", ".js", ".ts", ".html", ".css", ".json", ".csv", ".yaml", ".yml", ".log", ".sql", ".sh"}:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read(cls.MAX_TEXT_SAMPLE).strip()

            if ext == ".docx":
                try:
                    import docx
                    doc = docx.Document(path)
                    text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                    return text[:cls.MAX_TEXT_SAMPLE].strip()
                except Exception:
                    pass

            if ext == ".pdf":
                try:
                    import pypdf
                    reader = pypdf.PdfReader(str(path))
                    text = ""
                    for page in reader.pages[:3]:
                        t = page.extract_text()
                        if t:
                            text += t + "\n"
                    return text[:cls.MAX_TEXT_SAMPLE].strip()
                except Exception:
                    try:
                        with open(path, "rb") as f:
                            raw = f.read(4096)
                            text_chars = "".join([chr(b) if 32 <= b <= 126 else " " for b in raw])
                            return text_chars[:500].strip()
                    except Exception:
                        pass
        except Exception as e:
            return f"[Error reading content: {str(e)}]"

        return ""

    @classmethod
    def _inspect_image_hints(cls, path: Path) -> list:
        hints = []
        name_lower = path.name.lower()
        if any(w in name_lower for w in ["screenshot", "screen shot", "capture", "snip"]):
            hints.append("likely_screenshot")
        if any(w in name_lower for w in ["receipt", "invoice", "bill"]):
            hints.append("likely_receipt_or_invoice")
        if any(w in name_lower for w in ["meme", "funny"]):
            hints.append("likely_meme")
        return hints

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
