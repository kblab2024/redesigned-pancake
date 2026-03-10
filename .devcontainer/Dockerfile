FROM ubuntu:22.04

# Avoid interactive prompts during package installation
ARG DEBIAN_FRONTEND=noninteractive

# ── System packages ──────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Core utilities
    ca-certificates \
    curl \
    wget \
    git \
    gnupg \
    lsb-release \
    sudo \
    unzip \
    zip \
    jq \
    bash-completion \
    # Python 3
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    # C / C++ toolchain
    build-essential \
    gcc \
    g++ \
    gdb \
    cmake \
    make \
    ninja-build \
    clang \
    clang-format \
    clangd \
    libc++-dev \
    libc++abi-dev \
    # Networking / REST
    httpie \
    && rm -rf /var/lib/apt/lists/*

# ── Docker CLI (Docker-outside-of-Docker) ────────────────────────────────────
# Install Docker Engine so the container can manage sibling containers via the
# host socket that devcontainer mounts at /var/run/docker.sock.
RUN install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
       | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && chmod a+r /etc/apt/keyrings/docker.gpg \
    && echo \
       "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
       https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
       > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
       docker-ce-cli \
       docker-compose-plugin \
    && rm -rf /var/lib/apt/lists/*

# ── Python packages ───────────────────────────────────────────────────────────
# Upgrade pip first, then install data-science and DSA client libraries.
RUN python3 -m pip install --no-cache-dir --upgrade pip \
    && python3 -m pip install --no-cache-dir \
       # Data-science stack (required by the problem statement)
       numpy \
       openpyxl \
       pandas \
       # HTTP & REST helpers
       requests \
       httpx \
       # Digital Slide Archive Python client
       girder-client \
       # Notebook support (handy for interactive exploration)
       ipykernel \
       jupyter \
       # Linting / formatting
       black \
       flake8 \
       pylint

# ── Non-root dev user ─────────────────────────────────────────────────────────
# VS Code dev-containers convention: create a non-root user called "vscode".
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Add vscode user to the docker group so it can talk to the Docker socket
# (group is created lazily; use numeric GID 999 which is the common Docker GID)
RUN groupadd -f -g 999 docker && usermod -aG docker $USERNAME

# ── Shell niceties ────────────────────────────────────────────────────────────
# Make python3 / pip3 accessible without the "3" suffix
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1 \
    && update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# Persist bash history in the workspace volume so it survives container rebuilds
RUN SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
    && mkdir /commandhistory \
    && touch /commandhistory/.bash_history \
    && chown -R $USERNAME /commandhistory \
    && echo "$SNIPPET" >> /home/$USERNAME/.bashrc

USER $USERNAME
WORKDIR /workspace
