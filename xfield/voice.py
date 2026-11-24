"""Synthèse vocale locale avec Chatterbox (Resemble AI).

Le modèle multilingue gère le français (language_id="fr") et peut cloner
une voix à partir d'un extrait de ~10 s (audio_prompt_path).
"""
from __future__ import annotations

from pathlib import Path


def pick_device(preferred: str | None = None) -> str:
    if preferred:
        return preferred
    import torch
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class Voice:
    def __init__(self, language: str = "fr", device: str | None = None,
                 reference_wav: str | None = None, exaggeration: float = 0.5,
                 cfg_weight: float = 0.5):
        self.language = language
        self.device = pick_device(device)
        self.reference_wav = reference_wav
        self.exaggeration = exaggeration
        self.cfg_weight = cfg_weight
        self._model = None

    @property
    def model(self):
        if self._model is None:
            if self.language == "en":
                from chatterbox.tts import ChatterboxTTS
                self._model = ChatterboxTTS.from_pretrained(device=self.device)
            else:
                from chatterbox.mtl_tts import ChatterboxMultilingualTTS
                self._model = ChatterboxMultilingualTTS.from_pretrained(device=self.device)
        return self._model

    def say(self, text: str, out_path: str | Path) -> Path:
        import torchaudio as ta
        kw = {"exaggeration": self.exaggeration, "cfg_weight": self.cfg_weight}
        if self.reference_wav:
            kw["audio_prompt_path"] = self.reference_wav
        if self.language != "en":
            kw["language_id"] = self.language
        wav = self.model.generate(text, **kw)
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        ta.save(str(out), wav, self.model.sr)
        return out
