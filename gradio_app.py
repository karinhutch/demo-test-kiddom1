import os
from pathlib import Path
from datetime import datetime
import re
import gradio as gr

UPLOADS_DIR = Path("/workspace/uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
STANDARDS_PATH = Path("/workspace/standards/standards.pdf")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def _sanitize_filename(filename: str) -> str:
    base, ext = os.path.splitext(filename)
    safe_base = re.sub(r"[^A-Za-z0-9._-]", "_", base).strip("._-") or "file"
    return f"{safe_base}{ext.lower()}"


def _timestamp_name(name: str) -> str:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
    return f"{ts}__{name}"


def save_files(files):
    if not files:
        return list_gallery()
    saved = []
    for f in files:
        # Gradio may pass dicts with 'name' and 'path' or just a str path
        if isinstance(f, dict):
            src_path = f.get("path") or f.get("name")
            display_name = f.get("orig_name") or f.get("name") or Path(src_path).name
        else:
            src_path = str(f)
            display_name = Path(src_path).name
        if not src_path:
            continue
        safe_name = _sanitize_filename(display_name)
        dest = UPLOADS_DIR / _timestamp_name(safe_name)
        try:
            Path(src_path).replace(dest)
        except Exception:
            # Fallback to copy bytes
            with open(src_path, "rb") as r, open(dest, "wb") as w:
                w.write(r.read())
        saved.append(str(dest))
    return list_gallery()


def list_gallery():
    files = sorted(
        [p for p in UPLOADS_DIR.glob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    # Return list of [image_path, caption]
    return [[str(p), p.name] for p in files[:60]]


def build_ui():
    with gr.Blocks(theme=gr.themes.Soft()) as demo:
        gr.Markdown("## Assessment Uploads (Gradio)\nUpload assessment question images. Files persist in `/workspace/uploads`.")
        if STANDARDS_PATH.exists():
            gr.Markdown(f"Using standards document: `{STANDARDS_PATH}`")
        else:
            gr.Markdown("⚠️ No standards document at `/workspace/standards/standards.pdf`. Upload it to use for correlations.")

        with gr.Row():
            uploader = gr.File(label="Upload images", file_types=["image"], file_count="multiple")
        with gr.Row():
            save_btn = gr.Button("Save to uploads", variant="primary")
            refresh_btn = gr.Button("Refresh gallery")
        gallery = gr.Gallery(label="Uploaded images", columns=[3], height="auto", preview=True)

        save_btn.click(fn=save_files, inputs=uploader, outputs=gallery)
        refresh_btn.click(fn=list_gallery, inputs=None, outputs=gallery)
        uploader.upload(fn=save_files, inputs=uploader, outputs=gallery)

        # Initialize gallery on load
        demo.load(fn=list_gallery, inputs=None, outputs=gallery)
    return demo


if __name__ == "__main__":
    app = build_ui()
    app.queue(concurrency_count=4).launch(server_name="0.0.0.0", server_port=7860)