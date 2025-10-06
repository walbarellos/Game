#!/bin/bash
# ==============================================================================
# SCRIPT DE INSTALAÇÃO DEFINITIVO: O FARDO DO CIDADÃO
# OBJETIVO: Limpar o diretório atual e criar a estrutura correta do projeto.
# EXECUÇÃO: Deve ser executado de dentro da pasta raiz do projeto (ex: ~/Game).
# ==============================================================================

# Encerra o script imediatamente se qualquer comando falhar.
set -e

echo "--- OPERAÇÃO LIMPEZA FINAL ---"
echo "INFO: Limpando o diretório atual para uma instalação limpa..."

# Apaga estruturas antigas para evitar conflitos.
rm -rf data docs o_fardo_do_cidadao src tests README.md .gitignore

echo "INFO: Estrutura antiga removida."
echo "INFO: Criando a estrutura de diretórios correta..."

# --- 1. Cria a Estrutura de Pastas ---
mkdir -p data
mkdir -p docs
mkdir -p tests
mkdir -p src/o_fardo_do_cidadao/core
mkdir -p src/o_fardo_do_cidadao/engine
mkdir -p src/o_fardo_do_cidadao/ui

echo "INFO: Preenchendo os arquivos do projeto..."

# --- 2. Cria Arquivos de Configuração e Dados ---
cat << EOF > .gitignore
__pycache__/
*.pyc
venv/
.venv/
EOF

cat << EOF > README.md
# O Fardo do Cidadão
RPG Idle Guiado pela Narrativa.
EOF

cat << EOF > data/quests.json
{
  "q001_protocolar_formulario": {
    "title": "Protocolar o Formulário A-38",
    "description": "Um burocrata exige que você protocole o Formulário A-38.",
    "stages": {
      "1": {
        "type": "idle",
        "description": "Aguardar na fila da repartição.",
        "duration_seconds": 10
      },
      "2": {
        "type": "skill_check",
        "description": "O atendente parece cético quanto à validade do seu selo. Você precisa convencê-lo.",
        "skill": "Burocracia",
        "dc": 12,
        "attributes": ["Presença", "Raciocínio", "Poder"]
      }
    }
  }
}
EOF

# --- 3. Cria os Módulos Python com o Último Código ---

# Arquivos __init__.py para transformar os diretórios em pacotes
touch src/o_fardo_do_cidadao/__init__.py
touch src/o_fardo_do_cidadao/core/__init__.py
touch src/o_fardo_do_cidadao/engine/__init__.py
touch src/o_fardo_do_cidadao/ui/__init__.py

# character.py
cat << EOF > src/o_fardo_do_cidadao/core/character.py
import math

class Character:
    def __init__(self, name: str):
        self.name = name
        self.attributes = {
            "Poder": 10, "Agilidade": 10, "Fortitude": 10,
            "Raciocínio": 10, "Intuição": 10, "Presença": 10
        }
        self.skills = {"Burocracia": 1}
        self.inventory = {"Permissões": [], "Recursos": {}}
        self.quest_journal = {"ativas": [], "completas": []}
        self.status_effects = []
        self._initialize_derived_stats()

    @property
    def saude_maxima(self) -> int:
        return (self.attributes.get("Fortitude", 10) * 10) + (self.attributes.get("Poder", 10) * 2)

    @property
    def compostura_maxima(self) -> int:
        return (self.attributes.get("Fortitude", 10) * 5) + (self.attributes.get("Presença", 10) * 5)

    def _initialize_derived_stats(self):
        self.saude_atual = self.saude_maxima
        self.compostura_atual = self.compostura_maxima

    def get_attribute_modifier(self, attribute_name: str) -> int:
        return math.floor((self.attributes.get(attribute_name, 10) - 10) / 2)

    def get_skill_bonus(self, skill_name: str) -> int:
        return self.skills.get(skill_name, 0)

    def apply_composure_damage(self, amount: int):
        self.compostura_atual = max(0, self.compostura_atual - amount)
        print(f"\\nSua compostura foi abalada! [-{amount}] -> Atual: {self.compostura_atual}/{self.compostura_maxima}")
        if self.compostura_atual == 0:
            print("Você está no seu limite. A frustração toma conta.")
            self.status_effects.append("Frustrado")

    def __str__(self) -> str:
        header = f"--- Cidadão: {self.name} ---"
        status = (f"Saúde: {self.saude_atual}/{self.saude_maxima} | "
                  f"Compostura: {self.compostura_atual}/{self.compostura_maxima}")
        effects = f"Efeitos: {self.status_effects if self.status_effects else 'Nenhum'}"
        return f"\\n{header}\\n{status}\\n{effects}"
