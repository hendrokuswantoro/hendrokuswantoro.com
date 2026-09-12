"""Makes konftes.py importable from the test files.

pytest already inserts this directory on the path when the tests are not a
package, but relying on that is relying on a default. This says it out loud
so the suite runs the same way from the repository root, from inside tests/,
and from a CI runner.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
