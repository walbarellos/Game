````markdown
# ROADMAP.md: Auditoria de Projeto e Prioridades (Pós-Refatoração Arquitetural)

## Status Atual (Pós-Refatoração Core)

A arquitetura de software (separação de camadas, Facade/Mediator, Gerenciamento de Estado) está estável. O foco de desenvolvimento agora muda para **Design de Sistema, Conteúdo e Robustez (CTMU)**.

---

## I. Relatório de Auditoria Crítica: Conteúdo e Design de Sistema

A principal fragilidade do projeto é a falta de conteúdo e o design de jogo incompleto.

| Componente | Status | Problemas de Design/CTMU | Prioridade de Ação (Conteúdo) |
| :--- | :--- | :--- | :--- |
| **Conteúdo (Geral)** | **VAZIO** | Falta de NPCs, Mobs e locais além do inicial, impedindo o engajamento. | **ALTA** (Expansão de Dados) |
| **Fofoca System** | **DEFEITO** | A dica da NPC (Juliana) não se conecta a um NPC alvo ou a uma lógica de *gossip* funcional. | **MÉDIA** (Revisão da Lógica de Diálogo) |
| **Menus/Locais** | **CONFUSO** | Estrutura de navegação incompleta; salas/andares não possuem funções definidas. | **ALTA** (Definição de Escopo de Local) |
| **Recompensa** | **INCOMPLETO** | Recompensa de Combate é apenas XP (falta itens/moeda de jogo). | **MÉDIA** (Implementação de *Loot*) |
| **Base Arquitetural** | **ESTÁVEL** | (Fluxos de estado complexos como `COMBAT` ↔ `LEVEL_UP` resolvidos.) | **ALTA** (Implementar Aleatoriedade do Mob) |

---

## II. Roteiro de Ação e TO-DOs Priorizados

A prioridade imediata é a **Infraestrutura** e a **Expansão de Conteúdo**.

### 1. TO-DOs de Design de Jogo e Dados (Nova Prioridade)

| Tipo | Escopo | Descrição (Ação Técnica) | Arquivo(s) Afetado(s) |
| :--- | :--- | :--- | :--- |
| **feat** | `data/content` | **EXPANSÃO:** Adicionar 3 novos NPCs (com diálogo inicial) e 2 novos Mobs (com recompensas/DC). | `npcs.json`, `mobs.json` |
| **refactor** | `data/locations` | **LIMPEZA:** Definir 3 novos locais/andares (e.g., Arquivo Morto, Café, Almoxarifado) e garantir que cada um tenha pelo menos 1 ação `idle` e 1 NPC. | `locations.json` |
| **fix** | `dialogue/gossip` | **FOFOCA SYSTEM:** Conectar a dica de NPC a uma flag de *gossip* que desbloqueia um diálogo ou quest em outro NPC. | `npcs.json` / `game.py` |
| **fix** | `flow/combat` | **RECOMPENSA:** Implementar a aplicação de XP e `itens` (loot) no `FlowManager.process_combat_victory`. | `flow_manager.py` |

### 2. TO-DOs de Robustez (Lógica Pura)

| Tipo | Escopo | Descrição (Ação Técnica) | Arquivo(s) Afetado(s) |
| :--- | :--- | :--- | :--- |
| **feat** | `combat/mob` | **ALEATORIEDADE:** Adicionar um fator aleatório (d20 ou randrange) ao cálculo de dano do Mob no `process_mob_turn` para quebrar o determinismo. | `flow_manager.py` |
| **feat** | `combat/death` | Implementar lógica de derrota (`process_combat_defeat`) com penalidade (ex: perda de XP ou saúde) antes de retornar ao `MAIN_MENU`. | `flow_manager.py` |
| **test** | `testing` | **CRÍTICO:** Iniciar a escrita de testes unitários para a camada de lógica (`game_logic.py` e `flow_manager.py`). | Novo: `test/` |

### 3. TO-DOs de Infraestrutura e Documentação (Próximo Commit)

| Arquivo | Propósito | Status |
| :--- | :--- | :--- |
| **.gitignore** | Excluir arquivos de ambiente e compilação. | PENDENTE |
| **README.md** | Documentação inicial e Guia de Uso. | PENDENTE |
| **LICENSE** | Licença do código. | PENDENTE |
