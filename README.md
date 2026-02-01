<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />

# 🦜 KeaBot

**Agente de Automação Local Inteligente**

*Transformando sua máquina em um assistente autônomo*

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📖 Visão Geral

KeaBot é um **Agente de Automação Local** que combina uma interface React moderna com um backend Python robusto, permitindo que uma IA execute tarefas no seu sistema de forma segura e controlada.

### 🎯 Filosofia do Sistema

| Princípio | Descrição |
|-----------|-----------|
| **Contexto Infinito via Recursividade** | A IA nunca lê arquivos inteiros. Usa ferramentas (`ls`, `grep`, `read_chunk`) para navegar e ler sob demanda. |
| **Skills Modulares (.md)** | Capacidades estendidas via arquivos Markdown na pasta `/skills`. |
| **Safety Layer** | Ações destrutivas exigem aprovação humana explícita. |
| **Arquitetura Híbrida** | Backend Python (FastAPI) + Frontend React (Vite). |

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React/Vite)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Chat UI   │  │  File Tree  │  │  Approval Modal     │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
└─────────┼────────────────┼────────────────────┼─────────────┘
          │                │                    │
          ▼                ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                 API GATEWAY (FastAPI)                       │
│         WebSocket + REST | SSE Streaming                    │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    AGENT CORE                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Tool Router  │  │ Context Mgr  │  │  Safety Layer    │   │
│  │  (ReAct)     │  │  (Memory)    │  │  (Human-in-Loop) │   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │
└─────────┼────────────────┼────────────────────┼─────────────┘
          │                │                    │
┌─────────▼────────────────▼────────────────────▼─────────────┐
│                    TOOL LAYER                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐    │
│  │   FS     │ │  Shell   │ │  HTTP    │ │ Code Tools   │    │
│  │ (ls,cat) │ │ (bash)   │ │ (fetch)  │ │ (grep,parse) │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
          │
┌─────────▼───────────────────────────────────────────────────┐
│                    SKILLS (/skills/*.md)                    │
│   Instruções modulares que estendem as capacidades da IA    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Plano de Implementação

O desenvolvimento será feito em **4 Etapas**:

### Etapa 1: Core do Backend
> *Fundação do sistema*

- [ ] Estrutura FastAPI com WebSocket
- [ ] Sistema de Tools básico (filesystem, shell)
- [ ] Integração com Gemini/OpenAI API
- [ ] Loop ReAct simples (Thought → Action → Observation)

### Etapa 2: Safety Layer + Context Manager
> *Segurança e memória*

- [ ] Classificação de ações (safe/unsafe)
- [ ] Approval flow via WebSocket
- [ ] Context window infinito com chunking
- [ ] Working memory persistente

### Etapa 3: Skills System
> *Extensibilidade*

- [ ] Parser de Skills (.md)
- [ ] Hot-reload de skills
- [ ] Skills built-in (git, docker, npm, etc.)
- [ ] Skill discovery automático

### Etapa 4: Integração Frontend
> *Conexão com React UI*

- [ ] Streaming de mensagens (SSE)
- [ ] File browser integrado
- [ ] Terminal embutido
- [ ] Status de aprovação em tempo real

---

## 📁 Estrutura do Projeto (Planejada)

```
KeaBOT/
├── backend/                    # 🐍 Python Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI entry point
│   │   ├── agent/
│   │   │   ├── core.py         # ReAct loop
│   │   │   ├── context.py      # Context manager
│   │   │   └── safety.py       # Safety layer
│   │   ├── tools/
│   │   │   ├── base.py         # Tool base class
│   │   │   ├── filesystem.py   # ls, cat, read_chunk
│   │   │   ├── shell.py        # Execute commands
│   │   │   └── code.py         # grep, ast parsing
│   │   ├── skills/
│   │   │   └── loader.py       # Skill parser
│   │   └── api/
│   │       ├── routes.py       # REST endpoints
│   │       └── websocket.py    # Real-time communication
│   ├── skills/                 # 📚 Skill files (.md)
│   │   ├── git.md
│   │   ├── docker.md
│   │   └── debugging.md
│   ├── requirements.txt
│   └── pyproject.toml
│
├── src/                        # ⚛️ React Frontend (existente)
│   ├── components/
│   ├── pages/
│   └── services/
│
├── .env.local                  # API keys
└── README.md                   # Este arquivo
```

---

## ⚡ Quick Start

### Pré-requisitos
- **Node.js** >= 18
- **Python** >= 3.11
- **Gemini API Key** ou **OpenAI API Key**

### Frontend (Existente)
```bash
npm install
npm run dev
```

### Backend (Após Etapa 1)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## 🔐 Variáveis de Ambiente

```env
# .env.local
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key  # Opcional
KEABOT_SAFETY_MODE=strict       # strict | permissive
KEABOT_ALLOWED_PATHS=/home,/tmp # Paths permitidos para o agente
```

---

## 🛡️ Safety Layer

O KeaBot implementa um sistema de segurança em camadas:

| Nível | Ação | Comportamento |
|-------|------|---------------|
| 🟢 **Safe** | `ls`, `cat`, `grep` | Executa automaticamente |
| 🟡 **Review** | `write_file`, `mkdir` | Log + pode requerer aprovação |
| 🔴 **Dangerous** | `rm`, `shell`, `sudo` | **Sempre** requer aprovação humana |

---

## 📚 Skills System

Skills são arquivos Markdown que estendem as capacidades do agente:

```markdown
# skills/git.md

---
name: Git Operations
triggers: ["commit", "push", "branch", "merge"]
---

## Instruções

Quando o usuário pedir operações git:

1. Sempre execute `git status` primeiro
2. Nunca faça `git push --force` sem aprovação
3. Para commits, sugira uma mensagem seguindo Conventional Commits
```

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add: AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📄 Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

---

<div align="center">

**Pronto para começar?** 

Digite **"Etapa 1"** para iniciar a construção do Core do Backend! 🚀

</div>
