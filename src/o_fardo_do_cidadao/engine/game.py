# Adiciona o estado de DIALOGUE e os métodos para controlar a conversa
import json, os, sys, random
from o_fardo_do_cidadao.core.character import Character
from o_fardo_do_cidadao.ui.cli import CommandLineInterface
from o_fardo_do_cidadao.engine.game_logic import perform_skill_check

SAVE_FILE = "savegame.json"

class Game:
    def __init__(self):
        self.cli = CommandLineInterface(self); self.state = "MAIN_MENU"; self.player: Character | None = None
        with open("data/recipes.json", "r", encoding="utf-8") as f: self.recipes = json.load(f)
        with open("data/npcs.json", "r", encoding="utf-8") as f: self.npcs = json.load(f) # Carrega os NPCs
        self.dialogue_partner_id = None # Guarda com quem estamos falando
        self.dialogue_node_id = None # Guarda em que parte da conversa estamos

    def run(self):
        while True:
            if self.state == "MAIN_MENU": self.cli.display_main_menu()
            elif self.state == "IN_GAME": self.cli.display_game_menu()
            elif self.state == "LEVEL_UP": self.cli.display_level_up_screen()
            elif self.state == "DIALOGUE": self.cli.display_dialogue_screen() # NOVO estado de jogo

    # --- MÉTODOS DE DIÁLOGO (NOVOS) ---
    def initiate_dialogue(self, npc_id: str):
        """Inicia uma conversa com um NPC."""
        self.dialogue_partner_id = npc_id
        self.dialogue_node_id = "start" # Toda conversa começa no nó "start"
        self.state = "DIALOGUE"

    def process_dialogue_choice(self, choice_index: int):
        """Processa a escolha do jogador no diálogo e avança a conversa."""
        npc = self.npcs.get(self.dialogue_partner_id)
        node = npc['dialogue_tree'].get(self.dialogue_node_id)
        
        if 0 <= choice_index < len(node['options']):
            choice = node['options'][choice_index]
            next_node_id = choice.get('leads_to')
            
            if next_node_id == "end":
                self.state = "IN_GAME" # Volta ao menu do jogo
            else:
                self.dialogue_node_id = next_node_id
                
                # Aplica efeitos, se houver, no nó para onde vamos
                next_node = npc['dialogue_tree'].get(next_node_id, {})
                effect = next_node.get('effect')
                if effect:
                    if "lore_snippet" in effect: self.cli.display_message(f"Você descobriu: {effect['lore_snippet']}")
                    if "xp" in effect: self.process_xp_gain(effect['xp'])
                    # Adicionar outros efeitos aqui
        else:
            self.cli.display_message("Escolha de diálogo inválida.")

    # (O resto da classe não muda)
    def perform_ambient_action(self, action_data: dict):
        self.cli.clear_screen(); print(f"--- {action_data['name']} ---"); self.cli.display_player_status(); print(f"_{action_data.get('description', '')}_")
        action_type = action_data.get("type"); xp_gain = 0
        if action_type == "idle":
            self.cli._run_idle_stage(action_data); reward = action_data.get("reward", {})
            if "xp" in reward: xp_gain += reward["xp"]
            if "composure_heal" in reward: self.player.aplicar_cura_compostura(reward["composure_heal"])
            if action_data.get('id') == 'organizar_arquivos': self.player.game_flags['arquivos_organizados'] = self.player.game_flags.get('arquivos_organizados', 0) + 1; print("Seu conhecimento sobre a desordem local aumentou.")
        elif action_type == "skill_check":
            result = perform_skill_check(self.player, action_data['skill'], action_data['skill'], action_data['dc']); xp_gain += result.xp_gain
            if result.success:
                reward = action_data.get("on_success", {})
                if "item_found" in reward: self.player.adicionar_item(reward["item_found"])
                if "lore_snippet" in reward: self.cli.display_message(f"Você descobriu um segredo: {reward['lore_snippet']}")
        elif action_type == "random_event":
            outcomes = action_data.get("outcomes", []); roll = random.random(); cumulative_chance = 0; chosen_outcome = None
            for outcome in outcomes:
                cumulative_chance += outcome.get("chance", 0)
                if roll < cumulative_chance: chosen_outcome = outcome; break
            if chosen_outcome:
                effect = chosen_outcome.get("effect", {})
                if "description" in effect: self.cli.display_message(effect["description"])
                if "xp" in effect: xp_gain += effect["xp"]
                if "item_reward" in effect: self.player.adicionar_item(effect["item_reward"])
                if "composure_damage" in effect: self.player.apply_composure_damage(effect["composure_damage"])
            else: self.cli.display_message("Nada de interessante acontece.")
        self.process_xp_gain(xp_gain); self.cli.prompt_for_input("\nPressione Enter para continuar...")
    def perform_crafting(self, recipe_id: str):
        recipe = self.recipes.get(recipe_id)
        if not recipe: self.cli.display_message("Receita inválida."); return
        self.cli.clear_screen(); print(f"--- Tentando Fabricar: {recipe['name']} ---"); print(f"_{recipe['description']}_"); self.cli.display_player_status()
        if not self.player.tem_itens(recipe['ingredients']): self.cli.display_message("Você não tem os ingredientes necessários."); return
        print("\nRealizando o teste de fabricação..."); check_data = recipe['skill_check']
        result = perform_skill_check(self.player, check_data['skill'], check_data['skill'], check_data['dc'])
        if result.success:
            self.player.consumir_itens(recipe['ingredients']); output = recipe['output']
            self.player.adicionar_item(output['item_id'], output['quantidade']); self.cli.display_message("Fabricação bem-sucedida!")
        else: self.cli.display_message("Você falhou. Os materiais parecem intactos... por enquanto.")
        self.process_xp_gain(result.xp_gain); self.cli.prompt_for_input("\nPressione Enter para continuar...")
    def start_new_game(self):
        self.cli.clear_screen(); player_name = self.cli.prompt_for_input("Digite o nome do seu cidadão: ")
        self.player = Character(name=player_name)
        intro_text = "Você é o mais novo contratado...\nSeu novo chefe, Chefe de Setor Valdemar...\n'Olha aqui, novato... Se vira... Não me decepcione.'\nEle bate a porta..."
        self.cli.display_narrative_block(intro_text); self.state = "IN_GAME"
    def process_xp_gain(self, xp_amount: int):
        if self.player and self.player.adicionar_experiencia(xp_amount): self.state = "LEVEL_UP"
    def save_game(self):
        if self.player:
            with open(SAVE_FILE, "w", encoding="utf-8") as f: json.dump(self.player.to_dict(), f, indent=4, ensure_ascii=False)
            self.cli.display_message("Jogo salvo com sucesso!")
        else: self.cli.display_message("Erro: Nenhum jogo ativo para salvar.")
    def load_game(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r", encoding="utf-8") as f: self.player = Character.from_dict(json.load(f))
            self.state = "IN_GAME"; self.cli.clear_screen(); self.cli.display_message(f"Bem-vindo de volta, {self.player.name}.")
        else: self.cli.display_message("Nenhum jogo salvo encontrado.")
    def travel_to(self, location_id: str):
        if self.player: self.player.current_location = location_id
    def return_to_main_menu(self):
        self.player = None; self.state = "MAIN_MENU"
    def quit_game(self):
        self.cli.display_message("O fardo é eterno... até a próxima."); sys.exit()