EOF

# game_logic.py
cat << EOF > src/o_fardo_do_cidadao/engine/game_logic.py
import random
from collections import namedtuple
from o_fardo_do_cidadao.core.character import Character

SkillCheckResult = namedtuple("SkillCheckResult", ["success", "margin"])

def perform_skill_check(character: Character, skill: str, attribute: str, dc: int) -> SkillCheckResult:
    roll = random.randint(1, 20)
    modifier = character.get_attribute_modifier(attribute)
    bonus = character.get_skill_bonus(skill)
    total = roll + modifier + bonus
    margin = total - dc
    success = margin >= 0

    print(f"Teste de {skill} ({attribute}): Rolagem={roll}, Mod={modifier}, Bônus={bonus} -> Total={total} vs CD={dc}")

    if not success:
        composure_damage = abs(margin)
        character.apply_composure_damage(composure_damage)

    return SkillCheckResult(success=success, margin=margin)
EOF

# cli.py
cat << EOF > src/o_fardo_do_cidadao/ui/cli.py
import time
import json
import os
from o_fardo_do_cidadao.core.character import Character
from o_fardo_do_cidadao.engine.game_logic import perform_skill_check

class CommandLineInterface:
    def __init__(self):
        self.player = None
        with open("data/quests.json", "r", encoding="utf-8") as f:
            self.quests = json.load(f)

    def start_game(self):
        self.clear_screen()
        print("="*25 + " O FARDO DO CIDADÃO " + "="*25)
        self.player = Character(name=input("Digite o nome do seu cidadão: "))
        self.run_quest("q001_protocolar_formulario")

    def run_quest(self, quest_id: str):
        quest = self.quests.get(quest_id)
        print(f"\\n[MISSÃO] {quest['title']}\\n{quest['description']}")
        mission_success = True
        for _, stage in sorted(quest['stages'].items()):
            print("-" * 70)
            self._display_player_status()
            print(f"\\n> {stage['description']}")
            if stage['type'] == 'idle':
                self._run_idle_stage(stage)
            elif stage['type'] == 'skill_check':
                chosen_attribute = self._prompt_for_attribute_choice(stage)
                result = perform_skill_check(self.player, stage['skill'], chosen_attribute, stage['dc'])
                if not result.success:
                    mission_success = False
                    print("\\nSua abordagem falhou...")
                    break
        print("-" * 70)
        if mission_success:
            print("\\n--- MISSÃO CONCLUÍDA COM SUCESSO ---")
        else:
            print("\\n--- A MISSÃO TERMINOU EM FRACASSO ---")
        self._display_player_status()

    def _prompt_for_attribute_choice(self, stage_data: dict) -> str:
        print("Como você pretende abordar a situação?")
        possible_attributes = stage_data.get("attributes", [])
        for i, attr in enumerate(possible_attributes):
            print(f"  [{i + 1}] Usar {attr}")
        while True:
            try:
                choice = int(input("Escolha sua abordagem: "))
                if 1 <= choice <= len(possible_attributes):
                    return possible_attributes[choice - 1]
                else:
                    print("Opção inválida.")
            except ValueError:
                print("Por favor, digite um número.")

    def _run_idle_stage(self, stage_data: dict):
        duration = stage_data['duration_seconds']
        for i in range(duration + 1):
            time.sleep(0.1)
            progress = i / duration
            bar = '█' * int(30 * progress) + '-' * (30 - int(30 * progress))
            print(f'\\rProgresso: |{bar}| {int(progress * 100)}%', end='')
        print("\\n...Concluído.")
    
    def _display_player_status(self):
        if self.player:
            print(self.player)

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
EOF

# main.py
cat << EOF > src/o_fardo_do_cidadao/main.py
import sys
import os

# Adiciona o diretório 'src' ao path para garantir que os módulos sejam encontrados
# ao executar como script.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from o_fardo_do_cidadao.ui.cli import CommandLineInterface

def main():
    """Ponto de entrada principal da aplicação."""
    CommandLineInterface().start_game()

if __name__ == "__main__":
    main()
EOF

# --- 4. Finalização ---
echo ""
echo "--- SUCESSO ---"
echo "O projeto foi criado e preenchido corretamente."
echo "Para executar o jogo, use o comando:"
echo "python3 src/o_fardo_do_cidadao/main.py"
echo "----------------"