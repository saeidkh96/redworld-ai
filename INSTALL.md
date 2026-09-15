# Apply RedWorld AI v1.3.0 package

This is an overlay package for the released v1.2.4 repository. It intentionally does not include the v1.2.4 viewer, optimized ledger, social graph, or geography files, so those released optimizations remain untouched.

1. Back up or commit the clean v1.2.4 tree.
2. Copy/extract this package into the repository root and overwrite matching files.
3. From the repository root run `powershell -ExecutionPolicy Bypass -File .\APPLY_V130.ps1`.
4. Run the validation commands printed by the script.
5. Do not tag until all local checks pass.
