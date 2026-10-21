"""Pruebas básicas de identidad del proyecto."""

from __future__ import annotations

import unittest


class ProjectTests(unittest.TestCase):
    def test_project_name(self):
        self.assertIn("Democracia", "Modo Democracia")

    def test_steam_app_id(self):
        self.assertTrue("553850".isdigit())


if __name__ == "__main__":
    unittest.main()
