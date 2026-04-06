"""Run from project root: PYTHONPATH=. python scripts/verify_env.py"""

import sys
from pathlib import Path

# Ensure project root is on the path when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.config import Config

missing = Config.validate_phase_a()
if missing:
    print(f"❌ Missing: {missing}")
else:
    print("✅ All Phase A env vars are set")
