from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY))

from install import install


class InstallerTests(unittest.TestCase):
    def test_installs_both_skills_to_selected_home(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            installed = install("copilot", home, REPOSITORY)
            destination = home / ".agents" / "skills"
            self.assertEqual(installed, [destination / "itr", destination / "itr2"])
            self.assertTrue((destination / "itr" / "SKILL.md").is_file())
            self.assertTrue((destination / "itr2" / "SKILL.md").is_file())
            self.assertTrue((destination / "itr2" / "scripts" / "build_return.py").is_file())
            self.assertFalse(any(destination.rglob("*.pyc")))
            self.assertFalse(any(path.name == "__pycache__" for path in destination.rglob("*")))


if __name__ == "__main__":
    unittest.main()
