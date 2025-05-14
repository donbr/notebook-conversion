# RAG-Notebook Pipeline

A curated set of research / demo **Jupyter notebooks** exploring Retrieval-Augmented Generation (RAG) techniques.  A fully-automated pipeline keeps the notebooks tidy, well-documented and easy to browse:

* **Raw ideas in → clean artefacts out.**  You can focus on experimentation; the repository takes care of formatting, code / markdown separation and a searchable index.
* **Reproducibility first.**  Every generated artefact can be rebuilt from the original `.ipynb`, so the repo never bloats with transient files.
* **Cross-platform.**  Works on Windows, macOS and Linux (Python 3.11).

## Directory structure

| Folder | Contents | Git policy |
|--------|----------|------------|
| `raw/` | Original **source** notebooks (`*.ipynb`). | Folder is version-controlled, notebook *contents* are ignored so you can commit paths without bloating the repo. |
| `interim/` | Sanitised copies of each notebook plus generated pairs:<br>• `<slug>-py-only.py` (code)<br>• `<slug>-md-only.md` (markdown)<br>• `index.md` catalogue | Folder is kept; **all contents are git-ignored**—recreate at any time with a converter run. |
| `processed/` | Reserved for future artefacts (e.g. data outputs, converted formats). | Folder is kept; contents ignored. |

## Workflow
1. **Author notebooks** in `raw/…/*.ipynb`.
2. Run the converter:

You now have **two** conversion flavours – pick whichever you like:

| Purpose | Command | Output Files |
|---------|---------|-------------|
| **Full split** (pure-code & pure-markdown exports)&nbsp;• obeys the Cursor rule | `python tools/notebook_conversion.py --all` | `pydanticai-a-new-agent-framework-py-only.py`<br>`pydanticai-a-new-agent-framework-md-only.md` |
| **Legacy/simple** (mixed content – markdown comments inside `.py`) | `python tools/notebook_conversion_simple.py --all` | `pydanticai-a-new-agent-framework.py` (percent-format, includes commented markdown)<br>`pydanticai-a-new-agent-framework.md` |

Both commands copy each notebook into `interim/<slug>/<slug>.ipynb` (slug = sanitised name) **and rebuild `interim/index.md`** so the catalogue always points to the latest artefacts.

```powershell
# full split
python tools/notebook_conversion.py --all

# or, keep the old mixed-content style
python tools/notebook_conversion_simple.py --all
```

What happens either way:
* the notebook is copied to the interim folder
* paired script & docs are produced according to the flavour selected
* `interim/index.md` is refreshed with links to both files

**Do not edit files inside `interim/` directly.** Always change the source notebook then re-run one of the converter commands.

## Development setup (with [uv](https://docs.astral.sh/uv/))

See the official installation guide: <https://docs.astral.sh/uv/#installation>.

Once `uv` is installed:

```powershell
uv python install 3.11      # fetch Python 3.11 (one-time)
uv venv --python 3.11     # create & activate .venv

# see notes below on venv activation

# install dependencies
uv pip install -r requirements.txt
```

After `uv venv` finishes, activate the environment as suggested in its output:

* **PowerShell**: `.venv\Scripts\Activate.ps1`
* **cmd.exe**: `.venv\Scripts\activate.bat`
* **Bash / Zsh** (macOS/Linux): `source .venv/bin/activate`

Tip – you can always re-display the activation hint by running `uv venv --help` or checking the `Using … Activate with:` line printed by the command.

## Contributing
* Keep new notebooks small and purposeful.
* Add rich markdown explanations – the converter will turn them into docstrings or comments.
* If you need additional stop-words or slug rules edit `tools/notebook_conversion.py`.

# Acknowledgements

This project was inspired by—and borrows many ideas from—the awesome **AI Makerspace** community.  Their motto *Build → Ship → Share* keeps us moving.  Check out their ever-growing knowledge base: [Awesome AIM Index](https://github.com/AI-Maker-Space/Awesome-AIM-Index).
