#!/usr/bin/env python3
"""Generate Python bindings from Protocol Buffer definitions"""
import subprocess
import sys
from pathlib import Path


def main():
    """Generate Python protobuf bindings"""
    # Get project root
    script_dir = Path(__file__).parent
    agents_dir = script_dir.parent
    proto_dir = agents_dir / "proto"
    output_dir = agents_dir / "src" / "messaging" / "generated"

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create __init__.py
    init_file = output_dir / "__init__.py"
    init_file.write_text('"""Generated Protocol Buffer messages"""\n')

    # Generate Python code
    proto_file = proto_dir / "messages.proto"
    
    if not proto_file.exists():
        print(f"Error: Proto file not found: {proto_file}", file=sys.stderr)
        sys.exit(1)

    print(f"Generating Python bindings from {proto_file}...")
    
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "grpc_tools.protoc",
                f"--proto_path={proto_dir}",
                f"--python_out={output_dir}",
                f"--pyi_out={output_dir}",
                str(proto_file),
            ],
            check=True,
        )
        print(f"Successfully generated Python bindings in {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Error generating Python bindings: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
