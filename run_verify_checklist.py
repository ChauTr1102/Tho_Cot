"""Call the real AgentQAChecklistService.verify() function directly.

No mocking, no TestClient, no HTTP server — this imports and invokes the
exact same service object used by app/api/v1/endpoints/verify_checklist.py,
making real HTTP calls to ModelArk for both the checklist-generator stage
and every parallel per-item verifier stage.

Run with:
    backend\\venv\\Scripts\\python.exe run_verify_checklist.py
"""
import json
import logging
import os
import pathlib
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

REPO_ROOT = pathlib.Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Load ARK_API_KEY from the root .env (backend/.env doesn't define one).
root_env = REPO_ROOT / ".env"
for line in root_env.read_text(encoding="utf-8").splitlines():
    key, sep, value = line.partition("=")
    if sep:
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

print("ARK_API_KEY set:", bool(os.environ.get("ARK_API_KEY")))

from app.schemas.qa_checklist import VerifyChecklistRequest
from app.services.qa_agent import agent_qa_checklist_service

FIXTURE_PATH = REPO_ROOT / "sample_data" / "test_verify_checklist_input.json"

with open(FIXTURE_PATH, encoding="utf-8") as f:
    payload = json.load(f)
payload.pop("_comment", None)

request = VerifyChecklistRequest.model_validate(payload)

started = time.monotonic()
result = agent_qa_checklist_service.verify(request, timeout=90)
elapsed = time.monotonic() - started

output_json = result.model_dump_json(indent=2)
print(f"\nCompleted in {elapsed:.1f}s")
print("Result:")
try:
    sys.stdout.reconfigure(encoding="utf-8")
    print(output_json)
except (AttributeError, UnicodeEncodeError):
    # Fallback for terminals that can't be reconfigured to UTF-8 (rare).
    print(output_json.encode("ascii", errors="backslashreplace").decode("ascii"))

result_path = REPO_ROOT / "agent_qa_result.json"
result_path.write_text(output_json, encoding="utf-8")
print(f"\n(Full UTF-8 output written to {result_path})")
