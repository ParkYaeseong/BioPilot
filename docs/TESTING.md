# Tests and offline verification

Run from the repository root in an environment with the development/checker dependencies:

```powershell
.venv/Scripts/python.exe -m pytest tests tests_app -q -rs -p no:cacheprovider
.venv/Scripts/python.exe checks/validate_package.py
.venv/Scripts/python.exe checks/check_reproduction.py
```

The tests and package checker verify code, scientific contracts, source isolation and
record consistency. The reproduction check renders five saved-review views, checks
19 candidates and local input guards, and confirms that execution is disabled without
configuration. These checks do not dispatch provider requests or GPU jobs. They do not
verify browser WebGL rendering or biological efficacy.

## Optional local checksums

```powershell
.venv/Scripts/python.exe checks/update_manifest.py
.venv/Scripts/python.exe checks/validate_package.py
```

The first command generates an ignored local `MANIFEST.sha256`; the checker verifies
it when present. The application and a fresh Git checkout do not require that file.
Regenerate it after source edits if you choose to use it.

Scientific execution and reproduction receipts remain in [validation](../validation/README.md).
Generated logs, recordings, personal submission drafts, local instructions and planning
material stay outside the published source inventory.
