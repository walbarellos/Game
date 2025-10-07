# /home/wepiphany/Game/src/o_fardo_do_cidadao/ui/ui_manager.py

import time
from o_fardo_do_cidadao.engine.game_logic import SuccessTier 
from .constants import CLI_Color # Importa a paleta de cores

class UIManager:
    """
    Responsável unicamente pela Apresentação: Layout, formatação, cores e menus.
    Acessa constantes de cor diretamente do namespace do módulo.
    """
    def __init__(self, game, quests, locations, recipes, npcs, mobs):
        self.game = game
        self.quests = quests
        self.locations = locations
        self.recipes = recipes
        self.npcs = npcs
        self.mobs = mobs

    # --- LAYOUT E STATUS (Métodos Base) ---

    def _display_location_header(self, location: dict):
        """Exibe o cabeçalho da localização."""
        self.game.cli.clear_screen()
        print("="*20 + f" {CLI_Color.CYAN}DISTRITO 42{CLI_Color.ENDC} " + "="*20)
        print(f"{CLI_Color.CYAN}Local:{CLI_Color.ENDC} {location['name']}")
        print(f"_{location['description']}_")

    def _display_idle_header(self, action_name: str):
        """Exibe o cabeçalho do modo Grind Automático (Chamado pelo CLI Facade)."""
        self.game.cli.clear_screen()
        print(f"--- {CLI_Color.CYAN}GRIND AUTOMÁTICO: {action_name}{CLI_Color.ENDC} ---")

    def display_player_status_bar(self):
        """Exibe a barra de status concisa do jogador."""
        player = self.game.player
        health_color = CLI_Color.RED if player.saude_atual <= player.saude_maxima * 0.3 else CLI_Color.GREEN
        
        print(f"\n--- {CLI_Color.YELLOW}ESTADO DE CARREIRA{CLI_Color.ENDC} ---")
        print(f"Nome: {player.name} (Nvl {player.level})")
        print(f"Saúde: {health_color}{player.saude_atual}/{player.saude_maxima}{CLI_Color.ENDC}")
        print(f"XP: {player.xp_atual}/{player.xp_para_proximo_nivel}")
        
        warnings = []
        if player.game_flags.get('arquivos_organizados', 0) > 0:
            warnings.append(f"Arquivos Organizados: {player.game_flags['arquivos_organizados']}")
        if warnings:
            print(f"{CLI_Color.YELLOW}Avisos:{CLI_Color.ENDC} {' | '.join(warnings)}")
        print("-" * 50)
        
    def display_current_objective(self):
        """Exibe o protocolo ativo ou a sugestão de objetivo (FOCO)."""
        player = self.game.player
        active_quests = player.quest_journal.get('ativas', [])
        
        if active_quests:
            quest_id = active_quests[0]
            quest = self.quests.get(quest_id)
            current_stage_key = quest.get('start_stage', '1')
            
            print(f"\n{CLI_Color.YELLOW}>> PROTOCOLO ATIVO: {CLI_Color.ENDC}{CLI_Color.CYAN}{quest['title']}{CLI_Color.ENDC}")
            description = quest['stages'].get(current_stage_key, {}).get('description', 'Erro na Etapa.')
            print(f"{CLI_Color.CYAN}  - ETAPA: {current_stage_key} - {description}{CLI_Color.ENDC}") 
            
        else:
            print(f"\n{CLI_Color.CYAN}>> FOCO:{CLI_Color.ENDC} {CLI_Color.YELLOW}Sem Protocolo Ativo. Sugestão: Escaneie Avisos [Menu Geral].{CLI_Color.ENDC}")
        print("-" * 50)

    def log_skill_check(self, skill_name: str, attribute_name: str, result):
        """Loga o resultado do skill check no formato CLI/temático."""
        status = ""
        
        if result.tier == SuccessTier.CRITICAL_SUCCESS: status = f"{CLI_Color.CYAN}SUCESSO ÉPICO (CRÍTICO)!{CLI_Color.ENDC}"
        elif result.tier == SuccessTier.CRITICAL_FAILURE: status = f"{CLI_Color.RED}FALHA ABSOLUTA (CRÍTICA)!{CLI_Color.ENDC}"
        elif result.success: status = f"{CLI_Color.GREEN}SUCESSO{CLI_Color.ENDC}"
        else: status = f"{CLI_Color.RED}FALHA{CLI_Color.ENDC}"
            
        print(f"\n> CHECK [{skill_name.upper()} ({attribute_name.title()}) DC {result.dc}]: {status}")
        print(f"  [Log Interno: Rolagem={result.roll}, Total={result.total}]")

    def display_init_log(self, text_blocks: list):
        """Exibe a introdução como um log de sistema com delay e cor."""
        self.game.cli.clear_screen()
        log_header = f"{CLI_Color.CYAN}# INITIALIZING BÜRO-SYSTEM V.1.0.1{CLI_Color.ENDC}\n"
        print(log_header)
        time.sleep(0.5)

        for line in text_blocks:
            if line.startswith('>>>'):
                print(f"{CLI_Color.YELLOW}{line}{CLI_Color.ENDC}") 
            else:
                print(f"[{CLI_Color.GREEN}STATUS_OK{CLI_Color.ENDC}] {line}")
            time.sleep(1.0) 
        
        self.game.cli.prompt_for_input("\n>> Pressione ENTER para ACESSAR o TERMINAL de TRABALHO...")

    # --- NOVOS MÉTODOS DE RENDERIZAÇÃO (Chamados pelo CLI Facade) ---

    def render_xp_gain(self, xp_amount: int):
        """Renderiza a mensagem de ganho de XP com cor (Delegado do CLI)."""
        print(f"  [{CLI_Color.GREEN}INFO{CLI_Color.ENDC}] +{xp_amount} XP.")

    def render_idle_limit_message(self):
        """Renderiza a mensagem de limite de repetições com cor de aviso (Delegado do CLI)."""
        self.game.cli.display_message(f"{CLI_Color.YELLOW}Limite de repetições atingido. Retornando ao menu de ações.{CLI_Color.ENDC}")

    # --- MÉTODOS DE FLUXO E MENU (DELEGADOS) ---

    def display_game_menu(self):
        """Exibe o Menu Zero (Principal). Este é o método que o CLI chama."""
        location = self.locations.get(self.game.player.current_location)
        self._display_location_header(location)
        self.display_player_status_bar() 
        self.display_current_objective() 
        
        options = {}; i = 1
        
        # 1. AÇÃO PRINCIPAL: Grind/Idle
        organizar_arquivos = next((a for a in location.get("ambient_actions", []) if a['id'] == 'organizar_arquivos'), None)
        if organizar_arquivos:
            options[str(i)] = (organizar_arquivos["name"], lambda a=organizar_arquivos: self.game.flow.perform_ambient_action(a)); i += 1
            
        # 2. AÇÕES DE ENGAJAMENTO: NPCs
        npcs_in_location = [npc_id for npc_id, npc_data in self.npcs.items() if npc_data.get("location") == self.game.player.current_location] 
        for npc_id in npcs_in_location:
            npc_name = self.npcs[npc_id]['name']
            display_name = f"Incomodar {npc_name}" if self.game.player.game_flags.get(f"{npc_id}_talked") else f"Falar com {npc_name}"
            options[str(i)] = (display_name, lambda n=npc_id: self.game.initiate_dialogue(n)); i += 1
            
        print("-" * 50)
            
        # 3. MENU GERAL: Navegação/Meta-Game
        options[str(i)] = (f"{CLI_Color.CYAN}Menu Geral (Viajar/Craft/Protocolos){CLI_Color.ENDC}", self.display_secondary_menu); i += 1

        # 4. CONFIGURAÇÕES: Meta-Game
        options[str(i)] = (f"{CLI_Color.YELLOW}Opções (Salvar/Sair){CLI_Color.ENDC}", 
                           lambda: setattr(self.game, 'state', 'OPTIONS_MENU')); i += 1 

        
        for key, (text, _) in options.items(): print(f"[{key}] {text}")
        choice = self.game.cli.prompt_for_input(f"\n{CLI_Color.CYAN}O que você faz?{CLI_Color.ENDC} ")

        if choice in options: 
            _, action = options[choice]; action()

    def run_quest(self, quest_id: str):
        """Delega a execução da quest para o FlowManager."""
        self.game.flow.run_quest(quest_id)
        
    def run_idle_stage(self, stage_data: dict):
        """Simula o tempo de uma ação IDLE para quests."""
        duration = stage_data.get('duration_seconds', 1)
        self.game.cli.display_message(f"O processo leva {duration} segundos. Processando...")
        time.sleep(duration / 10) 
        print("\n...Concluído.")

    # --- MÉTODOS DE UTILIDADE PENDENTES ---

    def display_secondary_menu(self):
        """Menu Geral para navegação e utilidades."""
        self.game.cli.clear_screen()
        print("="*20 + f" {CLI_Color.CYAN}MENU GERAL (Navegação/Utilidades){CLI_Color.ENDC} " + "="*20)
        self.display_player_status_bar()
        
        options = {}
        options[str(1)] = ("Viajar (Mudar de Setor)", self.display_travel_menu)
        options[str(2)] = ("Escanear Avisos (Protocolos)", self.display_quest_board)
        options[str(3)] = ("Rascunhar Formulários (Craft)", self.display_crafting_menu)
        options[str(4)] = (f"{CLI_Color.YELLOW}Voltar ao Menu de Ações{CLI_Color.ENDC}", lambda: setattr(self.game, 'state', 'IN_GAME'))
        
        for key, (text, _) in options.items(): print(f"[{key}] {text}")
        choice = self.game.cli.prompt_for_input(f"\n{CLI_Color.CYAN}Opção CLI:{CLI_Color.ENDC} ")
        
        if choice in options: 
            _, action = options[choice]; action()
        else:
            self.game.cli.display_message("Comando inválido. Retornando ao menu principal.")
            self.game.state = "IN_GAME"

    def display_options_menu(self):
        """Menu de Meta-Game (Salvar/Sair/Level Up)."""
        self.game.cli.clear_screen()
        print("="*20 + f" {CLI_Color.CYAN}OPÇÕES DO SISTEMA{CLI_Color.ENDC} " + "="*20) 
        self.display_player_status_bar()
        
        options = {}
        options[str(1)] = ("Protocolar Progresso (Salvar)", self.game.save_game)
        options[str(2)] = ("Aprimorar Carreira (Level Up)", self.display_level_up_screen)
        options[str(3)] = ("Retornar ao Jogo", lambda: setattr(self.game, 'state', 'IN_GAME'))
        options[str(4)] = ("Sair para Menu Principal", self.game.return_to_main_menu)
        options[str(5)] = (f"{CLI_Color.RED}Encerrar Sistema (Quit){CLI_Color.ENDC}", self.game.quit_game)
        
        for key, (text, _) in options.items(): print(f"[{key}] {text}")
        choice = self.game.cli.prompt_for_input(f"\n{CLI_Color.CYAN}Opção CLI:{CLI_Color.ENDC} ")
        
        if choice in options: 
            _, action = options[choice]; action()
        else:
            self.game.cli.display_message("Comando inválido. Retornando ao menu principal.")
            self.game.state = "IN_GAME"

    def display_dialogue_screen(self):
        """Exibe a tela de diálogo, permitindo escolhas ao jogador."""
        npc = self.npcs.get(self.game.dialogue_partner_id)
        node = npc['dialogue_tree'].get(self.game.dialogue_node_id)
        
        self.game.cli.clear_screen()
        print(f"--- DIÁLOGO COM: {npc['name']} ---")
        self.display_player_status_bar()
        
        print(f"\n{npc['name']}: {node['text']}\n")
        
        if 'options' in node:
            print("Escolhas:")
            options_dict = {}
            for i, option in enumerate(node['options']):
                options_dict[str(i + 1)] = option
                print(f"[{i + 1}] {option['text']}")
            
            choice_input = self.game.cli.prompt_for_input("\nSua resposta: ")
            
            try:
                choice_index = int(choice_input) - 1
                if 0 <= choice_index < len(node['options']):
                    self.game.process_dialogue_choice(choice_index)
                else:
                    self.game.cli.display_message("Escolha inválida.")
            except ValueError:
                self.game.cli.display_message("Entrada inválida.")
        else:
            # Caso seja um nó final ou narrativo sem opções
            self.game.cli.prompt_for_input("Pressione Enter para continuar...")
            self.game.state = "IN_GAME" # Encerra o diálogo se não houver opções
            
    # --- MÉTODOS DE UTILIDADE PENDENTES (Continuação) ---

    def display_travel_menu(self):
        """Exibe o menu de Viagem."""
        location = self.locations.get(self.game.player.current_location); travel_options = location.get("travel_to", [])
        self.game.cli.clear_screen()
        print(f"\n--- {CLI_Color.CYAN}Viajar Para (Mudar de Setor){CLI_Color.ENDC} ---")
        for i, location_id in enumerate(travel_options): print(f"[{i+1}] {self.locations[location_id]['name']}")
        try:
            choice = int(self.game.cli.prompt_for_input(f"{CLI_Color.CYAN}Para onde? (0 para voltar){CLI_Color.ENDC} "))
            if 1 <= choice <= len(travel_options): self.game.travel_to(travel_options[choice-1])
        except ValueError: pass

    def display_quest_board(self):
        """Exibe o quadro de avisos."""
        location = self.locations.get(self.game.player.current_location)
        available_quests = self.get_available_quests(location)
        self.game.cli.clear_screen()
        print(f"\n--- {CLI_Color.CYAN}Quadro de Avisos Burocráticos{CLI_Color.ENDC} ---")
        for i, quest_id in enumerate(available_quests): print(f"[{i+1}] {self.quests[quest_id]['title']}")
        try:
            choice = int(self.game.cli.prompt_for_input(f"{CLI_Color.CYAN}Aceitar qual Protocolo? (0 para voltar){CLI_Color.ENDC} "))
            if 1 <= choice <= len(available_quests): self.run_quest(available_quests[choice-1])
        except ValueError: pass

    def display_crafting_menu(self):
        """Exibe o menu de Crafting."""
        self.game.cli.clear_screen()
        print(f"--- Mesa de {CLI_Color.CYAN}Rascunhos Burocráticos{CLI_Color.ENDC} ---")
        self.display_player_status_bar()
        
        recipes = list(self.recipes.keys())
        for i, recipe_id in enumerate(recipes):
            recipe = self.recipes[recipe_id]
            can_craft_str = f"{CLI_Color.GREEN}✓{CLI_Color.ENDC}" if self.game.player.tem_itens(recipe['ingredients']) else f"{CLI_Color.RED}✗{CLI_Color.ENDC}"
            print(f"[{i+1}] {recipe['name']} {can_craft_str}")
        try:
            choice = int(self.game.cli.prompt_for_input(f"{CLI_Color.CYAN}Rascunhar o quê? (0 para voltar){CLI_Color.ENDC} "))
            if 1 <= choice <= len(recipes): self.game.perform_crafting(list(self.recipes.keys())[choice - 1])
        except ValueError: pass

    def display_level_up_screen(self):
        """Exibe o menu de Level Up."""
        self.game.cli.clear_screen()
        while self.game.player.pontos_de_aprimoramento > 0:
            print("="*20 + f" {CLI_Color.YELLOW}PROMOÇÃO DE CARREIRA!{CLI_Color.ENDC} " + "="*20)
            self.display_player_status_bar()
            
            print(f"Você tem {self.game.player.pontos_de_aprimoramento} ponto(s) para gastar.\n\nO que você deseja aprimorar?")
            options = list(self.game.player.attributes.keys()) + list(self.game.player.skills.keys())
            for i, option in enumerate(options): print(f"  [{i+1}] {option.title()}")
            try:
                choice = int(self.game.cli.prompt_for_input("Escolha uma opção: "))
                if 1 <= choice <= len(options): self.game.player.gastar_ponto_aprimoramento(options[choice - 1])
                else: self.game.cli.display_message("Opção inválida.")
            except (ValueError, IndexError): self.game.cli.display_message("Entrada inválida.")
        
        self.game.cli.display_message("Todos os pontos foram gastos...")
        # CORRIGIDO: Retorna ao estado anterior (COMBAT ou IN_GAME)
        self.game.state = self.game.previous_state

    def display_combat_menu(self):
        """Exibe o menu de combate com opções táticas."""
        self.game.cli.clear_screen()
        mob = self.game.current_mob
        
        print("="*20 + f" {CLI_Color.RED}COMBATE: {mob['name'].upper()}{CLI_Color.ENDC} " + "="*20)
        self.display_player_status_bar()

        mob_health = mob.get('saude_atual', mob['saude_maxima'])
        print(f"\n{CLI_Color.RED}INIMIGO:{CLI_Color.ENDC} {mob['name']} | Saúde: {mob_health}/{mob['saude_maxima']}")
        print("-" * 50)
        
        options = {}
        options[str(1)] = (f"{CLI_Color.CYAN}1. Ataque Burocrático (Skill Check){CLI_Color.ENDC}", self.process_player_attack)
        options[str(2)] = (f"{CLI_Color.YELLOW}2. Tentar Fuga (Agilidade/Discrição){CLI_Color.ENDC}", self.process_flee)
        
        for key, (text, _) in options.items(): print(f"[{key}] {text}")
        
        choice = self.game.cli.prompt_for_input(f"\n{CLI_Color.CYAN}Escolha sua Tática:{CLI_Color.ENDC} ")

        if choice in options: 
            _, action = options[choice]; action()
        else:
            self.game.cli.display_message("Comando inválido. O inimigo ataca!")
            self.process_mob_turn()

    def process_player_attack(self):
        """Delega o processamento do ataque ao FlowManager."""
        self.game.flow.process_player_attack() 

    def process_mob_turn(self):
        """Delega o turno do mob ao FlowManager."""
        self.game.flow.process_mob_turn()

    def process_flee(self):
        """Delega a tentativa de fuga ao FlowManager."""
        self.game.flow.process_flee()

    def get_available_quests(self, location: dict) -> list:
        """Lógica para filtrar quests disponíveis."""
        journal = self.game.player.quest_journal
        location_quests = location.get("quests", [])
        all_possible_quests = set(location_quests + journal.get('unlocked_quests', []))
        return [q_id for q_id in all_possible_quests if q_id not in journal['ativas'] and q_id not in journal['completas'].keys()]

    # Métodos de Log de Quest (Delegados, mas logicamente pertencem ao FlowManager)
    def log_quest_stage_header(self, quest_title: str, stage: dict):
          # Exibe cabeçalho da etapa para run_quest
        print("-" * 70); self.display_player_status_bar(); print(f"\n> {stage['description']}")

    def log_quest_completion(self, quest_id: str, mission_success: bool, total_xp_gain: int):
        # Lógica de conclusão de quest
        quest = self.quests.get(quest_id)
        print("-" * 70)
        if mission_success:
            print(f"\n--- {CLI_Color.GREEN}PROTOCOLO '{quest['title']}' CONCLUÍDO COM SUCESSO{CLI_Color.ENDC} ---")
        else:
            print(f"\n--- {CLI_Color.RED}O PROTOCOLO '{quest['title']}' TERMINOU EM FRACASSO{CLI_Color.ENDC} ---")
        
        self.display_player_status_bar()
        if self.game.state != "LEVEL_UP": self.game.cli.prompt_for_input("\nPressione Enter para retornar...")