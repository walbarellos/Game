# /home/wepiphany/Game/src/o_fardo_do_cidadao/engine/game.py
# CORRIGIDO: Implementação do gerenciamento de estado anterior (previous_state) para Level Up.

import json, os, sys, random
from o_fardo_do_cidadao.core.character import Character
from o_fardo_do_cidadao.ui.cli import CommandLineInterface
from o_fardo_do_cidadao.engine.game_logic import perform_skill_check
from .flow_manager import FlowManager 

SAVE_FILE = "savegame.json"

class Game:
    def __init__(self):
        # ESTADOS E PROPRIEDADES (Inicialização)
        self.state = "MAIN_MENU"
        self.possible_states = ["MAIN_MENU", "IN_GAME", "LEVEL_UP", "DIALOGUE", "IDLE_GRIND", "OPTIONS_MENU", "COMBAT"] 
        self.player: Character | None = None
        
        # ADICIONADO: Variável para armazenar o estado que levou ao Level Up
        self.previous_state = "MAIN_MENU"
        
        # 1. CARREGAMENTO CRÍTICO DE DADOS (PRIORIDADE - CENTRALIZAÇÃO)
        with open("data/recipes.json", "r", encoding="utf-8") as f: self.recipes = json.load(f)
        with open("data/npcs.json", "r", encoding="utf-8") as f: self.npcs = json.load(f)
        with open("data/mobs.json", "r", encoding="utf-8") as f: self.mobs = json.load(f)
        with open("data/quests.json", "r", encoding="utf-8") as f: self.quests = json.load(f)
        with open("data/locations.json", "r", encoding="utf-8") as f: self.locations = json.load(f)
        
        self.dialogue_partner_id = None
        self.dialogue_node_id = None
        self.current_mob = None 
        
        # 2. CRIAÇÃO DA INTERFACE E FLUXO (Inversão de Controle - IoC)
        self.cli = CommandLineInterface(self, self.quests, self.locations) 
        self.flow = FlowManager(self)


    def run(self):
        while True:
            if self.state == "MAIN_MENU": self.cli.display_main_menu()
            elif self.state == "IN_GAME": self.cli.display_game_menu()
            elif self.state == "IDLE_GRIND": self.flow.run_idle_loop() 
            elif self.state == "LEVEL_UP": self.cli.display_level_up_screen()
            elif self.state == "DIALOGUE": self.cli.display_dialogue_screen()
            elif self.state == "OPTIONS_MENU": self.cli.display_options_menu()
            elif self.state == "COMBAT": self.cli.display_combat_menu()

    # --- MÉTODOS DE DIÁLOGO ---
    def initiate_dialogue(self, npc_id: str):
        self.dialogue_partner_id = npc_id
        npc = self.npcs.get(npc_id)
        
        cooldown_flag = f"{npc_id}_talked"
        if self.player.game_flags.get(cooldown_flag):
            self.dialogue_node_id = npc.get("dialogue_cooldown", "start")
        else:
            self.dialogue_node_id = "start"
            self.player.game_flags[cooldown_flag] = True

        self.state = "DIALOGUE"

    def process_dialogue_choice(self, choice_index: int):
        npc = self.npcs.get(self.dialogue_partner_id)
        node = npc['dialogue_tree'].get(self.dialogue_node_id)
        
        if 0 <= choice_index < len(node['options']):
            choice = node['options'][choice_index]
            next_node_id = choice.get('leads_to')
            
            if next_node_id == "end":
                self.state = "IN_GAME"
            else:
                self.dialogue_node_id = next_node_id
                
                next_node = npc['dialogue_tree'].get(next_node_id, {})
                effect = next_node.get('effect')
                if effect:
                    if "fragmento_lore" in effect: self.cli.display_message(f"Você descobriu: {effect['fragmento_lore']}")
                    if "xp" in effect: self.process_xp_gain(effect['xp'])
                    if "reputation_change" in effect:
                        rep_change = effect["reputation_change"]
                        self.player.alterar_reputacao(rep_change["faccao"], rep_change["valor"])
        else:
            self.cli.display_message("Escolha de diálogo inválida.")

    # --- NOVO MÉTODO: Lógica de Domínio Pura (Chamado pelo FlowManager) ---
    def unlock_quest(self, quest_id: str):
        """Adiciona uma quest à lista de desbloqueadas do jogador e notifica a UI."""
        if self.player:
            journal = self.player.quest_journal
            if quest_id not in journal.get('unlocked_quests', []):
                journal['unlocked_quests'].append(quest_id)
                # O Game notifica o CLI (Facade) para exibir a mensagem.
                self.cli.display_message(f"Novo Protocolo '{quest_id}' desbloqueado!")

    # --- MÉTODOS DE AÇÃO (DELEGADOS AO FLOW MANAGER) ---
    def perform_ambient_action(self, action_data: dict):
        self.flow.perform_ambient_action(action_data)
        
    def perform_crafting(self, recipe_id: str):
        self.flow.perform_crafting(recipe_id)

    # --- MÉTODO: INICIAR COMBATE ---
    def initiate_combat(self, mob_id: str):
        self.current_mob = self.mobs.get(mob_id)
        if not self.current_mob:
            self.cli.display_message("Erro: Inimigo desconhecido. Retornando ao menu.")
            self.state = "IN_GAME"
            return
        
        # Inicializa a saúde do mob para o combate
        self.current_mob['saude_atual'] = self.current_mob['saude_maxima']
        self.state = "COMBAT"
        self.cli.display_message(f"--- COMBATE INICIADO: {self.current_mob['name']} apareceu! ---")
    
    # --- MÉTODO: PROCESSAR DANO NO MOB ---
    def process_mob_damage(self, damage: int):
        if not self.current_mob: return
        self.current_mob['saude_atual'] = max(0, self.current_mob['saude_atual'] - damage)
        if self.current_mob['saude_atual'] <= 0:
            self.flow.process_combat_victory(self.current_mob)
        
    # --- MÉTODOS DE CONTROLE ---
    def start_new_game(self):
        self.cli.clear_screen(); player_name = self.cli.prompt_for_input("Digite o nome do seu cidadão: ")
        self.player = Character(name=player_name)
        
        intro_log = [
            "Iniciando processo de cadastro...", "Processo de contratação concluído.",
            "Conectando ao Setor de Protocolo Distrital 42...",
            "Seu novo chefe, Chefe de Setor Valdemar, aproxima-se.",
            ">>> 'Olha aqui, novato... Se vira... Não me decepcione.'",
            "Ele bate a porta, deixando você sozinho."
        ]
        self.cli.display_init_log(intro_log)
        self.state = "IN_GAME"
    
    def process_xp_gain(self, xp_amount: int):
        if self.player and self.player.adicionar_experiencia(xp_amount):
            # CORRIGIDO: Armazena o estado atual (COMBAT) antes de mudar para LEVEL_UP
            self.previous_state = self.state 
            self.state = "LEVEL_UP"
    
    def travel_to(self, location_id: str):
        if self.player: self.player.current_location = location_id

    def save_game(self):
        if self.player:
            self.player.game_flags['idle_mode'] = False 
            with open(SAVE_FILE, "w", encoding="utf-8") as f: json.dump(self.player.to_dict(), f, indent=4, ensure_ascii=False)
            self.cli.display_message("Jogo salvo com sucesso!")
        else: self.cli.display_message("Erro: Nenhum jogo ativo para salvar.")
        
    def load_game(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r", encoding="utf-8") as f: self.player = Character.from_dict(json.load(f))
            self.state = "IN_GAME"; self.cli.clear_screen(); self.cli.display_message(f"Bem-vindo de volta, {self.player.name}.")
        else: self.cli.display_message("Nenhum jogo salvo encontrado.")
        
    def return_to_main_menu(self):
        if self.player: self.player.game_flags['idle_mode'] = False 
        self.player = None; self.state = "MAIN_MENU"
        
    def quit_game(self):
        self.cli.display_message("O fardo é eterno... até a próxima."); sys.exit()