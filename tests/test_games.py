"""Automated test suite verifying game script memory safety and syntax."""

import unittest
from pathlib import Path
from numworks.deploy import run_all_checks, check_syntax, check_size, check_allocations


class TestGames(unittest.TestCase):
    """Verify all games in games/ pass syntax and size checks."""

    @classmethod
    def setUpClass(cls):
        cls.games_dir = Path(__file__).parent.parent / "games"

    def test_maties_memory_safety(self):
        """Verify maties.py has zero hot-loop allocations and fits heap limits."""
        path = self.games_dir / "maties.py"
        self.assertTrue(path.exists(), "maties.py must exist")

        source = path.read_text(encoding="utf-8")
        checks = run_all_checks(source, filename=str(path))

        for check in checks:
            with self.subTest(check=check.name):
                self.assertTrue(
                    check.passed,
                    f"{check.name} failed: {check.message}\n" + "\n".join(check.details)
                )

    def test_all_games_syntax(self):
        """Verify all .py files in games/ have valid Python syntax."""
        for py_file in self.games_dir.glob("*.py"):
            with self.subTest(file=py_file.name):
                source = py_file.read_text(encoding="utf-8")
                res = check_syntax(source, filename=str(py_file))
                self.assertTrue(res.passed, f"{py_file.name} syntax error: {res.message}")

    def test_all_games_size(self):
        """Verify all .py files in games/ fit within the 32KB hard storage limit."""
        for py_file in self.games_dir.glob("*.py"):
            with self.subTest(file=py_file.name):
                source = py_file.read_text(encoding="utf-8")
                res = check_size(source)
                self.assertTrue(res.passed, f"{py_file.name} exceeds size limit: {res.message}")


if __name__ == "__main__":
    unittest.main()
