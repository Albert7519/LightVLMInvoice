# Contributing to LightVLMInvoice

Thank you for considering a contribution to LightVLMInvoice.

This project is a local, privacy-preserving VLM-based invoice and document extraction system. Contributions that improve reliability, reproducibility, document parsing quality, deployment, or maintainability are welcome.

## Good first contribution areas

- Improve Docker and deployment documentation.
- Add examples for common invoice or document layouts.
- Improve JSON schema validation and output repair.
- Add tests for PDF splitting, image conversion, extraction output, and API behavior.
- Report bugs with reproducible sample inputs or anonymized test documents.
- Improve frontend usability and error messages.

## Development setup

1. Fork and clone the repository.
2. Create a feature branch.
3. Copy `.env.example` to `.env` and adjust local settings.
4. Start the services:

```bash
cd docker
docker-compose up -d --build
```

5. Open the frontend and backend API documentation:

```text
Frontend: http://localhost:8002
Backend API docs: http://localhost:8005/docs
```

## Pull request guidelines

Before opening a pull request:

- Keep the change focused and explain the motivation.
- Include reproduction steps for bug fixes.
- Update documentation when behavior or configuration changes.
- Avoid committing secrets, private invoices, API keys, or real personal data.
- Prefer anonymized or synthetic test data.

## Issue guidelines

When opening an issue, include:

- Operating system and Docker version.
- GPU model and NVIDIA Container Toolkit version, if relevant.
- Model name and vLLM settings.
- Steps to reproduce.
- Expected behavior and actual behavior.
- Logs, screenshots, or sanitized example files when possible.

## Security and privacy

Do not upload real invoices, identity documents, private financial data, API keys, or confidential business documents to issues or pull requests. Use synthetic or anonymized examples only.
