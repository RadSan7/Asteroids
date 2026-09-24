"""Child process entry: build one asset. Usage: python3 -m forge.run_asset <theme> <asset>"""
import importlib
import json
import os
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import bpy  # noqa: E402,F401  (bpy must load before bmesh users)

from forge import pipeline  # noqa: E402


def main():
    theme, name = sys.argv[1], sys.argv[2]
    importlib.import_module(f"themes.{theme}")
    try:
        meta = pipeline.run(theme, name, os.path.join(ROOT, "library"),
                            os.environ.get("FORGE_WORKROOT", "/tmp/forge_work"))
    except Exception as e:  # report compactly to the queue
        tb = traceback.format_exc().strip().splitlines()
        print("FORGE_ERROR " + json.dumps(dict(error=f"{type(e).__name__}: {e}", tail=tb[-12:])))
        sys.exit(1)
    print("FORGE_RESULT " + json.dumps(meta))


if __name__ == "__main__":
    main()
