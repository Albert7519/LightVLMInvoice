# LightVLMInvoice

[English](README.md) | [中文](README.zh-CN.md)

LightVLMInvoice is a local Vision Large Language Model (VLM) system for structured invoice and document extraction. It parses complex layouts such as multi-page PDF files and single document images through a locally deployed VLM, avoiding external OCR APIs and helping keep sensitive business data private.

## Why this project matters

Many small teams, students, and individual developers need invoice or document OCR, but hosted OCR APIs can be costly, difficult to customize, or unsuitable for sensitive financial documents. LightVLMInvoice provides a fully local, Dockerized VLM-based extraction pipeline with asynchronous processing, JSON repair, configurable concurrency, and a clear full-stack structure.

The project is intended as a reproducible open-source reference for privacy-preserving document automation: users can run extraction locally, adapt prompts and models, and inspect the full backend, worker, frontend, and deployment stack.

## Architecture and Tech Stack

The system uses a separated frontend/backend architecture, with an asynchronous task queue designed for long-running model inference workloads.

- **Frontend**: React + Vite + TypeScript + TailwindCSS. In production, the frontend is served through Nginx.
- **Backend**: FastAPI for high-concurrency HTTP APIs.
- **Task queue**: Celery + Redis for long-running page splitting and VLM inference tasks.
- **Inference engine**: A local VLM served through vLLM. The default model is `cyankiwi/Qwen3.5-2B-AWQ-BF16-INT8`, which is designed for low VRAM usage while preserving strong layout understanding.
- **Output repair**: `json_repair` is used to recover from occasional malformed JSON emitted by the model, such as missing quotes or truncated output.

## Project Structure

```text
.
├── backend/                  # Backend and model orchestration code
│   ├── main.py               # FastAPI endpoints for upload, result polling, and related APIs
│   ├── tasks.py              # Celery tasks for PDF splitting, VLM calls, and extraction logic
│   ├── celery_app.py         # Celery and Redis configuration
│   └── requirements.txt      # Python dependencies
├── frontend/                 # Frontend application
│   ├── src/                  # React components and styles
│   ├── vite.config.ts        # Vite build and development proxy configuration
│   ├── nginx.conf            # Production reverse proxy configuration inside the frontend container
│   └── package.json          # Node dependencies
├── docker/                   # Containerized deployment files
│   ├── docker-compose.yml    # Service orchestration
│   ├── backend.Dockerfile    # Backend image build configuration
│   └── frontend.Dockerfile   # Frontend image build configuration
└── .env.example              # Environment variable template
```

## Features

1. **Complex file support**: Automatically parses multi-page PDF documents, including scanned invoice bundles, by splitting pages into images for batch processing.
2. **Asynchronous, non-blocking workflow**: After upload, the frontend polls Celery task status for progress updates instead of blocking on model inference.
3. **Robust JSON recovery**: Repairs imperfect model-generated JSON such as `{"amount": .040}` -> `{"amount": 0.04}` to reduce data loss.
4. **Fully local processing**: All inference and document parsing run in the local environment.

## Deployment

### Requirements

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- NVIDIA GPU and the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) for vLLM GPU inference inside containers

### Quick Start

1. **Clone the repository**

   ```bash
   git clone https://github.com/Albert7519/LightVLMInvoice.git
   cd LightVLMInvoice
   ```

2. **Build and start all services**

   This starts the `vllm`, `redis`, `celery`, `backend`, and `frontend` containers.

   ```bash
   cd docker
   docker-compose up -d --build
   ```

3. **Open the services**

   - **Frontend**: `http://localhost:8002`
   - **Backend API docs**: `http://localhost:8005/docs`

### Ports

- The frontend web UI is mapped to `${FRONTEND_PORT:-8002}` on the host.
- The backend FastAPI service is mapped to `${BACKEND_PORT:-8005}` on the host.

If a port is already in use, set a different value in the root `.env` file.

### Advanced Configuration and Concurrency Tuning

Runtime and performance settings are managed through `.env` variables. Create a local configuration file from the template:

```bash
cp .env.example .env
```

Key settings:

- `CELERY_CONCURRENCY=2`: Number of files Celery can process concurrently. The default is `1`; GPUs with more than 16 GB of VRAM may be able to use `2` or higher.
- `MAX_CONCURRENT_PAGES=10`: Maximum number of pages processed concurrently within a single invoice/document.
- `VLLM_MODEL=cyankiwi/Qwen3.5-2B-AWQ...`: Model name served by vLLM. You can replace it with other compatible VLMs such as LLaVA-style models.
- `VLLM_GPU_MEMORY_UTILIZATION=0.8`: GPU memory utilization ratio for vLLM.
- `VLLM_MAX_MODEL_LEN=8192`: Maximum context length. Lower values may free memory for more concurrent work.

## Development

- **Change the VLM model**: Update the model name through `.env`. Depending on the target model, you may also need to adjust the system prompt in `backend/tasks.py` to match the model's instruction format.
- **Run the frontend locally**:

  ```bash
  cd frontend
  npm install
  npm run dev
  ```

## OSS Maintainer Workflow

This repository is maintained as an open-source project. Planned maintainer workflows include:

- issue triage for deployment, parsing, model-output, and frontend problems;
- reproducible bug reports with sanitized or synthetic sample files;
- pull request review across FastAPI backend code, Celery workers, Docker configuration, and React frontend code;
- release notes for user-visible behavior, deployment changes, and model/prompt changes;
- documentation updates for local deployment, privacy constraints, and model substitution.

## Roadmap

- Add synthetic sample invoices and expected structured outputs.
- Add automated tests for PDF splitting, image conversion, JSON repair, and API responses.
- Add stricter output schema validation.
- Improve frontend error reporting and batch-processing status display.
- Document recommended vLLM settings for different GPU memory sizes.
- Publish tagged releases with changelogs.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
