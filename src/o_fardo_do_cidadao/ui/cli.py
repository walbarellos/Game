# /home/wepiphany/Game/src/o_fardo_do_cidadao/ui/cli.py
# LIMPO: Manipulador de I/O, Facade/Mediator.
# CORRIGIDO: Adicionadas delegações de menus faltantes (DIALOGUE, OPTIONS).

import time, json, os, sys, random
from o_fardo_do_cidadao.engine.game_logic import perform_skill_check, SuccessTier 
from .ui_manager import UIManager 
from .constants import CLI_Color # Importa a paleta do módulo de constantes

class CommandLineInterface:
    """
    Atua como: 
    1. Camada de Input/Output (I/O). 
    2. Facade/Mediator, traduzindo chamadas de Lógica (FlowManager) para a Apresentação (UIManager).
    """
    def __init__(self, game, quests, locations): # IoC: Recebe quests e locations do Game
        self.game = game
        
        # 1. ARMAZENAMENTO DE DADOS (Injetados pelo Game)
        self.quests = quests
        self.locations = locations
        
        # 2. Cria o Gerenciador de UI 
        # NOTA: O UIManager recebe dados do Game (recipes, npcs, mobs) e do CLI (quests, locations).
        self.ui = UIManager(game, self.quests, self.locations, game.recipes, game.npcs, game.mobs) 

    # --- I/O BÁSICO (CORE RESPONSABILITIES) ---
    
    def clear_screen(self): 
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def prompt_for_input(self, prompt: str) -> str: 
        return input(prompt)
        
    def display_message(self, message: str): 
        print(f"\n>>> {message}"); time.sleep(2)
        
    # --- NOVOS MÉTODOS FACADE/MEDIATOR (Para FlowManager) ---

    def display_idle_header(self, action_name):
        """[FACADE] Exibe o cabeçalho IDLE. Delega a exibição ao UIManager."""
        self.ui._display_idle_header(action_name)

    def log_xp_gain(self, xp_amount):
        """[FACADE] Registra o ganho de XP. Delega a formatação ao UIManager."""
        self.ui.render_xp_gain(xp_amount)

    def display_idle_limit_message(self):
        """[FACADE] Exibe a mensagem de limite de repetições. Delega ao UIManager."""
        self.ui.render_idle_limit_message()

    # --- MÉTODOS DE FLUXO (Delegados para UIManager) ---
    
    def display_main_menu(self):
        """Implementa o menu principal aqui (I/O simples)."""
        self.clear_screen()
        print("="*25 + f" {CLI_Color.CYAN}O FARDO DO CIDADÃO{CLI_Color.ENDC} " + "="*25)
        print("\n[1] Novo Jogo\n[2] Carregar Jogo\n[3] Sair")
        
        choice = self.prompt_for_input("\nEscolha uma opção: ")
        action = {'1': self.game.start_new_game, '2': self.game.load_game, '3': self.game.quit_game}.get(choice)
        
        if action: action()
    
    # Todos os métodos abaixo delegam para a camada UI, cumprindo o padrão Facade.
    def display_game_menu(self): self.ui.display_game_menu()
    def display_options_menu(self): self.ui.display_options_menu() 
    def display_combat_menu(self): self.ui.display_combat_menu() 
    def display_level_up_screen(self): self.ui.display_level_up_screen()
    def display_crafting_menu(self): self.ui.display_crafting_menu()
    def display_quest_board(self): self.ui.display_quest_board()
    def display_travel_menu(self): self.ui.display_travel_menu()
    
    # CORRIGIDO: Adicionado o método de delegação que faltava para DIALOGUE
    def display_dialogue_screen(self): self.ui.display_dialogue_screen() 
    
    # CORRIGIDO: Método de delegação para iniciar o fluxo da quest.
    def run_quest(self, quest_id: str): self.ui.run_quest(quest_id)

    # --- MÉTODOS AUXILIARES E LEGAIS ---
    
    def display_init_log(self, text_blocks: list): self.ui.display_init_log(text_blocks)
    
    # NOTE: 'unlock_quest' foi movido para a lógica de domínio (Game.unlock_quest).
    
    def display_player_status(self): self.ui.display_player_status_bar() 
    def _log_skill_check(self, skill_name: str, attribute_name: str, result): self.ui.log_skill_check(skill_name, attribute_name, result)
    def _run_idle_stage(self, stage_data: dict): self.ui.run_idle_stage(stage_data)
    
    def display_narrative_block(self, text: str):
        self.clear_screen(); print(text); self.prompt_for_input("\nPressione Enter para continuar...")
        
    def _prompt_for_attribute_choice(self, stage_data: dict) -> str:
        # Lógica de I/O para escolha de atributo (mantida no CLI)
        print("Como você pretende abordar a situação?"); possible_attributes = stage_data.get("attributes", [])
        for i, attr in enumerate(possible_attributes): print(f"  [{i + 1}] Usar {attr}")
        while True:
            try:
                choice = int(self.prompt_for_input("Escolha sua abordagem: "));
                if 1 <= choice <= len(possible_attributes): print(); return possible_attributes[choice - 1]
                else: print("Opção inválida.")
            except ValueError: print("Por favor, digite um número.")