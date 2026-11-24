# xfield

Relie **Chatterbox** (voix, Resemble AI) et **Open Higgsfield AI** (image et vidéo, via l'API Muapi.ai) en un seul outil :

```
texte ──► Chatterbox (voix FR, clonage possible) ──► voix.wav
                                                         │
prompt ou photo ──► image (Flux…) ──────────────────────►├──► lip sync ──► video.mp4
```

## Installation (sur ton ordinateur, idéalement avec une carte graphique NVIDIA)

```bash
git clone https://github.com/<ton-compte>/xfield.git
cd xfield
python3.11 -m venv .venv && source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env    # puis colle ta clé Muapi dedans
```

La clé Muapi se crée sur https://muapi.ai : c'est le même service que celui qu'utilise Open Higgsfield. Les générations d'image et de vidéo y sont **payantes à l'usage**. La voix, elle, tourne gratuitement sur ta machine.

## Utilisation

```bash
# Générer un personnage et le faire parler
python -m xfield "Bienvenue sur ma chaîne ! Aujourd'hui on parle d'IA." \
  --image-prompt "portrait d'une présentatrice souriante, studio lumineux, photo réaliste"

# Animer ta propre photo, avec ta propre voix (extrait de 10 s)
python -m xfield "Salut, c'est moi !" --image moi.jpg --voice ma_voix.wav

# Plusieurs vidéos d'un coup
python -m xfield --batch exemples/scripts.json
```

Chaque vidéo arrive dans `outputs/<date>-<titre>/` avec `voix.wav`, `video.mp4` et `job.json` (les liens et réglages utilisés).

## Réglages

| Variable / option | Rôle | Défaut |
|---|---|---|
| `MUAPI_API_KEY` | clé Muapi | — |
| `--lang` | langue de la voix | `fr` |
| `--image-model` / `XFIELD_IMAGE_MODEL` | modèle d'image Muapi | `flux-dev-image` |
| `--lipsync-model` / `XFIELD_LIPSYNC_MODEL` | modèle lip sync | `infinitetalk-image-to-video` |

Les noms de modèles disponibles sont ceux affichés dans Open Higgsfield ou sur muapi.ai ; si l'un d'eux change, il suffit de le passer en option.

## Test (sans GPU ni réseau)

```bash
python -m unittest discover tests
```

> Chaque audio Chatterbox contient un filigrane invisible (PerTh) qui permet de l'identifier comme généré par IA. N'utilise le clonage que sur ta voix ou avec l'accord de la personne.
