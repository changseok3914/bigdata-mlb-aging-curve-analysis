"""
Generate analysis figures.

This script currently delegates to src/analyze/run_analysis.py,
which contains the visualization code converted from the original notebook.
"""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[2]
runpy.run_path(str(ROOT / "src" / "analyze" / "run_analysis.py"), run_name="__main__")
