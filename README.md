# PLLM‑Interactive 🚀
> *Debug Python dependency hell together with an LLM – one step at a time.*

`PLLM‑Interactive` is a lightweight, drop‑in tool that spins up a **chat‑style agent** for fixing import / version conflicts in arbitrary Python scripts or Gists.  
You run *one* shell script, point it at a snippet, and the agent:

1. guesses the required Python version & packages,  
2. generates a Docker image, tries to build/run it,  
3. shows a **two‑line diagnosis** from the LLM,  
4. lets **you** tweak the plan live (`py==3.7`, `pillow==6.2`, `del getopt`, …).

No more deciphering hundred‑line error logs, no more editing Dockerfiles by hand.

---

## ⚠️ Disk usage warning

By design, this system **downloads and tests real Python packages** inside Docker.  
This may result in **high disk usage** (several GB), especially for longer or more complex code snippets.

To free space, you may:

- delete the `.venv/` folder if unused
- run `docker system prune -a`
- remove downloaded Ollama models (see below)

---

## 🛠️  Quick start

```bash
# 1. clone & enter
git clone https://github.com/<your-name>/pllm-interactive.git
cd pllm-interactive

# 2. run the bootstrap script (creates venv, installs deps, pulls a model)
./start.sh
```

You’ll be prompted for:

- **Snippet path** – e.g. `local-test-gists/5780127/snippet.py`  
- **Ollama model** – default is `gemma3:4b-it-qat`  
- **Run mode**  
  - 1 = interactive mode (recommended)  
  - 2 = unattended batch mode  
- Optional range & loop params (±Python versions, max tries)

---

## 💬 Interactive mode command cheatsheet

```
↩ <Enter>     retry with current plan
py==3.8       force Python version
pillow==6.0   pin / change module version
del getopt    remove module
q / quit      abort program
```

Every error summary is auto‑explained like:

```
🧠 SUMMARY: getopt==1.2.2 does not exist on PyPI for Python 3.8.
🧠 NEXT: remove getopt or drop the explicit version pin.
```

Logs are saved next to the snippet in:  
`output_data_interactive.yml`

---

## 🏗️ Manual usage

```bash
pip install -r requirements.txt
cd src
python test_executor.py \
    -f "../local-test-gists/5780127/snippet.py" \
    -m "gemma3:4b-it-qat" \
    -r 1  -l 10  -i
```

All CLI flags (`-f -m -r -l -i -t ...`) are unchanged from the original tool.

---

## 📦 Using different Ollama models

```bash
ollama pull phi3:medium
ollama pull llama3
```

Then, specify them at the prompt or use the -m flag in CLI mode.

For best results, pick chat-capable models with code reasoning ability.
(Quantized models like 4b-it-qat are smaller but may miss edge cases.)

---

## 🧯 Troubleshooting

### error: model not found
Run ollama pull <model> manually to fetch it.

### Docker out of space
Run docker system prune -a to clean up old containers & images.

### Interactive mode hangs at input
Ensure you're in a real terminal (not VSCode output panel).

### Python modules not found
May be falsely inferred (e.g. stdlib like sys, os) — just del them.

Then, specify them at the prompt or use the -m flag in CLI mode.

For best results, pick chat-capable models with code reasoning ability.
(Quantized models like 4b-it-qat are smaller but may miss edge cases.)

---

## 📂 Repo contents

| Path/Script           | Purpose |
|-----------------------|---------|
| `start.sh`            | one-liner bootstrap (venv + Ollama setup) |
| `start.py`            | simple menu wrapper that calls `test_executor.py` |
| `src/`                | core logic with new interactive enhancements |
| `local-test-gists/`   | demo Gists for quick testing |
| `Dockerfile`          | optional dockerized runner |

Omitted from this repo (see `.gitignore`):

- `pllm_results/`, `pyego-results/`, `readpy-results/` (for evaluation only)
- `.venv/` (local Python environment)

---

## ✨ Improvements vs. the original PLLM package

| Feature | Original | **This repo** |
|---------|----------|---------------|
| One‑liner installer (`start.sh`) | – | ✅ |
| Interactive mode (`-i`) with LLM summaries | – | ✅ |
| Tiny command language (`py==3.7`, `del foo`, …) | – | ✅ |
| Unified YAML log (`output_data_interactive.yml`) | long per-version logs | ✅ |
| Std-lib detection (never installs `os`, `sys`, …) | ❌ | ✅ |

---

## 🧪 Reproduce ISSTA 2025 evaluations

You can reproduce all benchmark results from the original paper.

```bash
# 1. fetch the hard-gist set (from paper §4)
./scripts/download_hard_gists.sh

# 2. run them in batch mode
nohup ./run_gists.sh > run.log 2>&1 &
```

Results appear in `pllm_results/` and match the published numbers.

---

## 📜 Original study

This project is based on the ISSTA 2025 paper:

**Raiders of the Lost Dependency: Fixing Dependency Conflicts in Python using LLMs**  
by *Antony Bartlett, Cynthia C. S. Liem, and Annibale Panichella*  
[[arXiv:2501.16191](https://arxiv.org/abs/2501.16191)]

The original work showed how to use large language models (LLMs) to autonomously resolve dependency conflicts in Python via static analysis and Docker validation.  
This fork focuses on **developer experience**, adding a true human-in-the-loop workflow.

If you use this repo in academic work, please cite the original:

```bibtex
@article{Bartlett2025Raiders,
  title  = {Raiders of the Lost Dependency: Fixing Dependency Conflicts in Python using LLMs},
  author = {Bartlett, Antony and Liem, Cynthia C. S. and Panichella, Annibale},
  year   = {2025},
  journal= {arXiv preprint arXiv:2501.16191}
}
```

---

## 🪪 License

Apache 2.0 – same as upstream.  
Ollama model licenses may differ; check model sources for terms.

---
