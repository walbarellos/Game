# Adiciona a exibição de NPCs no menu e a nova tela de diálogo
import time, json, os
from o_fardo_do_cidadao.engine.game_logic import perform_skill_check, SuccessTier

class CommandLineInterface:
    def __init__(self, game):
        self.game = game
        with open("data/quests.json", "r", encoding="utf-8") as f: self.quests = json.load(f)
        with open("data/locations.json", "r", encoding="utf-8") as f: self.locations = json.load(f)
        with open("data/recipes.json", "r", encoding="utf-8") as f: self.recipes = json.load(f)
        with open("data/npcs.json", "r", encoding="utf-8") as f: self.npcs = json.load(f) # Carrega os NPCs

    def display_game_menu(self):
        self.clear_screen(); location_id = self.game.player.current_location; location = self.locations.get(location_id)
        print(f"Você está em: {location['name']}\n_{location['description']}_"); self.display_player_status()
        options = {}; i = 1
        
        # Lógica para NPCs
        npcs_in_location = [npc_id for npc_id, npc_data in self.npcs.items() if npc_data.get("location") == location_id]
        for npc_id in npcs_in_location:
            options[str(i)] = (f"Falar com {self.npcs[npc_id]['name']}", lambda n=npc_id: self.game.initiate_dialogue(n)); i += 1
            
        ambient_actions = location.get("ambient_actions", []);
        for action_data in ambient_actions:
            options[str(i)] = (action_data["name"], lambda a=action_data: self.game.perform_ambient_action(a)); i += 1
        options[str(i)] = ("Burocracia Aplicada (Fabricar)", self.display_crafting_menu); i += 1
        available_quests = self.get_available_quests(location)
        if available_quests: options[str(i)] = ("Ver Quadro de Avisos", self.display_quest_board); i += 1
        options[str(i)] = ("Viajar", self.display_travel_menu); i += 1
        options[str(i)] = ("Salvar Jogo", self.game.save_game); i += 1
        options[str(i)] = ("Sair para Menu Principal", self.game.return_to_main_menu)
        for key, (text, _) in options.items(): print(f"[{key}] {text}")
        choice = self.prompt_for_input("\nO que você faz? ")
        if choice in options: _, action = options[choice]; action()

    # --- TELA DE DIÁLOGO (NOVA) ---
    def display_dialogue_screen(self):
        self.clear_screen()
        npc = self.game.npcs.get(self.game.dialogue_partner_id)
        node = npc['dialogue_tree'].get(self.game.dialogue_node_id)
        
        print(f"--- Conversando com {npc['name']} ---")
        print(f"_{npc['description']}_")
        self.display_player_status()
        
        print(f"\n{npc['name']} diz: \"{node['text']}\"")
        
        if node.get("is_end", False):
            self.prompt_for_input("\nPressione Enter para continuar...")
            self.game.state = "IN_GAME"
            return

        for i, option in enumerate(node.get('options', [])):
            print(f"  [{i+1}] {option['text']}")
            
        try:
            choice = int(self.prompt_for_input("Sua resposta: ")) - 1
            self.game.process_dialogue_choice(choice)
        except (ValueError, IndexError):
            self.game.process_dialogue_choice(-1) # Envia uma escolha inválida

    # (O resto da classe não muda)
    def display_main_menu(self):
        self.clear_screen(); print("="*25 + " O FARDO DO CIDADÃO " + "="*25); print("\n[1] Novo Jogo\n[2] Carregar Jogo\n[3] Sair")
        choice = self.prompt_for_input("\nEscolha uma opção: ")
        action = {'1': self.game.start_new_game, '2': self.game.load_game, '3': self.game.quit_game}.get(choice)
        if action: action()
    # (Todos os outros métodos permanecem como na última versão)
    def display_crafting_menu(self):
        self.clear_screen(); print("--- Mesa de Burocracia Aplicada ---"); self.display_player_status()
        recipes = list(self.recipes.keys())
        for i, recipe_id in enumerate(recipes):
            recipe = self.recipes[recipe_id]
            can_craft_str = "✓" if self.game.player.tem_itens(recipe['ingredients']) else "✗"
            print(f"[{i+1}] {recipe['name']} {can_craft_str}")
        try:
            choice = int(self.prompt_for_input("Fabricar o quê? (0 para voltar) "))
            if 1 <= choice <= len(recipes): self.game.perform_crafting(list(self.recipes.keys())[choice - 1])
        except ValueError: pass
    def display_level_up_screen(self):
        self.clear_screen()
        while self.game.player.pontos_de_aprimoramento > 0:
            print("="*20 + " LEVEL UP! " + "="*20); self.display_player_status()
            print(f"Você tem {self.game.player.pontos_de_aprimoramento} ponto(s) para gastar.\n\nO que você deseja aprimorar?")
            options = list(self.game.player.attributes.keys()) + list(self.game.player.skills.keys())
            for i, option in enumerate(options): print(f"  [{i+1}] {option.title()}")
            try:
                choice = int(self.prompt_for_input("Escolha uma opção: "))
                if 1 <= choice <= len(options): self.game.player.gastar_ponto_aprimoramento(options[choice - 1])
                else: self.display_message("Opção inválida.")
            except (ValueError, IndexError): self.display_message("Entrada inválida.")
        self.display_message("Todos os pontos foram gastos..."); self.game.state = "IN_GAME"
    def run_quest(self, quest_id: str):
        quest = self.quests.get(quest_id); current_stage_id = quest.get("start_stage", "1"); journal = self.game.player.quest_journal
        journal['ativas'].append(quest_id); mission_success = True; total_xp_gain = 0; final_stage_id = ""
        while current_stage_id:
            final_stage_id = current_stage_id; stage = quest['stages'].get(current_stage_id)
            if not stage: print(f"ERRO: Etapa '{current_stage_id}' não encontrada."); break
            print("-" * 70); self.display_player_status(); print(f"\n> {stage['description']}")
            stage_type = stage.get("type")
            if stage_type == 'idle': self._run_idle_stage(stage); current_stage_id = stage.get("next_stage")
            elif stage_type == 'skill_check':
                chosen_attribute = self._prompt_for_attribute_choice(stage)
                result = perform_skill_check(self.game.player, stage['skill'], chosen_attribute, stage['dc'])
                total_xp_gain += result.xp_gain
                if not result.success: mission_success = False
                current_stage_id = stage.get("on_success") if result.success else stage.get("on_failure")
            elif stage_type == 'morality_choice':
                options = stage.get("options", {}); choice_keys = list(options.keys())
                print("Sua decisão é crucial. O que você faz?")
                for i, key in enumerate(choice_keys): print(f"  [{i+1}] {key.title()}")
                try:
                    choice = int(self.prompt_for_input("Escolha seu caminho: "))
                    if 1 <= choice <= len(choice_keys):
                        chosen_key = choice_keys[choice - 1]; chosen_option = options[chosen_key]
                        effect = chosen_option.get("effect", {})
                        if "reputation_change" in effect:
                            # Formato esperado: {"faccao": "nome", "valor": -2}
                            rep_change = effect["reputation_change"]
                            self.game.player.alterar_reputacao(rep_change["faccao"], rep_change["valor"])
                        if "xp" in effect: self.game.process_xp_gain(effect["xp"])
                        if "composure_heal" in effect: self.game.player.aplicar_cura_compostura(effect["composure_heal"])
                        current_stage_id = chosen_option.get("result")
                    else: self.display_message("Escolha inválida. O momento passou."); current_stage_id = None
                except ValueError: self.display_message("Você hesita demais. A oportunidade se foi."); current_stage_id = None
            elif stage_type == 'narrative': current_stage_id = stage.get("next_stage")
            if stage.get("is_end"): break
        journal['ativas'].remove(quest_id); final_stage = quest['stages'].get(final_stage_id, {})
        if "unlocks_quest" in final_stage:
            unlocked_quest_id = final_stage["unlocks_quest"]; unlocked_list = journal.get('unlocked_quests', [])
            if unlocked_quest_id not in unlocked_list:
                unlocked_list.append(unlocked_quest_id); journal['unlocked_quests'] = unlocked_list
                self.display_message(f"Nova missão desbloqueada: {self.quests[unlocked_quest_id]['title']}")
        print("-" * 70)
        if mission_success:
            journal['completas'][quest_id] = "success"; print(f"\n--- MISSÃO '{quest['title']}' CONCLUÍDA COM SUCESSO ---")
            total_xp_gain += quest.get("xp_reward", 0)
        else:
            journal['completas'][quest_id] = "failure"; print(f"\n--- A MISSÃO '{quest['title']}' TERMINOU EM FRACASSO ---")
        self.game.process_xp_gain(total_xp_gain); self.display_player_status()
        if self.game.state != "LEVEL_UP": self.prompt_for_input("\nPressione Enter para retornar...")
    def display_quest_board(self):
        location = self.locations.get(self.game.player.current_location); available_quests = self.get_available_quests(location)
        print("\n--- Quadro de Avisos ---")
        for i, quest_id in enumerate(available_quests): print(f"[{i+1}] {self.quests[quest_id]['title']}")
        try:
            choice = int(self.prompt_for_input("Aceitar qual missão? (0 para voltar) "))
            if 1 <= choice <= len(available_quests): self.run_quest(available_quests[choice-1])
        except ValueError: pass
    def display_travel_menu(self):
        location = self.locations.get(self.game.player.current_location); travel_options = location.get("travel_to", [])
        print("\n--- Viajar Para ---")
        for i, location_id in enumerate(travel_options): print(f"[{i+1}] {self.locations[location_id]['name']}")
        try:
            choice = int(self.prompt_for_input("Para onde? (0 para voltar) "))
            if 1 <= choice <= len(travel_options): self.game.travel_to(travel_options[choice-1])
        except ValueError: pass
    def get_available_quests(self, location: dict) -> list:
        journal = self.game.player.quest_journal; location_quests = location.get("quests", [])
        all_possible_quests = set(location_quests + journal.get('unlocked_quests', []))
        return [q_id for q_id in all_possible_quests if q_id not in journal['ativas'] and q_id not in journal['completas'].keys()]
    def display_message(self, message: str): print(f"\n>>> {message}"); time.sleep(2)
    def prompt_for_input(self, prompt: str) -> str: return input(prompt)
    def _prompt_for_attribute_choice(self, stage_data: dict) -> str:
        print("Como você pretende abordar a situação?"); possible_attributes = stage_data.get("attributes", [])
        for i, attr in enumerate(possible_attributes): print(f"  [{i + 1}] Usar {attr}")
        while True:
            try:
                choice = int(input("Escolha sua abordagem: "));
                if 1 <= choice <= len(possible_attributes): print(); return possible_attributes[choice - 1]
                else: print("Opção inválida.")
            except ValueError: print("Por favor, digite um número.")
    def _run_idle_stage(self, stage_data: dict):
        duration = stage_data.get('duration_seconds', 1)
        for i in range(duration + 1):
            time.sleep(0.1); progress = i / duration
            bar = '█' * int(30 * progress) + '-' * (30 - int(30 * progress))
            print(f'\rProgresso: |{bar}| {int(progress * 100)}%', end='');
        print("\n...Concluído.")
    def display_player_status(self):
        if self.game.player: print(self.game.player)
    def clear_screen(self): os.system('cls' if os.name == 'nt' else 'clear')
    def display_narrative_block(self, text: str):
        self.clear_screen(); print(text); self.prompt_for_input("\nPressione Enter para continuar...")