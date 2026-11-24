"""Test du pipeline sans GPU ni réseau : voix et API simulées."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from xfield.pipeline import Job, run  # noqa: E402


class FakeVoice:
    def say(self, text, out):
        Path(out).write_bytes(b"RIFF....WAVE")
        return Path(out)


class FakeApi:
    def __init__(self):
        self.calls = []

    def upload(self, path):
        self.calls.append(("upload", Path(path).name)); return f"https://cdn/{Path(path).name}"

    def image(self, prompt, model):
        self.calls.append(("image", model)); return "https://cdn/img.png"

    def lipsync(self, model, audio_url, image_url=None, video_url=None, prompt=None):
        self.calls.append(("lipsync", model, audio_url, image_url)); return "https://cdn/out.mp4"

    def download(self, url, dest):
        Path(dest).write_bytes(b"mp4"); return Path(dest)


class PipelineTest(unittest.TestCase):
    def test_generated_image(self):
        with tempfile.TemporaryDirectory() as d:
            api = FakeApi()
            res = run(Job(text="Bonjour à tous", image_prompt="présentatrice souriante",
                          out_dir=d, name="t"), voice=FakeVoice(), api=api, log=lambda *_: None)
            self.assertEqual([c[0] for c in api.calls], ["image", "upload", "lipsync"])
            self.assertEqual(api.calls[2][2:], ("https://cdn/voix.wav", "https://cdn/img.png"))
            self.assertTrue(Path(res["video_local"]).exists())
            self.assertEqual(json.loads((Path(d) / "t" / "job.json").read_text())["text"], "Bonjour à tous")

    def test_existing_image(self):
        with tempfile.TemporaryDirectory() as d:
            img = Path(d) / "moi.png"; img.write_bytes(b"png")
            api = FakeApi()
            run(Job(text="Salut", image_path=str(img), out_dir=d), voice=FakeVoice(), api=api, log=lambda *_: None)
            self.assertEqual(api.calls[0], ("upload", "moi.png"))

    def test_needs_image(self):
        with self.assertRaises(ValueError):
            run(Job(text="x"), voice=FakeVoice(), api=FakeApi())


if __name__ == "__main__":
    unittest.main()
