# Security Policy

## API keys and credentials

- This repository does **not** provide shared API keys.
- Every user must configure their own model provider credentials through `.env` or the in-app **设置** page.
- Never commit `.env`, secrets, or screenshots that expose API keys.

## Local data

The following directories may contain private local data and must not be committed:

- `data/uploads/`
- `data/outputs/`
- `data/projects/`
- `data/cache/`

## Responsible disclosure

If you discover a security issue in this project, please report it privately to the maintainer before opening a public issue.
