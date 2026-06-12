# RAG-PDF-Chatbot

A small Retrieval-Augmented Generation (RAG) demo that lets you chat with the contents of PDF documents.

Prerequisites

- Python 3.10+ (3.11 recommended)
- Virtual environment (venv) or equivalent

Install dependencies

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the app

```powershell
python app.py
```

Run tests

```powershell
pytest -q
# or
python test_openrouter.py
```

Notes

- Edit `requirements.txt` to pin or update dependencies.
- The main entrypoint is `app.py`.

Contributing

- Feel free to open issues or submit PRs.

License

- MIT
