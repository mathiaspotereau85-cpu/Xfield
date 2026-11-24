"""Pipeline xfield : texte -> voix (Chatterbox) -> image -> vidéo parlante (Muapi / Open Higgsfield)."""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

from .muapi import Muapi

DEFAULT_IMAGE_MODEL = os.environ.get("XFIELD_IMAGE_MODEL", "flux-dev-image")
DEFAULT_LIPSYNC_MODEL = os.environ.get("XFIELD_LIPSYNC_MODEL", "infinitetalk-image-to-video")


@dataclass
class Job:
    text: str
    image_prompt: str | None = None   # génère le visage/la scène
    image_path: str | None = None     # ou utilise une image existante
    language: str = "fr"
    reference_wav: str | None = None  # voix à cloner (~10 s)
    image_model: str = DEFAULT_IMAGE_MODEL
    lipsync_model: str = DEFAULT_LIPSYNC_MODEL
    out_dir: str = "outputs"
    name: str | None = None
    results: dict = field(default_factory=dict)


def slug(s: str, n: int = 40) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:n] or "clip"


def run(job: Job, voice=None, api: Muapi | None = None, log=print) -> dict:
    if not (job.image_prompt or job.image_path):
        raise ValueError("Il faut --image-prompt ou --image.")
    api = api or Muapi()
    name = job.name or f"{time.strftime('%Y%m%d-%H%M%S')}-{slug(job.text)}"
    out = Path(job.out_dir) / name
    out.mkdir(parents=True, exist_ok=True)

    # 1. Voix
    if voice is None:
        from .voice import Voice
        voice = Voice(language=job.language, reference_wav=job.reference_wav)
    log("🎙️  Voix Chatterbox…")
    wav = voice.say(job.text, out / "voix.wav")
    job.results["audio_local"] = str(wav)

    # 2. Image
    if job.image_path:
        log("🖼️  Envoi de l'image…")
        image_url = api.upload(job.image_path)
    else:
        log(f"🖼️  Image ({job.image_model})…")
        image_url = api.image(job.image_prompt, job.image_model)
    job.results["image_url"] = image_url

    # 3. Vidéo synchronisée
    log("☁️  Envoi de l'audio…")
    audio_url = api.upload(wav)
    job.results["audio_url"] = audio_url
    log(f"🎬 Lip sync ({job.lipsync_model})…")
    video_url = api.lipsync(job.lipsync_model, audio_url=audio_url, image_url=image_url)
    job.results["video_url"] = video_url

    log("⬇️  Téléchargement…")
    job.results["video_local"] = str(api.download(video_url, out / "video.mp4"))
    (out / "job.json").write_text(json.dumps(asdict(job), ensure_ascii=False, indent=2))
    log(f"✅ Terminé : {job.results['video_local']}")
    return job.results
