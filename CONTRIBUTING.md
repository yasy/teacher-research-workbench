# Contributing

## Development workflow

1. Fork the repository or create a feature branch.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env`, then use **your own** model provider credentials.
4. Run the app locally with `streamlit run app.py`.
5. Before submitting changes, run:
   - `python -m pytest tests -q`
   - `python -m py_compile app.py`

## Important rules

- Do not commit `.env`, API keys, uploaded PDFs, exported files, or local project snapshots.
- Keep the app focused on teacher research writing workflow.
- Prefer small, reviewable pull requests.

## Reporting issues

When reporting an issue, please include:

- operating system
- Python version
- model provider
- reproduction steps
- screenshots if the issue is UI related
