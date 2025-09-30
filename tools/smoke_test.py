"""Basic smoke test to verify imports and running a help message.

This file is safe to import by test runners. Running the script directly
executes the smoke check and exits with non-zero on failure.
"""
import importlib


def smoke_check():
    modules = [
        "pandas",
        "sklearn",
        "psutil",
        "joblib",
    ]

    failed = []
    for m in modules:
        try:
            importlib.import_module(m)
        except Exception as e:
            failed.append((m, str(e)))

    if failed:
        print("Smoke test failed: could not import:")
        for m, err in failed:
            print(f" - {m}: {err}")
        return False

    print("Smoke test passed: imports ok")
    return True


if __name__ == "__main__":
    ok = smoke_check()
    import sys
    sys.exit(0 if ok else 2)
