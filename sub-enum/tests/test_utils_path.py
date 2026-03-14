import os
import tempfile
import unittest

from src.sub_enum.utils import ensure_path_context


class TestUtilsPath(unittest.TestCase):
    def test_ensure_path_context_adds_expected_bins(self):
        # Use a temporary HOME to control the expected bin paths
        with tempfile.TemporaryDirectory() as tmp_home:
            old_home = os.environ.get("HOME")
            old_path = os.environ.get("PATH", "")
            try:
                os.environ["HOME"] = tmp_home
                # Reset PATH to a known value
                os.environ["PATH"] = ""
                ensure_path_context()
                new_path = os.environ.get("PATH", "")
                # The .sub-enum/bin should be present
                assert os.path.join(tmp_home, ".sub-enum", "bin") in new_path
            finally:
                if old_home is not None:
                    os.environ["HOME"] = old_home
                os.environ["PATH"] = old_path


if __name__ == '__main__':
    unittest.main()
