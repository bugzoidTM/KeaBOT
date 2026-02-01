---
name: YouTube Engagement
description: Analisa vídeos do YouTube (metadados, transcrição ou áudio real) e gera comentários autênticos.
triggers: ["youtube", "video", "transcrição", "assistir", "resumir vídeo"]
---

# Instruções

Quando o usuário pedir para analisar um vídeo do YouTube:

1.  **Chame a tool** `youtube(url="...")`.
    *   A tool tentará obter a transcrição automaticamente.
    *   Se não houver legendas, a tool baixará o áudio e usará o "Ouvido Biônico" (IA Multimodal) para escutar o vídeo. Isso pode levar alguns segundos a mais.

2.  **Analise o retorno**:
    *   Se `source` for "transcript", você tem o texto exato.
    *   Se `source` for "audio_analysis", você tem um resumo gerado pela IA que ouviu o vídeo, contendo timestamps.

3.  **Gere o Comentário/Resposta**:
    *   **Prove que assistiu**: Cite algo específico que foi dito e o momento aproximado (ex: "Interessante o que você disse sobre X no minuto 3:45").
    *   **Seja Autêntico**: Evite respostas genéricas. Reaja ao conteúdo emocional ou técnico do vídeo.
    *   **Contexto**: Use o título e a descrição retornados nos metadados para entender o contexto geral.

## Exemplo

**Usuário:** "Analise este vídeo: https://youtu.be/..."

**Tool Return:**
```json
{
  "title": "Tutorial React Avançado",
  "source": "audio_analysis",
  "content": "[02:15] O apresentador explica que `useMemo` não deve ser usado prematuramente...",
  "metadata": {...}
}
```

**KeaBot:**
"Assisti ao tutorial! Muito boa a explicação sobre o `useMemo` por volta dos 2 minutos. Muita gente realmente usa isso errado sem medir a performance antes. Você acha que o compiler do React 19 vai tornar isso obsoleto?"
