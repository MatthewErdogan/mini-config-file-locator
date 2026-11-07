import os
import tempfile
import unittest

from mini_config_file_locator import find_config, find_config_in


class TestFindConfigIn(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.addCleanup(self._tmp.cleanup)

    def _mkdir(self, relpath):
        path = os.path.join(self.root, relpath)
        os.makedirs(path, exist_ok=True)
        return path

    def _touch(self, relpath, content=""):
        path = os.path.join(self.root, relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        return path

    def test_finds_file_in_start_directory(self):
        self._touch("a.cfg")
        found = find_config_in(self.root, "a.cfg")
        self.assertEqual(found, os.path.join(self.root, "a.cfg"))

    def test_finds_file_in_nearest_ancestor(self):
        self._touch("a.cfg", "root")
        deep = self._mkdir("one/two/three")
        found = find_config_in(deep, "a.cfg")
        self.assertEqual(found, os.path.join(self.root, "a.cfg"))

    def test_nearest_wins_over_farther_ancestor(self):
        self._touch("a.cfg", "root")
        mid = self._mkdir("one/two")
        self._touch("one/a.cfg", "mid")
        found = find_config_in(mid, "a.cfg")
        self.assertEqual(found, os.path.join(self.root, "one", "a.cfg"))

    def test_returns_none_when_absent(self):
        deep = self._mkdir("one/two")
        self.assertIsNone(find_config_in(deep, "missing.cfg"))

    def test_start_path_may_be_a_file(self):
        self._touch("a.cfg")
        script = self._touch("one/two/script.py")
        found = find_config_in(script, "a.cfg")
        self.assertEqual(found, os.path.join(self.root, "a.cfg"))

    def test_relative_start_path_is_resolved(self):
        self._touch("a.cfg")
        deep = self._mkdir("one/two")
        old_cwd = os.getcwd()
        os.chdir(self.root)
        try:
            found = find_config_in(os.path.join("one", "two"), "a.cfg")
        finally:
            os.chdir(old_cwd)
        self.assertEqual(found, os.path.join(self.root, "a.cfg"))
        # sanity: the deep dir really is where we said it was
        self.assertTrue(os.path.isdir(deep))

    def test_directory_with_matching_name_is_not_a_match(self):
        self._mkdir("a.cfg")
        deep = self._mkdir("one/two")
        self.assertIsNone(find_config_in(deep, "a.cfg"))

    def test_empty_name_is_rejected(self):
        with self.assertRaises(ValueError):
            find_config_in(self.root, "")

    def test_name_with_separator_is_rejected(self):
        with self.assertRaises(ValueError):
            find_config_in(self.root, os.path.join("sub", "a.cfg"))


class TestFindConfig(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        self.addCleanup(self._tmp.cleanup)

    def test_defaults_to_current_working_directory(self):
        target = os.path.join(self.root, "a.cfg")
        with open(target, "w", encoding="utf-8") as handle:
            handle.write("")
        old_cwd = os.getcwd()
        os.chdir(self.root)
        try:
            found = find_config("a.cfg")
        finally:
            os.chdir(old_cwd)
        self.assertEqual(found, target)

    def test_explicit_none_matches_default(self):
        target = os.path.join(self.root, "a.cfg")
        with open(target, "w", encoding="utf-8") as handle:
            handle.write("")
        old_cwd = os.getcwd()
        os.chdir(self.root)
        try:
            self.assertEqual(find_config("a.cfg", None), find_config("a.cfg", self.root))
        finally:
            os.chdir(old_cwd)

    def test_returns_none_when_missing(self):
        self.assertIsNone(find_config("definitely-not-here.cfg", self.root))


if __name__ == "__main__":
    unittest.main()
