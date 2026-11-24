"""Client minimal pour l'API Muapi.ai, le moteur utilisé par Open Higgsfield AI.

Même logique que packages/studio/src/muapi.js d'Open Higgsfield :
  - POST /api/v1/upload_file          -> héberge un fichier, renvoie une URL
  - POST /api/v1/{endpoint}           -> lance une génération, renvoie un request_id
  - GET  /api/v1/predictions/{id}/result -> à interroger jusqu'à 'completed'
Authentification : en-tête x-api-key.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import requests

BASE_URL = os.environ.get("MUAPI_BASE_URL", "https://api.muapi.ai")
DONE = {"completed", "succeeded", "success"}
FAILED = {"failed", "error"}


class MuapiError(RuntimeError):
    pass


class Muapi:
    def __init__(self, api_key: str | None = None, base_url: str = BASE_URL,
                 session: requests.Session | None = None):
        self.api_key = api_key or os.environ.get("MUAPI_API_KEY")
        if not self.api_key:
            raise MuapiError("Clé manquante : définis MUAPI_API_KEY (voir .env.example).")
        self.base_url = base_url.rstrip("/")
        self.http = session or requests.Session()
        self.http.headers["x-api-key"] = self.api_key

    # -- bas niveau ---------------------------------------------------------
    def upload(self, path: str | Path) -> str:
        """Envoie un fichier local (audio, image) et renvoie son URL hébergée."""
        path = Path(path)
        with path.open("rb") as f:
            r = self.http.post(f"{self.base_url}/api/v1/upload_file",
                               files={"file": (path.name, f)}, timeout=300)
        r.raise_for_status()
        data = r.json()
        url = data.get("url") or data.get("file_url") or (data.get("data") or {}).get("url")
        if not url:
            raise MuapiError(f"Upload sans URL en retour : {data}")
        return url

    def submit(self, endpoint: str, payload: dict) -> str:
        r = self.http.post(f"{self.base_url}/api/v1/{endpoint}", json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        rid = data.get("request_id") or data.get("id") or (data.get("data") or {}).get("request_id")
        if not rid:
            raise MuapiError(f"Pas de request_id pour {endpoint} : {data}")
        return rid

    def wait(self, request_id: str, every: float = 3.0, timeout: float = 1200) -> str:
        """Interroge le résultat jusqu'à la fin et renvoie l'URL du média produit."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            r = self.http.get(f"{self.base_url}/api/v1/predictions/{request_id}/result", timeout=60)
            r.raise_for_status()
            data = r.json()
            status = str(data.get("status", "")).lower()
            if status in DONE:
                url = ((data.get("outputs") or [None])[0] or data.get("url")
                       or (data.get("output") or {}).get("url"))
                if not url:
                    raise MuapiError(f"Terminé mais sans média : {data}")
                return url
            if status in FAILED:
                raise MuapiError(f"Génération échouée : {data.get('error') or data}")
            time.sleep(every)
        raise MuapiError(f"Délai dépassé pour {request_id}")

    def run(self, endpoint: str, payload: dict, **wait_kw) -> str:
        return self.wait(self.submit(endpoint, payload), **wait_kw)

    # -- haut niveau --------------------------------------------------------
    def image(self, prompt: str, model: str, **extra) -> str:
        return self.run(model, {"prompt": prompt, **extra})

    def lipsync(self, model: str, audio_url: str, image_url: str | None = None,
                video_url: str | None = None, prompt: str | None = None) -> str:
        payload: dict = {"audio_url": audio_url}
        if image_url:
            payload["image_url"] = image_url
        if video_url:
            payload["video_url"] = video_url
        if prompt is not None:
            payload["prompt"] = prompt
        return self.run(model, payload)

    def download(self, url: str, dest: str | Path) -> Path:
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(url, stream=True, timeout=600) as r:
            r.raise_for_status()
            with dest.open("wb") as f:
                for chunk in r.iter_content(1 << 16):
                    f.write(chunk)
        return dest
