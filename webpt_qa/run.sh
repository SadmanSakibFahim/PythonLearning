#!/usr/bin/env bash
set -euo pipefail

# Example runner. Update paths accordingly.

python -m webpt_qa.cli capture \
  --config /workspace/webpt_qa/config.sample.yaml \
  --output-dir /workspace/webpt_qa/output \
  --patient-ids 12345 \
  --pages patient_profile,scheduler