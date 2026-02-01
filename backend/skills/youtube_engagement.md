---
name: YouTube Engagement
description: Analisa vídeos do YouTube e gera comentários de engajamento
triggers: ["youtube", "video", "transcrição", "assistir"]
---

# Instruções

Sempre que o usuário fornecer uma URL do YouTube ou pedir para analisar um vídeo:

1.  Use a tool `youtube` para obter os detalhes e a transcrição do vídeo.
2.  Analise o conteúdo da transcrição (resumo, pontos principais, tom).
3.  Gere um comentário que prove que você "assistiu" ao vídeo. O comentário deve:
    *   Mencionar um ponto específico do meio ou fim do vídeo.
    *   Ser construtivo e engajado.
    *   Não soar genérico (evite "Bom vídeo", "Gostei").
    *   Se apropriado, faça uma pergunta sobre o conteúdo.

## Exemplo de fluxo

**Usuário:** "O que você acha desse vídeo? https://youtu.be/..."

**KeaBot:**
1.  Chama `youtube(url="...")`
2.  Lê título e transcrição.
3.  Responde: "Achei a técnica de misturar a farinha aos poucos (mencionada aos 5:00) muito interessante! Isso evita grumos mesmo sem batedeira? Ótimo tutorial."
