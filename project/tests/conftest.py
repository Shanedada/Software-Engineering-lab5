import sys
import os

# Ensure repository root is on sys.path so `import project.*` works when running pytest from workspace root
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
