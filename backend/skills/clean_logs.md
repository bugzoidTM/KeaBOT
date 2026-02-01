# 🧹 Skill: Limpeza de Arquivos de Logs

## Objetivo
Esta skill ensina você a encontrar e remover arquivos `.log` antigos de forma segura.

## Fluxo de Trabalho

### Passo 1: Identificar Arquivos de Log

Primeiro, liste os arquivos `.log` no diretório especificado:

```
Ação: list_directory(path=".", depth=2, pattern="*.log")
```

### Passo 2: Verificar Tamanho e Data

Para cada arquivo encontrado, verifique os metadados:

```
Ação: file_stats(path="caminho/do/arquivo.log")
```

**Critérios para exclusão:**
- Arquivos maiores que 10MB
- Arquivos não modificados há mais de 7 dias
- Arquivos em pastas `logs/`, `temp/`, ou `cache/`

### Passo 3: Confirmar com o Usuário

⚠️ **IMPORTANTE**: Antes de deletar qualquer arquivo, SEMPRE liste o que será removido e peça confirmação:

```
🔍 Encontrei os seguintes arquivos de log antigos:

1. logs/app.log (45MB, modificado há 15 dias)
2. temp/debug.log (12MB, modificado há 30 dias)
3. cache/requests.log (8MB, modificado há 10 dias)

Total: 65MB serão liberados.

❓ Deseja que eu remova esses arquivos? (Responda "sim" para confirmar)
```

### Passo 4: Executar Limpeza

Após confirmação, use a ferramenta de shell para remover:

```
Ação: (Solicitar aprovação do usuário para comandos de exclusão)
```

## Exemplos de Uso

### Exemplo 1: Usuário pede para limpar logs
**Usuário**: "Limpa os logs antigos do projeto"

**Você deve**:
1. `list_directory(".", 3, "*.log")` para encontrar arquivos
2. `file_stats()` para cada arquivo relevante
3. Apresentar lista ao usuário
4. Aguardar confirmação antes de deletar

### Exemplo 2: Busca específica
**Usuário**: "Quais logs estão ocupando mais espaço?"

**Você deve**:
1. Listar todos os .log com `list_directory`
2. Verificar tamanho de cada um com `file_stats`
3. Ordenar por tamanho e apresentar top 10

## Regras de Segurança

1. ❌ NUNCA delete arquivos sem confirmação
2. ❌ NUNCA delete arquivos fora da pasta permitida
3. ✅ Sempre mostre preview do que será deletado
4. ✅ Calcule espaço que será liberado
5. ✅ Mantenha arquivos .log modificados nos últimos 24h