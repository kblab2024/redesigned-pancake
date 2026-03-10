# redesigned-pancake — DSA Sandbox (VS Code Dev Container)

A self-contained development sandbox built on **VS Code Dev Containers** and **Docker**.  
It gives you a full Python / C++ / Docker environment inside an isolated Ubuntu container, plus a one-command setup for running and scripting **[Digital Slide Archive](https://github.com/DigitalSlideArchive/digital_slide_archive) (HistomicsUI)** locally.

---

## What's inside

| Layer | Tools |
|---|---|
| **OS** | Ubuntu 22.04 |
| **Python** | 3.x · `numpy` · `openpyxl` · `pandas` · `requests` · `girder-client` · Jupyter |
| **C / C++** | `gcc` · `g++` · `clang` · `cmake` · `gdb` · clangd language server |
| **Docker** | Docker CLI (Docker-outside-of-Docker via host socket) · `docker compose` |
| **DSA stack** | Girder + HistomicsUI · MongoDB · Memcached · RabbitMQ · Celery worker |
| **VS Code extensions** | Python · Black · Pylint · Jupyter · C/C++ · CMake Tools · clangd · Docker · REST Client · GitLens · GitHub Copilot |

---

## Prerequisites

| Requirement | Version |
|---|---|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine on Linux) | ≥ 24 |
| [VS Code](https://code.visualstudio.com/) | latest |
| [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) | latest |

---

## Quick start

### 1 — Open the repo in a dev container

```bash
git clone https://github.com/kblab2024/redesigned-pancake.git
code redesigned-pancake
```

VS Code will detect `.devcontainer/devcontainer.json` and prompt:

> **Reopen in Container** → click it (or use the command palette: *Dev Containers: Reopen in Container*).

The first build downloads the Ubuntu base image and installs all packages (~5 minutes).  
Subsequent opens reuse the cached image.

---

### 2 — Start HistomicsUI

Open the integrated terminal inside the container and run:

```bash
./scripts/start_dsa.sh
```

This starts the full DSA stack (`girder`, `mongodb`, `memcached`, `rabbitmq`, `worker`) and waits until the REST API is healthy.

Open **http://localhost:8080** in your browser (port is forwarded automatically).  
Default credentials: **admin / password**.

---

### 3 — Run the REST API smoke test

```bash
python3 scripts/test_dsa_api.py
```

Expected output:

```
🔬 DSA REST API smoke test → http://localhost:8080/api/v1

── Step 1: Authentication ─────────────────────────────────────────
  ✓ Authenticated as 'admin'

── Step 2: Server version ─────────────────────────────────────────
  ✓ Server: 3.x.x

── Step 3: Collections ────────────────────────────────────────────
  • DSA  (id=...)

── Step 4: Upload test ────────────────────────────────────────────
  ✓ Created folder '_api_test_tmp'
  ✓ Uploaded 'test_image.png' (85 bytes)
  ✓ Item visible in folder listing (1 item(s))
  ✓ Cleaned up test folder

✅ All checks passed — DSA REST API is functional.
```

---

## Directory structure

```
.
├── .devcontainer/
│   ├── devcontainer.json   ← VS Code dev container config
│   └── Dockerfile          ← Ubuntu image with Python, C++, Docker CLI
├── dsa/
│   ├── docker-compose.yml  ← Full DSA / HistomicsUI stack
│   └── provision.py        ← First-run provisioning (admin, plugin, collection)
├── scripts/
│   ├── start_dsa.sh        ← Start the DSA stack and wait for readiness
│   ├── stop_dsa.sh         ← Stop the DSA stack (--clean to also remove volumes)
│   ├── wait_for_dsa.sh     ← Poll until the REST API responds
│   └── test_dsa_api.py     ← Python REST API smoke test
└── README.md
```

---

## Useful commands (run inside the container)

```bash
# Start / stop HistomicsUI
./scripts/start_dsa.sh
./scripts/stop_dsa.sh
./scripts/stop_dsa.sh --clean   # also deletes MongoDB data + assetstore

# Stream DSA logs
docker compose -f dsa/docker-compose.yml logs -f

# Use the official girder-client CLI
girder-client --api-url http://localhost:8080/api/v1 \
              --username admin --password password \
              list collection

# Compile a C++ file
g++ -std=c++17 -o hello hello.cpp && ./hello

# Run a Python script with data-science libraries
python3 - <<'EOF'
import pandas as pd, numpy as np
df = pd.DataFrame({"x": np.arange(5), "y": np.random.rand(5)})
print(df)
EOF
```

---

## Scripting DSA via the REST API

The `girder-client` Python library (pre-installed) gives full access to the Girder API:

```python
import girder_client

gc = girder_client.GirderClient(apiUrl="http://localhost:8080/api/v1")
gc.authenticate("admin", "password")

# List collections
for col in gc.listCollection():
    print(col["name"])

# Upload a file into a folder
gc.uploadFileToFolder("<folder_id>", "/path/to/slide.svs")

# GET any endpoint directly
info = gc.get("system/version")
print(info)
```

You can also use plain `requests` or `curl` against any endpoint listed in the Swagger UI at **http://localhost:8080/api/v1**.

---

## Security note

The default admin password is `password`. This sandbox is intended for **local development only**. Do **not** expose port 8080 to the public internet without changing the credentials in `dsa/docker-compose.yml`.
