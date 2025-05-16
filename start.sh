#!/usr/bin/env bash
# ------------------------------------------------------------
# start.sh – one‑command bootstrap + runner for PLLM demo
# ------------------------------------------------------------
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

GREEN=$'\e[1;32m'; NC=$'\e[0m'
tick(){ printf "${GREEN}✔ %s${NC}\n" "$*"; }
step(){ printf "\n${GREEN}▶ %s...${NC}\n" "$*"; }

# 0. Banner & intro -----------------------------------------
cat <<'BANNER'
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  Raiders of the Lost Dependency  •  PLLM DEMO┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
BANNER
echo "Welcome! This assistant sets up an LLM‑powered tool that"
echo "iteratively fixes Python dependency problems in code snippets."
echo "Everything will be installed locally; just follow the prompts."

# 1. Python 3.11 & virtual‑env -------------------------------
if ! command -v python3.11 &>/dev/null; then
  step "Installing Python 3.11"
  sudo apt-get update -qq
  sudo apt-get install -y software-properties-common
  sudo add-apt-repository -y ppa:deadsnakes/ppa
  sudo apt-get update -qq
  sudo apt-get install -y python3.11 python3.11-venv python3.11-distutils
  tick "Python 3.11 ready"
fi

step "Creating / re‑using virtual‑env (.venv)"
[[ -d .venv ]] || python3.11 -m venv .venv
tick "Virtual‑env ready"
source .venv/bin/activate
pip install --upgrade --quiet pip wheel > /dev/null

step "Installing Python packages (16 total)"
REQS=(
  datetime==5.5 python-dateutil==2.9.0.post0 transformers==4.41.1
  accelerate==0.30.1 "requests<2.32" docker==7.1.0 ollama==0.2.0
  langchain==0.2.1 langchain-community==0.2.1 langchain-openai==0.1.9
  llama-index-llms-ollama==0.1.5 jq==1.7.0 pypi-json==0.4.0
  jsonschema==4.22.0 load-dotenv==0.1.0 pyyaml==6.0.1
)
pip install --quiet "${REQS[@]}"
tick "Python packages installed (16/16)"

# 2. Ollama CLI & daemon ------------------------------------
if ! command -v ollama &>/dev/null; then
  step "Installing Ollama CLI & daemon"
  curl -fsSL https://ollama.com/install.sh | sh
  tick "Ollama installed"
fi

if ! pgrep -x ollama &>/dev/null; then
  step "Starting Ollama daemon"
  nohup ollama serve >/dev/null 2>&1 &
  sleep 3
  tick "Ollama daemon running"
fi

# 2b. Model selection / download -----------------------------
echo
echo "Local Ollama models:"
ollama list || true
read -r -p "Model to use [gemma3:4b-it-qat]: " MODEL
MODEL=${MODEL:-gemma3:4b-it-qat}

if ! ollama list | grep -q "^$MODEL"; then
  step "Pulling model $MODEL (first time)"
  ollama pull "$MODEL"
  tick "Model downloaded"
fi

# 3. Prep done ----------------------------------------------
echo
tick "All prerequisites are ready"

# 4. Choose run mode ----------------------------------------
echo
echo "Select run mode:"
echo "  1) Interactive agent (step‑by‑step)  ← talk to the assistant"
echo "  2) Easy mode (single‑shot run)       ← let it run unattended"
read -r -p "Your choice [1]: " MODE
MODE=${MODE:-1}

if [[ $MODE == 2 ]]; then
  read -r -p "Path to Python file [local-test-gists/5780127/snippet.py]: " FILE
  FILE=${FILE:-"$PROJECT_DIR/local-test-gists/5780127/snippet.py"}
  echo
  step "Running easy mode – please wait"
  #  Easy mode section – replace the call
    (
    cd "$PROJECT_DIR/src"
    "$PROJECT_DIR/.venv/bin/python" test_executor.py \
            -f "$FILE" -m "$MODEL" -b "http://localhost:11434" -t 0.7 -r 1
    )

else
  step "Launching interactive assistant"
  exec "$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/src/start.py" "$@"
fi
