import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline_observe.models.pipeline_definition_schemas import PipelineIn
from pipeline_observe.collector.pipeline_definition_service import (
    create_pipeline_definition,
)

p = Path(__file__).resolve().parents[1] / "payload.json"
print("Loading", p)
raw = json.loads(p.read_text())
try:
    model = PipelineIn.model_validate(raw)
    print("Validation OK: ", model)
except Exception as e:
    print("Validation ERROR:", repr(e))
    raise

try:
    created = create_pipeline_definition(model)
    print("Created:", created)
except Exception as e:
    print("Create ERROR:", repr(e))
    raise
