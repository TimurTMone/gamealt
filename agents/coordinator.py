#!/usr/bin/env python3
"""
🎯 BabyPath Agent Coordinator
================================
Orchestrates all AI agents and generates a unified report.
This is your "command center" — run this to execute any/all agents.

Usage:
    python3 coordinator.py status                  # Check what's been generated
    python3 coordinator.py run coloring             # Run coloring agent
    python3 coordinator.py run guides               # Run guide agent
    python3 coordinator.py run all                   # Run everything
    python3 coordinator.py run coloring --theme animals --count 5
    python3 coordinator.py run guides --guide speech-delay --lang ru
    python3 coordinator.py report                   # Generate summary report
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

from config import OUTPUT_DIR, COLORING_DIR, GUIDES_DIR, BILINGUAL_DIR, REPORTS_DIR

AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))


def run_command(cmd: list, label: str) -> dict:
    """Run a command and capture output."""
    print(f"\n{'='*60}")
    print(f"  🚀 Running: {label}")
    print(f"{'='*60}\n")

    try:
        result = subprocess.run(
            cmd,
            cwd=AGENTS_DIR,
            capture_output=False,
            text=True
        )
        return {
            "agent": label,
            "status": "success" if result.returncode == 0 else "failed",
            "returncode": result.returncode,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"agent": label, "status": "error", "error": str(e)}


def check_api_keys():
    """Check which API keys are configured."""
    keys = {
        "LEONARDO_API_KEY": bool(os.getenv("LEONARDO_API_KEY")),
        "ANTHROPIC_API_KEY": bool(os.getenv("ANTHROPIC_API_KEY")),
        "HIGGSFIELD_API_KEY": bool(os.getenv("HIGGSFIELD_API_KEY")),
    }
    return keys


def get_status():
    """Get status of all generated content."""
    status = {}

    # Coloring pages
    coloring_packs = []
    if os.path.exists(COLORING_DIR):
        for d in sorted(os.listdir(COLORING_DIR)):
            pack_dir = os.path.join(COLORING_DIR, d)
            if os.path.isdir(pack_dir):
                report_file = os.path.join(pack_dir, "report.json")
                if os.path.exists(report_file):
                    with open(report_file) as f:
                        coloring_packs.append(json.load(f))
                else:
                    files = [f for f in os.listdir(pack_dir) if f.endswith(".png")]
                    coloring_packs.append({"dir": d, "pages": len(files)})
    status["coloring"] = coloring_packs

    # Guides
    guides = []
    if os.path.exists(GUIDES_DIR):
        for f in sorted(os.listdir(GUIDES_DIR)):
            if f.endswith(".html"):
                size = os.path.getsize(os.path.join(GUIDES_DIR, f))
                guides.append({"file": f, "size_kb": round(size / 1024, 1)})
    status["guides"] = guides

    # Bilingual kits
    kits = []
    if os.path.exists(BILINGUAL_DIR):
        for f in sorted(os.listdir(BILINGUAL_DIR)):
            size = os.path.getsize(os.path.join(BILINGUAL_DIR, f))
            kits.append({"file": f, "size_kb": round(size / 1024, 1)})
    status["bilingual_kits"] = kits

    return status


def print_status():
    """Print a formatted status report."""
    keys = check_api_keys()
    status = get_status()

    print("\n" + "="*60)
    print("  🎯 BABYPATH AGENT COORDINATOR — STATUS REPORT")
    print("="*60)

    # API Keys
    print("\n  📡 API Keys:")
    for key, configured in keys.items():
        icon = "✅" if configured else "❌"
        print(f"     {icon} {key}")

    # Coloring
    print(f"\n  🖍️  Coloring Pages: {len(status['coloring'])} packs")
    for pack in status["coloring"]:
        if "theme" in pack:
            print(f"     • {pack.get('name', pack['theme'])}: {pack.get('success', '?')}/{pack.get('total', '?')} pages")
        else:
            print(f"     • {pack['dir']}: {pack['pages']} pages")

    # Guides
    print(f"\n  📖 Guides: {len(status['guides'])} generated")
    for guide in status["guides"]:
        print(f"     • {guide['file']} ({guide['size_kb']} KB)")

    # Kits
    print(f"\n  🌍 Bilingual Kits: {len(status['bilingual_kits'])} files")
    for kit in status["bilingual_kits"]:
        print(f"     • {kit['file']} ({kit['size_kb']} KB)")

    # Next steps
    print(f"\n  📁 Output directory: {OUTPUT_DIR}")
    print()

    if not any(keys.values()):
        print("  ⚠️  No API keys configured! Set them:")
        print("     export LEONARDO_API_KEY='your-key'")
        print("     export ANTHROPIC_API_KEY='your-key'")
        print()


def run_agent(agent: str, extra_args: list = None):
    """Run a specific agent."""
    extra = extra_args or []

    if agent in ("coloring", "all"):
        cmd = [sys.executable, "coloring_agent.py"] + extra
        run_command(cmd, "Coloring Page Agent")

    if agent in ("guides", "all"):
        if not extra:
            extra = ["--guide", "all"]
        cmd = [sys.executable, "guide_agent.py"] + extra
        run_command(cmd, "Guide Agent")


def generate_report():
    """Generate a comprehensive report of all content."""
    status = get_status()
    keys = check_api_keys()

    report = {
        "generated_at": datetime.now().isoformat(),
        "api_keys": keys,
        "content": status,
        "summary": {
            "coloring_packs": len(status["coloring"]),
            "guides": len(status["guides"]),
            "bilingual_kits": len(status["bilingual_kits"]),
        }
    }

    report_path = os.path.join(REPORTS_DIR, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n  📋 Report saved: {report_path}")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BabyPath Agent Coordinator")
    parser.add_argument("command", nargs="?", default="status",
                        choices=["status", "run", "report"],
                        help="Command to execute")
    parser.add_argument("agent", nargs="?", help="Agent to run: coloring, guides, all")
    parser.add_argument("extra", nargs=argparse.REMAINDER, help="Extra arguments for the agent")

    args = parser.parse_args()

    if args.command == "status":
        print_status()
    elif args.command == "report":
        print_status()
        generate_report()
    elif args.command == "run":
        if not args.agent:
            print("\n  Usage: python3 coordinator.py run <coloring|guides|all> [args]")
            print("\n  Examples:")
            print("    python3 coordinator.py run coloring --theme animals --count 5")
            print("    python3 coordinator.py run guides --guide speech-delay --lang ru")
            print("    python3 coordinator.py run all")
            print()
        else:
            run_agent(args.agent, args.extra)
            print()
            generate_report()
