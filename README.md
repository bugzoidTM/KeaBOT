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

KeaBot é um **Agente de Automação Local** totalmente funcional que combina uma interface React moderna com um backend Python robusto, permitindo que uma IA execute tarefas no seu sistema de forma segura e controlada. O projeto evoluiu para uma plataforma madura, suportando múltiplos provedores de LLM e gerenciamento visual de skills.

### 🎯 Principais Funcionalidades

*   **Multi-Provider LLM**: Suporte integrado para **Google Gemini**, **OpenAI**, **Anthropic** e **DeepSeek**.
*   **Gerenciamento de Skills**: Interface visual para criar, editar e excluir Skills (arquivos Markdown) que ensinam novos truques ao agente.
*   **Automação com Segurança**: Sistema de permissões granulares onde ações críticas (como deletar arquivos ou rodar comandos shell) exigem aprovação humana.
*   **Contexto Inteligente**: O agente navega pelo sistema de arquivos e lê apenas o necessário, mantendo o contexto eficiente.

---

## 🏗️ Arquitetura

O sistema utiliza uma arquitetura híbrida moderna:

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React/Vite)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Chat UI   │  │ Skills Mgr  │  │  LLM Configuration  │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
└─────────┼────────────────┼────────────────────┼─────────────┘
          │                │ REST / WebSocket   │
          ▼                ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                 API GATEWAY (FastAPI)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    AGENT CORE                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  LLM Router  │  │ Skill Loader │  │  Safety Layer    │   │
│  │ (Multi-Prov) │  │  (Markdown)  │  │  (Human-in-Loop) │   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │
└─────────┼────────────────┼────────────────────┼─────────────┘
          │                │                    │
┌─────────▼────────────────▼────────────────────▼─────────────┐
│                    TOOL LAYER                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐    │
│  │   FS     │ │  Shell   │ │ Browser  │ │ Code Tools   │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Status do Projeto: Concluído

Todas as etapas de desenvolvimento foram finalizadas:

✅ **Core do Backend**: API FastAPI, WebSocket, Agent Loop (ReAct).
✅ **Sistema de Skills**: Carregamento dinâmico, CRUD via API e UI.
✅ **Suporte Multi-LLM**: Arquitetura plugável para Gemini, OpenAI, Anthropic, DeepSeek.
✅ **Frontend Completo**: Chat com streaming, Gerenciamento de Skills, Configurações, File Explorer.
✅ **Safety Layer**: Fluxo de aprovação para ações sensíveis.

---

## ⚡ Quick Start

### Pré-requisitos
- **Node.js** >= 18
- **Python** >= 3.11

### Instalação e Execução

1.  **Backend SETUP**:
    ```bash
    cd backend
    python -m venv .venv
    .\.venv\Scripts\activate  # Windows
    pip install -r requirements.txt
    playwright install
    uvicorn app.main:app --reload --port 8000
    ```

2.  **Frontend SETUP**:
    ```bash
    # Em outro terminal, na raiz do projeto
    npm install
    npm run dev
    ```

3.  **Acesso**:
    Abra `http://localhost:3000` no seu navegador.

---

## ⚙️ Configuração

Você pode configurar os provedores de IA diretamente pela interface em **Settings** ou via variáveis de ambiente.

**Provedores Suportados:**
*   **Google Gemini**: Modelos Flash 2.5, Pro 2.5 (Recomendado/Default)
*   **OpenAI**: GPT-4o
*   **Anthropic**: Claude 3.5 Sonnet
*   **DeepSeek**: DeepSeek V3/R1

---

## 📚 Criando Skills

Skills são a maneira de ensinar o KeaBot a realizar novas tarefas. Você pode criá-las pela interface gráfica ou adicionando arquivos `.md` na pasta `backend/skills`.

**Exemplo de Skill:**
```markdown
---
name: Git Expert
description: Realiza operações avançadas de git
triggers: ["git", "commit", "push"]
---

# Instruções

Sempre verifique o status do repositório com `git status` antes de realizar commits.
Nunca faça push em branches protegidas sem confirmação explícita.
```

---

## 🛡️ Segurança

O KeaBot roda localmente na sua máquina com permissões reais.
*   **Ações Seguras** (ler arquivos, listar diretórios): Executadas automaticamente.
*   **Ações Críticas** (escrever arquivos, rodar comandos): Podem exigir aprovação dependendo do modo de segurança configurado.

---

## 📄 Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

By @BugZoidTM