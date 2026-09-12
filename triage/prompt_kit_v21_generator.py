"""Self-service materializer and launcher for AI Harness Prompt Kit V21.

It loads the packaged zip implementation from base64, adds it to sys.path
via zipimport, and executes the V21 generator.
"""
from __future__ import annotations

import argparse
import base64
import sys
import tempfile
import zipimport
from pathlib import Path

# Load implementation payload and run
def get_payload_path() -> Path:
    return Path(__file__).parent / "prompt_kit_v21_impl.parts" / "payload.b64"


def generate_v21(v20_bundle_path: Path, output_dir: Path) -> None:
    payload_path = get_payload_path()
    if not payload_path.exists():
        raise FileNotFoundError(f"Implementation payload not found at: {payload_path}")

    # Read base64 payload
    with open(payload_path, "rb") as f:
        b64_data = f.read()
    zip_bytes = base64.b64decode(b64_data)

    # Materialize into temporary zipimport file
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
        tmp_file.write(zip_bytes)
        tmp_zip_path = Path(tmp_file.name)

    try:
        # Load module via zipimport
        importer = zipimport.zipimporter(str(tmp_zip_path))
        impl = importer.load_module("prompt_kit_v21_impl")
        # Run the generator implementation
        impl.generate(v20_bundle_path, output_dir, tmp_zip_path)
    finally:
        # Cleanup temporary zip
        try:
            tmp_zip_path.unlink()
        except OSError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic V21 Self-Service Generator")
    parser.add_argument(
        "--source-bundle",
        required=True,
        help="Path to the authoritative AI Harness Prompt Kit V20 bundle ZIP file",
    )
    parser.add_argument(
        "--out-dir",
        default="Outputs",
        help="Directory where generated V21 files will be written",
    )
    args = parser.parse_args()

    try:
        generate_v21(Path(args.source_bundle), Path(args.out_dir))
        return 0
    except Exception as e:
        print(f"Error during V21 generation: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
