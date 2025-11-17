#!/bin/bash
# Generate Python Protocol Buffer bindings

cd "$(dirname "$0")/.." || exit 1
python scripts/generate_proto.py
