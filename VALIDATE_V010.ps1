$ErrorActionPreference = "Stop"

Write-Host "Validating RedWorld AI v0.1.0..."
python -m pytest
python -m ruff check .
python -m mypy src

Write-Host "Running 50-tick closed-economy invariant check..."
$env:PYTHONPATH = "src"
python -c "from redworld.simulation.factory import create_genesis_world; from redworld.simulation.engine import SimulationEngine; w=create_genesis_world('Validation'); SimulationEngine(w).run(50); assert w.ledger.trial_balance_delta().is_zero(); print({'tick': w.tick, 'entries': w.ledger.audit_entry_count(), 'events': len(w.events.events), 'balanced': True})"

Write-Host "RedWorld AI v0.1.0 validation complete."
