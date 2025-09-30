Thanks for looking at this project! A few notes to make contributing and releases smooth.

1. Code style
- Follow existing code conventions (PEP8-ish). Keep changes minimal and well-scoped.

2. Tests
- There is a basic smoke test at `tools/smoke_test.py`. Add unit tests under `tests/` and update CI if you add more.

3. Pull requests
- Branch from `main` (or `master` if you prefer). Open a PR with a clear description and include the output of `tools/smoke_test.py` where appropriate.

4. Releases
- Use `requirements-pinned.txt` to build releases. See `PUBLISH.md` for guidance.

5. Issues
- Use the issue tracker to report bugs or request features. Please include steps to reproduce and any logs from `tools/logs/` if relevant.
