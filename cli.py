"""
SlothSort CLI: Terminal Interface for Lazy Developers
"""

import sys
import os
import argparse
from pathlib import Path

# Force UTF-8 on Windows terminal to support emojis & special symbols
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
from sloth_engine import SlothEngine

console = Console(legacy_windows=False)

def run_cli():
    parser = argparse.ArgumentParser(description="SlothSort: Zero-effort local file tidier")
    parser.add_argument("--folder", type=str, default="./demo_messy_folder", help="Target messy folder")
    parser.add_argument("--execute", action="store_true", help="Execute the moves (default is dry-run preview)")
    parser.add_argument("--undo", action="store_true", help="Rollback the last sort batch")
    parser.add_argument("--provider", type=str, default="auto", choices=["auto", "ollama", "gemini", "groq", "builtin"])
    parser.add_argument("--create-demo", action="store_true", help="Populate demo messy folder first")
    args = parser.parse_args()

    console.print(Panel.fit(
        "[bold green]SlothSort[/bold green] - [italic]Slow and Steady AI File Tidier[/italic]\n"
        "[dim]Hacktoberfest Open-Source AI Challenge (International Sloth Day)[/dim]",
        border_style="green"
    ))

    target_path = Path(args.folder).resolve()

    if args.create_demo:
        from generate_demo_files import create_sample_files
        created = create_sample_files(str(target_path))
        console.print(f"[bold cyan]Generated {len(created)} messy test files in:[/bold cyan] {target_path}")

    engine = SlothEngine(provider=args.provider)

    if args.undo:
        console.print(f"[yellow]Undoing last sort in:[/yellow] {target_path}")
        res = engine.rollback_last_sort(str(target_path))
        if res.get("success"):
            console.print(f"[bold green]Successfully restored {res['restored_count']} files back to original positions![/bold green]")
        else:
            console.print(f"[bold red]Undo failed:[/bold red] {res.get('message')}")
        return

    if not target_path.exists():
        console.print(f"[bold red]Folder does not exist:[/bold red] {target_path}")
        return

    console.print(f"[cyan]Scanning folder:[/cyan] {target_path}")
    console.print(f"[dim]AI Provider: {engine.provider}[/dim]\n")

    plans = engine.scan_directory(str(target_path))

    if not plans:
        console.print("[bold yellow]No unorganized files found in target folder.[/bold yellow]")
        return

    table = Table(title=f"SlothSort Proposed Actions ({len(plans)} files)")
    table.add_column("Original File", style="white")
    table.add_column("Target Folder", style="magenta")
    table.add_column("Clean Semantic Name", style="green")
    table.add_column("AI Reasoning", style="dim")
    table.add_column("Confidence", justify="right", style="cyan")

    for p in plans:
        table.add_row(
            p["original_name"],
            p["target_folder"],
            p["new_name"],
            p["reasoning"][:45] + "...",
            f"{int(p['confidence'] * 100)}%"
        )

    console.print(table)

    if args.execute:
        console.print("\n[bold green]Moving files like a sloth...[/bold green]")
        res = engine.execute_sort(plans, str(target_path))
        console.print(f"[bold green]Successfully tidied {res['moved_count']} files![/bold green]")
        console.print("[dim]Tip: Run with --undo anytime to restore all files back.[/dim]")
    else:
        console.print("\n[bold yellow]Preview Mode complete.[/bold yellow] Pass [bold]--execute[/bold] to apply changes.")

if __name__ == "__main__":
    run_cli()
