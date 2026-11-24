"""Ligne de commande : python -m xfield "Ton texte" --image-prompt "..."

Ou en lot : python -m xfield --batch scripts.json
"""
from __future__ import annotations

import argparse
import json
import sys

from .pipeline import Job, run, DEFAULT_IMAGE_MODEL, DEFAULT_LIPSYNC_MODEL


def load_dotenv(path: str = ".env") -> None:
    import os
    try:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))
    except FileNotFoundError:
        pass


def main(argv=None) -> int:
    load_dotenv()
    p = argparse.ArgumentParser(prog="xfield", description="Texte → voix Chatterbox → vidéo parlante Open Higgsfield")
    p.add_argument("text", nargs="?", help="Texte à faire dire")
    p.add_argument("--image-prompt", help="Description de la personne/scène à générer")
    p.add_argument("--image", dest="image_path", help="Image existante à animer")
    p.add_argument("--voice", dest="reference_wav", help="Extrait .wav (~10 s) de la voix à cloner")
    p.add_argument("--lang", dest="language", default="fr")
    p.add_argument("--image-model", default=DEFAULT_IMAGE_MODEL)
    p.add_argument("--lipsync-model", default=DEFAULT_LIPSYNC_MODEL)
    p.add_argument("--out", dest="out_dir", default="outputs")
    p.add_argument("--batch", help="Fichier JSON : liste d'objets avec les mêmes champs")
    a = p.parse_args(argv)

    common = {k: v for k, v in vars(a).items() if k not in {"text", "batch"} and v is not None}
    if a.batch:
        items = json.load(open(a.batch, encoding="utf-8"))
        from .voice import Voice
        voices: dict = {}
        ok = 0
        for i, item in enumerate(items, 1):
            job = Job(**{**common, **item})
            key = (job.language, job.reference_wav)
            voices.setdefault(key, Voice(language=job.language, reference_wav=job.reference_wav))
            print(f"\n[{i}/{len(items)}] {job.text[:60]}")
            try:
                run(job, voice=voices[key]); ok += 1
            except Exception as e:  # on continue le lot
                print(f"❌ {e}", file=sys.stderr)
        print(f"\n{ok}/{len(items)} vidéos produites.")
        return 0 if ok == len(items) else 1

    if not a.text:
        p.error("donne un texte, ou --batch")
    run(Job(text=a.text, **common))
    return 0


if __name__ == "__main__":
    sys.exit(main())
