"""Build a sanitized Device Transfer / Stock Sign-Off proof artifact."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from openpyxl import Workbook

from triage.device_transfer_signoff import run


def _write_source(path: Path, count: int) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Example Configs"
    ws.append([
        "Device Type",
        "Current Building",
        "Install Building",
        "Cybernet Hostname",
        "Cybernet Serial",
        "Neuron Hostname",
        "Neuron MAC",
        "Neuron S/N",
    ])
    for idx in range(1, count + 1):
        ws.append(["Cybernet", "STAGING", "EX", f"EX-CYB-{idx:03d}", f"CYB-SERIAL-{idx:03d}", "", "", ""])
    for idx in range(1, count + 1):
        ws.append(["Neuron", "STAGING", "EX", "", "", "", f"00AA00BB{idx:04d}", f"NEU-SERIAL-{idx:03d}"])
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="Outputs/device_transfer_signoff_example")
    parser.add_argument("--serial-count", type=int, default=25)
    args = parser.parse_args(argv)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    source = out / "example_source_configs.xlsx"
    config_path = out / "example_site_config.json"
    workbook = out / "EXAMPLE_Device_Transfer_SignOff_20260728.xlsx"

    _write_source(source, args.serial_count)
    config = {
        "artifact_family": "device_transfer_signoff",
        "site": {
            "name": "Example Hospital",
            "code": "EXAMPLE",
            "address": "100 Example Avenue, Example, NY 10000",
            "poc": "Example Receiver",
            "delivery_date": "2026-07-28",
            "delivery_time": "8:00 AM",
            "origin": "1 Marcus Ave / Staging",
            "prepared_by": "Example Coordinator",
            "signoff_id": "EXAMPLE-EDI-STOCK-20260728-001",
        },
        "source": {"sheet": None, "device_type_header": "Device Type"},
        "shipment": [
            {"item": "DIMs", "qty": 10},
            {"item": "Grey Cat5 Ethernet", "qty": 20},
            {"item": "Mice", "qty": args.serial_count},
            {"item": "Keyboards", "qty": args.serial_count},
            {"item": "Tap Badge Scanners", "qty": args.serial_count},
            {"item": "Neurons", "qty": args.serial_count, "serial_source": "Neuron", "serial_header": "Neuron S/N"},
            {"item": "Cybernets", "qty": args.serial_count, "serial_source": "Cybernet", "serial_header": "Cybernet Serial"},
        ],
    }
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    result = run(str(source), str(config_path), output=str(workbook))
    print(result.workbook)
    print(result.manifest)
    print(result.preflight)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
