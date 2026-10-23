"""
SlothSort Background Watcher Agent
Uses 'watchdog' to run as an autonomous background daemon.
Observes folders (like Downloads or Desktop) and tidies incoming clutter lazily.
"""

import time
import os
import argparse
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from sloth_engine import SlothEngine
from file_inspector import FileInspector

IGNORED_EXTENSIONS = {".crdownload", ".tmp", ".part", ".download", ".lock", ".swp"}

class SlothFolderHandler(FileSystemEventHandler):
    def __init__(self, engine: SlothEngine, folder: str, auto_apply: bool = False):
        super().__init__()
        self.engine = engine
        self.folder = Path(folder).resolve()
        self.auto_apply = auto_apply

    def on_created(self, event):
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.name.startswith(".") or file_path.suffix.lower() in IGNORED_EXTENSIONS:
            return

        time.sleep(1.5)
        if not file_path.exists():
            return

        print(f"\n[SlothWatcher] Detected incoming file: {file_path.name}")
        info = FileInspector.inspect(str(file_path))
        plan = self.engine.classify_file(info)

        print(f"  Proposed Category: {plan['target_folder']}")
        print(f"  Proposed Name:     {plan['new_name']}")
        print(f"  AI Reason:         {plan['reasoning']}")

        if self.auto_apply:
            dest_dir = self.folder / plan["target_folder"]
            dest_path = dest_dir / plan["new_name"]
            single_plan = [{
                "source_path": str(file_path),
                "original_name": file_path.name,
                "target_folder": plan["target_folder"],
                "new_name": plan["new_name"],
                "dest_path": str(dest_path),
                "reasoning": plan["reasoning"]
            }]
            res = self.engine.execute_sort(single_plan, str(self.folder))
            if res.get("success"):
                print(f"  [Auto-Sorted] Moved to: {plan['target_folder']}/{plan['new_name']}")
            else:
                print(f"  [Error] {res.get('errors')}")

def start_watching(folder_path: str, auto_apply: bool = False, provider: str = "auto"):
    target_dir = Path(folder_path).resolve()
    if not target_dir.exists():
        print(f"Error: Folder does not exist: {target_dir}")
        return

    engine = SlothEngine(provider=provider)
    event_handler = SlothFolderHandler(engine, str(target_dir), auto_apply=auto_apply)
    observer = Observer()
    observer.schedule(event_handler, str(target_dir), recursive=False)
    observer.start()

    print(f"""
=====================================================
  SlothSort Background Watcher Active!
  Folder:      {target_dir}
  Auto-Apply:  {auto_apply}
  AI Provider: {engine.provider}
  Theme:       Slow and Steady (Conserve your energy)
=====================================================
Press Ctrl+C to stop the watcher.
""")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n[SlothWatcher] Sloth is resting now. Goodnight!")
    observer.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SlothSort Background Watcher")
    parser.add_argument("--folder", type=str, default="./demo_messy_folder", help="Folder to observe")
    parser.add_argument("--auto", action="store_true", help="Automatically move files without manual confirmation")
    parser.add_argument("--provider", type=str, default="auto", choices=["auto", "ollama", "gemini", "groq", "builtin"])
    args = parser.parse_args()

    start_watching(args.folder, auto_apply=args.auto, provider=args.provider)
