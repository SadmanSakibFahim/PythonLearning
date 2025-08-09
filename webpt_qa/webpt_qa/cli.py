from __future__ import annotations

import argparse
import os
from typing import List, Optional

from rich import print as rprint

from .config import load_config
from .driver import create_driver, ensure_logged_in
from .capture import capture_patient


def _read_patient_ids(args: argparse.Namespace) -> List[str]:
    ids: List[str] = []
    if args.patient_ids:
        ids.extend([str(x) for x in args.patient_ids])
    if args.patient_id_file:
        with open(args.patient_id_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    ids.append(line)
    if not ids:
        raise SystemExit("No patient IDs provided. Use --patient-ids or --patient-id-file")
    return ids


def cmd_capture(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    driver = create_driver(config)
    try:
        ensure_logged_in(driver, config)
        ids = _read_patient_ids(args)
        page_keys = args.pages.split(",") if args.pages else None
        for pid in ids:
            rprint(f"[bold green]Capturing patient[/bold green] {pid} ...")
            capture_patient(driver, config, pid, output_dir, page_keys)
        rprint("[bold green]Done[/bold green]")
    finally:
        driver.quit()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="webpt_qa")
    sub = parser.add_subparsers(dest="command", required=True)

    p_cap = sub.add_parser("capture", help="Capture screenshots for patient fields")
    p_cap.add_argument("--config", required=True, help="Path to YAML config file")
    p_cap.add_argument("--output-dir", required=True, help="Directory to save screenshots")
    p_cap.add_argument("--patient-ids", nargs="*", help="One or more patient IDs")
    p_cap.add_argument("--patient-id-file", help="File path with one patient ID per line")
    p_cap.add_argument("--pages", help="Comma-separated list of page keys to capture; defaults to all")
    p_cap.set_defaults(func=cmd_capture)

    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()