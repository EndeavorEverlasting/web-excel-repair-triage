#!/usr/bin/env python3
"""Bounded Tk GUI for registered Prompt Kit generators."""
from __future__ import annotations

import json
import sys
import threading
import webbrowser
from pathlib import Path
from tkinter import BooleanVar, END, StringVar, Tk, filedialog, messagebox
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_prompt_kit_registry  # noqa: E402

MANIFEST_PATH = REPO_ROOT / "configs" / "prompt_kit" / "generators.v1.json"
ALLOWED_RUNNER = "scripts/build_prompt_kit_registry.py"


class GeneratorApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Prompt Kit Generator")
        self.root.minsize(720, 500)
        self.manifest = self._load_manifest()
        self.generators = {
            item["display_name"]: item for item in self.manifest["generators"]
        }
        self.generator_name = StringVar()
        self.output_path = StringVar()
        self.validate_after_build = BooleanVar(value=True)
        self.open_after_build = BooleanVar(value=True)
        self.status = StringVar(value="Ready")
        self._build_ui()
        default_id = self.manifest["default_generator_id"]
        default = next(item for item in self.manifest["generators"] if item["id"] == default_id)
        self.generator_name.set(default["display_name"])
        self._apply_generator_defaults()

    def _load_manifest(self) -> dict:
        try:
            payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"Cannot load generator manifest {MANIFEST_PATH}: {exc}") from exc
        if payload.get("schema_version") != "prompt-kit-generators/v1":
            raise SystemExit("Unsupported Prompt Kit generator manifest schema")
        generators = payload.get("generators")
        if not isinstance(generators, list) or not generators:
            raise SystemExit("Generator manifest contains no generators")
        for generator in generators:
            if generator.get("runner") != ALLOWED_RUNNER:
                raise SystemExit(f"Unapproved generator runner: {generator.get('runner')}")
        return payload

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Generator").grid(row=0, column=0, sticky="w", pady=6)
        combo = ttk.Combobox(
            frame,
            textvariable=self.generator_name,
            values=list(self.generators),
            state="readonly",
            width=48,
        )
        combo.grid(row=0, column=1, columnspan=2, sticky="ew", pady=6)
        combo.bind("<<ComboboxSelected>>", lambda _event: self._apply_generator_defaults())
        ttk.Label(frame, text="Output HTML").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(frame, textvariable=self.output_path).grid(row=1, column=1, sticky="ew", pady=6)
        ttk.Button(frame, text="Browse...", command=self._browse_output).grid(
            row=1, column=2, padx=(8, 0), pady=6
        )
        ttk.Checkbutton(
            frame,
            text="Validate exact generated output after build",
            variable=self.validate_after_build,
        ).grid(row=2, column=1, columnspan=2, sticky="w", pady=4)
        ttk.Checkbutton(
            frame,
            text="Open website after build",
            variable=self.open_after_build,
        ).grid(row=3, column=1, columnspan=2, sticky="w", pady=4)
        button_row = ttk.Frame(frame)
        button_row.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(14, 8))
        self.run_button = ttk.Button(button_row, text="Build", command=self._start_build)
        self.run_button.pack(side="left")
        ttk.Button(button_row, text="Open output folder", command=self._open_output_folder).pack(
            side="left", padx=8
        )
        ttk.Label(button_row, textvariable=self.status).pack(side="right")
        self.log = ScrolledText(frame, height=18, wrap="word", state="disabled")
        self.log.grid(row=5, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(5, weight=1)

    def _selected_generator(self) -> dict:
        return self.generators[self.generator_name.get()]

    def _apply_generator_defaults(self) -> None:
        selected = self._selected_generator()
        self.output_path.set(str(REPO_ROOT / selected["default_output"]))
        defaults = {item["id"]: item.get("default") for item in selected["options"]}
        self.validate_after_build.set(bool(defaults.get("validate_after_build", True)))
        self.open_after_build.set(bool(defaults.get("open_after_build", True)))

    def _browse_output(self) -> None:
        current = Path(self.output_path.get()).expanduser()
        filename = filedialog.asksaveasfilename(
            title="Choose generated Prompt Kit website",
            initialdir=str(current.parent if current.parent.exists() else REPO_ROOT),
            initialfile=current.name or "index.html",
            defaultextension=".html",
            filetypes=(("HTML files", "*.html"), ("All files", "*.*")),
        )
        if filename:
            self.output_path.set(filename)

    def _append_log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert(END, text.rstrip() + "\n")
        self.log.see(END)
        self.log.configure(state="disabled")

    def _start_build(self) -> None:
        output = Path(self.output_path.get()).expanduser().resolve()
        if output.suffix.lower() not in {".html", ".htm"}:
            messagebox.showerror("Invalid output", "Choose an .html or .htm output file.")
            return
        self.run_button.configure(state="disabled")
        self.status.set("Building...")
        self._append_log(f"Building {self._selected_generator()['display_name']} -> {output}")
        threading.Thread(target=self._run_build, args=(output,), daemon=True).start()

    def _run_build(self, output: Path) -> None:
        returncode = 0
        message = ""
        try:
            html = build_prompt_kit_registry.build(output)
            if self.validate_after_build.get():
                actual = output.read_text(encoding="utf-8")
                if actual != html:
                    raise RuntimeError("Generated output does not match the in-memory build")
            message = f"Built {output} ({len(html)} bytes)."
        except Exception as exc:  # GUI boundary: report and preserve the exception text.
            returncode = 1
            message = f"Build failed: {exc}"
        self.root.after(0, self._finish_build, returncode, output, message)

    def _finish_build(self, returncode: int, output: Path, message: str) -> None:
        self.run_button.configure(state="normal")
        self._append_log(message)
        if returncode:
            self.status.set("Failed")
            messagebox.showerror("Build failed", "See the generator log for details.")
            return
        self.status.set("Completed")
        if self.open_after_build.get():
            webbrowser.open(output.as_uri())

    def _open_output_folder(self) -> None:
        folder = Path(self.output_path.get()).expanduser().resolve().parent
        webbrowser.open(folder.as_uri())


def main() -> int:
    root = Tk()
    GeneratorApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
