# /home/wepiphany/Game/src/o_fardo_do_cidadao/engine/flow_manager.py
# CORRIGIDO: Implementação do loop de combate com pausas controladas para melhor UX.

import random
from .game_logic import perform_skill_check, SuccessTier 
import time

class FlowManager:
    """
    Gerencia a lógica de estado, loops de jogo e regras de domínio (o quê).
    Todas as interações com a UI são feitas através do Facade CLI (self.game.cli).
    Acesso a dados (quests, locations, etc.) é feito diretamente via self.game (Owner).
    """
    def __init__(self, game):
        self.game = game
        self.quests = game.quests  
        self.locations = game.locations
        self.recipes = game.recipes 
        self.mobs = game.mobs 

    # --- MÉTODO 1: FLUXO IDLE (O Loop de Grind) ---
    
    def run_idle_loop(self):
        """Controla o loop de Grind Automático."""
        player = self.game.player
        action_id = player.game_flags.get('current_idle_action')
        location = self.locations.get(player.current_location)
        
        action_data = next((a for a in location.get("ambient_actions", []) if a['id'] == action_id), None)
        
        if not action_data:
            self.game.cli.display_message("Erro: Ação IDLE não encontrada. Retornando ao menu.")
            self.game.state = "IN_GAME"
            return

        self.game.cli.display_idle_header(action_data['name'])
        
        while self.game.state == "IDLE_GRIND":
            
            xp_gain = self._process_single_idle_action(action_data)
            
            if xp_gain > 0:
                self.game.cli.log_xp_gain(xp_gain)
            
            time.sleep(action_data.get('duration_seconds', 1) / 10) 
            
            player.game_flags['idle_count'] = player.game_flags.get('idle_count', 0) + 1
            if player.game_flags['idle_count'] > 10:
                self.game.cli.display_idle_limit_message()
                player.game_flags['idle_count'] = 0
                self.game.state = "IN_GAME"

    def _process_single_idle_action(self, action_data: dict) -> int:
        """Processa uma única iteração de uma ação IDLE (Surto, Dano/Cura, XP)."""
        surtos = action_data.get("surtos_potenciais", [])
        triggered_outbreak = None
        xp_gain = 0
        
        if surtos:
            outbreak_roll = random.random(); cumulative_chance = 0
            for surto in surtos:
                cumulative_chance += surto.get("chance", 0)
                if outbreak_roll < cumulative_chance: triggered_outbreak = surto; break

        if triggered_outbreak:
            # 🚨 INÍCIO DO NOVO FLUXO: COMBATE
            challenge_data = triggered_outbreak.get('challenge', {})
            if challenge_data.get('type') == 'combat':
                mob_id = challenge_data['mob_id']
                self.game.initiate_combat(mob_id) 
                return xp_gain 

            # Feedback de Surto Burocrático (Não-Combate)
            self.game.cli.display_message(triggered_outbreak["description"]) 
            
            effect = triggered_outbreak.get("effect", {})
            
            if "saude_heal" in effect: self.game.player.aplicar_cura_saude(effect["saude_heal"])
            
            challenge = triggered_outbreak.get("challenge")
            if challenge and challenge.get("type") == "skill_check":
                result = perform_skill_check(self.game.player, challenge['skill'], challenge['skill'], challenge['dc']) 
                self.game.cli._log_skill_check(challenge['skill'], challenge['skill'], result) 
                xp_gain += result.xp_gain
                
                if result.success:
                    outcome = challenge.get("em_sucesso", {})
                    xp_gain += outcome.get("xp", 0)
                else:
                    outcome = challenge.get("em_falha", {})
                    saude_damage = outcome.get("saude_damage", 0)
                    if saude_damage > 0: self.game.player.aplicar_dano_saude(saude_damage)
            
            if "desbloqueia_protocolo" in effect:
                self.game.unlock_quest(effect["desbloqueia_protocolo"])
            
            self.game.state = "IN_GAME" 
            return xp_gain

        # 2. SEM SURTO: Recompensa IDLE Padrão (Grind)
        recompensa = action_data.get("recompensa", {})
        
        if "saude_heal" in recompensa:
            self.game.player.aplicar_cura_saude(recompensa["saude_heal"])

        if "saude_damage" in recompensa:
            self.game.player.aplicar_dano_saude(recompensa["saude_damage"])

        if "xp" in recompensa: 
            xp_gain += recompensa["xp"]
            self.game.process_xp_gain(xp_gain) 
        
        return xp_gain

    # --- MÉTODO 2: FLUXO DE QUEST (run_quest) ---
    
    def run_quest(self, quest_id: str):
        """Executa a lógica de uma quest sequencial (migrada do UIManager)."""
        quest = self.quests.get(quest_id); current_stage_id = quest.get("start_stage", "1"); journal = self.game.player.quest_journal
        journal['ativas'].append(quest_id); mission_success = True; total_xp_gain = 0; final_stage_id = ""
        
        while current_stage_id:
            final_stage_id = current_stage_id; stage = quest['stages'].get(current_stage_id)
            if not stage: self.game.cli.display_message(f"ERRO: Etapa '{current_stage_id}' não encontrada."); break
            
            self.game.cli.ui.log_quest_stage_header(quest['title'], stage) 
            
            stage_type = stage.get("type")
            
            if stage_type == 'idle': 
                self.game.cli._run_idle_stage(stage)
                current_stage_id = stage.get("proxima_etapa")
                
            elif stage_type == 'skill_check':
                chosen_attribute = self.game.cli._prompt_for_attribute_choice(stage)
                result = perform_skill_check(self.game.player, stage['skill'], chosen_attribute, stage['dc']) 
                self.game.cli._log_skill_check(stage['skill'], chosen_attribute, result) 
                
                total_xp_gain += result.xp_gain
                if not result.success: mission_success = False
                current_stage_id = stage.get("em_sucesso") if result.success else stage.get("em_falha")
                
            elif stage_type == 'morality_choice':
                options = stage.get("options", {}); choice_keys = list(options.keys())
                self.game.cli.ui.log_morality_options(stage) 
                
                try:
                    choice = int(self.game.cli.prompt_for_input("Escolha seu caminho: "))
                    if 1 <= choice <= len(choice_keys):
                        chosen_key = choice_keys[choice - 1]; chosen_option = options[chosen_key]
                        effect = chosen_option.get("effect", {})
                        if "reputation_change" in effect:
                            rep_change = effect["reputation_change"]
                            self.game.player.alterar_reputacao(rep_change["faccao"], rep_change["valor"])
                        if "xp" in effect: self.game.process_xp_gain(effect["xp"])
                        if "saude_heal" in effect: self.game.player.aplicar_cura_saude(effect["saude_heal"])
                        current_stage_id = chosen_option.get("result")
                    else: self.game.cli.display_message("Escolha inválida. O momento passou."); current_stage_id = None
                except ValueError: self.game.cli.display_message("Você hesita demais. A oportunidade se foi."); current_stage_id = None
                
            elif stage_type == 'narrative': current_stage_id = stage.get("proxima_etapa")
            
            if stage.get("fim_etapa"): break
            
        # Pós-Missão
        self.game.process_xp_gain(total_xp_gain)
        self.game.cli.ui.log_quest_completion(quest_id, mission_success, total_xp_gain) 
        
        self.game.cli.display_player_status()
        if self.game.state != "LEVEL_UP": self.game.cli.prompt_for_input("\nPressione Enter para retornar...")

    # --- MÉTODOS DE CRAFTING E AMBIENTE (MIGRADO DE GAME.PY) ---

    def perform_ambient_action(self, action_data: dict):
        """Método de entrada de ambient_actions (delegado pelo Game)."""
        self.game.cli.clear_screen()
        print(f"--- {action_data['name']} ---")
        self.game.cli.display_player_status()
        print(f"_{action_data.get('description', '')}_")
        
        action_type = action_data.get("type")
        total_xp_gain = 0
        
        if action_type == "idle":
             # Delega para o loop se tiver surto
             if action_data.get("surtos_potenciais") or action_data.get("recompensa"):
                self.game.player.game_flags['current_idle_action'] = action_data['id']
                self.game.state = "IDLE_GRIND"
                self.game.cli.display_message("Iniciando modo de Grind Automático.")
                return 
             # Lógica simplificada de idle sem loop
             self.game.cli._run_idle_stage(action_data)
             recompensa = action_data.get("recompensa", {})
             if "saude_heal" in recompensa:
                self.game.player.aplicar_cura_saude(recompensa["saude_heal"])
                self.game.cli.display_message(f"Você se recuperou um pouco. [+{recompensa['saude_heal']} Saúde]")
             if "xp" in recompensa: total_xp_gain += recompensa["xp"]

        elif action_type == "skill_check":
             chosen_attribute = action_data.get("attributes", [action_data['skill']])[0] 
             result = perform_skill_check(self.game.player, action_data['skill'], chosen_attribute, action_data['dc'])
             self.game.cli._log_skill_check(action_data['skill'], chosen_attribute, result) 
             total_xp_gain += result.xp_gain
             # ... (Restante da lógica de recompensa/dano de skill check)

        self.game.process_xp_gain(total_xp_gain)
        self.game.cli.prompt_for_input("\nPressione Enter para continuar...")
        
    def perform_crafting(self, recipe_id: str):
        """Método de crafting (delegado pelo Game)."""
        recipe = self.game.recipes.get(recipe_id)
        if not recipe: self.game.cli.display_message("Receita inválida."); return
        self.game.cli.clear_screen()
        print(f"--- Tentando Rascunhar: {recipe['name']} ---")
        self.game.cli.display_player_status()
        print(f"_{recipe['description']}_")
        
        if not self.game.player.tem_itens(recipe['ingredients']): self.game.cli.display_message("Você não tem os ingredientes necessários."); return
        
        print("\nRealizando o teste de fabricação..."); check_data = recipe['skill_check']
        result = perform_skill_check(self.game.player, check_data['skill'], check_data['skill'], check_data['dc'])
        
        if result.success:
            self.game.player.consumir_itens(recipe['ingredients'])
            resultado = recipe['resultado']
            self.game.player.adicionar_item(resultado['id_item'], resultado['quantidade'])
            self.game.cli.display_message("Rascunho bem-sucedido!")
        else: self.game.cli.display_message("Você falhou. Os materiais parecem intactos... por enquanto.")
        
        self.game.process_xp_gain(result.xp_gain); self.game.cli.prompt_for_input("\nPressione Enter para continuar...")

    # --- MÉTODOS DE COMBATE (LÓGICA PURA) ---
    
    def process_player_attack(self):
        """
        [CORRIGIDO] Processa o ataque do jogador: Rola o dado, calcula o dano, e aplica.
        """
        player = self.game.player
        mob = self.game.current_mob
        
        # 1. Lógica: Realizar Skill Check de Ataque
        attack_skill = "Burocracia"
        attack_attribute = "Poder" 
        mob_defense_dc = mob.get('defesa_dc', 10) 
        
        result = perform_skill_check(player, attack_skill, attack_attribute, mob_defense_dc)
        self.game.cli._log_skill_check(attack_skill, attack_attribute, result)
        
        damage_dealt = 0
        if result.success:
            # 2. Lógica: Calcular Dano
            base_damage = player.get_attribute_modifier("Poder") + 3 
            damage_multiplier = 2 if result.tier == SuccessTier.CRITICAL_SUCCESS else 1
            damage_dealt = base_damage * damage_multiplier
            
            # 3. Lógica: Aplicar Dano
            self.game.process_mob_damage(damage_dealt)
            
            # 4. Feedback (UI)
            self.game.cli.display_message(f"Você golpeou o {mob['name']} por {damage_dealt} de dano! (XP ganho: {result.xp_gain})")
            
        else:
            self.game.cli.display_message(f"Seu ataque falhou! O {mob['name']} não foi afetado.")
        
        # 5. Ganho de XP 
        self.game.process_xp_gain(result.xp_gain)
        
        # 6. VERIFICAÇÃO DE ESTADO E PRÓXIMO TURNO
        if mob['saude_atual'] > 0:
            # CORRIGIDO: Pausa para UX antes de passar o turno para o mob.
            self.game.cli.prompt_for_input("Pressione Enter para ver o turno do inimigo...")
            self.process_mob_turn()
        # Se não, a vitória já foi processada via self.game.process_mob_damage


    def process_mob_turn(self):
        """
        [CORRIGIDO] Processa o turno do mob: Calcula ataque e aplica dano ao jogador.
        """
        player = self.game.player
        mob = self.game.current_mob
        
        if self.game.state != "COMBAT":
            return
            
        self.game.cli.display_message(f"O {mob['name']} ataca!");
        
        # 1. Lógica: Cálculo de Ataque do Mob
        mob_attack_value = mob.get('ataque', 5) 
        
        # 2. Lógica: Cálculo de Defesa do Jogador
        player_defense = player.get_attribute_modifier("Fortitude") + player.get_skill_bonus("Organização")
        
        damage_taken = max(0, mob_attack_value - player_defense)
        
        # 3. Lógica: Aplica Dano
        if damage_taken > 0:
            player.aplicar_dano_saude(damage_taken) 
            self.game.cli.display_message(f"Você sofreu {damage_taken} de dano!")
        else:
            self.game.cli.display_message("Você defendeu o ataque do mob.")
            
        # 4. Verifica a vida do jogador
        if player.saude_atual <= 0:
            self.process_combat_defeat()
        else:
            # Volta para o menu do jogador
            self.game.state = "COMBAT"
            # CORRIGIDO: Pausa para UX antes de retornar ao menu de combate.
            self.game.cli.prompt_for_input("Pressione Enter para retornar ao menu de táticas...")

    def process_flee(self):
        """
        [NOVO] Processa a tentativa de fuga do jogador.
        """
        player = self.game.player
        mob = self.game.current_mob
        
        flee_skill = "Discrição"
        flee_attribute = "Agilidade"
        flee_dc = mob.get('fuga_dc', 15) # DC baseada na dificuldade de escapar do mob
        
        result = perform_skill_check(player, flee_skill, flee_attribute, flee_dc)
        self.game.cli._log_skill_check(flee_skill, flee_attribute, result)
        
        if result.success:
            self.game.cli.display_message("Você conseguiu escapar do combate!");
            self.game.process_xp_gain(result.xp_gain)
            self.game.state = "IN_GAME"
        else:
            self.game.cli.display_message("Você não conseguiu fugir!");
            self.game.process_xp_gain(result.xp_gain)
            # Sem pausa, o mob ataca imediatamente
            self.process_mob_turn() # Mob ataca após a falha na fuga

    def process_combat_defeat(self):
        """
        [NOVO] Lógica a ser implementada quando o jogador é derrotado.
        """
        # TODO: Implementar lógica de derrota (Game Over, penalidade de XP/Saúde, etc.)
        self.game.cli.display_message("Você foi sobrecarregado pelo combate! Derrota!")
        self.game.return_to_main_menu() # Exemplo de ação após derrota (retornar ao menu principal)
        
    def process_combat_victory(self, mob):
        """
        [CORRIGIDO] Lógica a ser implementada para processar a vitória de combate,
        garantindo um prompt de confirmação de UX antes de retornar.
        """
        # TODO: Implementar lógica de recompensa de combate
        
        # 1. Exibe a mensagem de vitória (que já tem um sleep em display_message)
        self.game.cli.display_message(f"Vitória contra {mob['name']}! (Recompensas pendentes)")
        
        # 2. ADICIONADO: Prompt de confirmação para segurar a tela de feedback final.
        self.game.cli.prompt_for_input("\nProtocolo de combate finalizado. Pressione Enter para retornar ao menu principal...")
        
        # 3. Transição de estado limpa.
        self.game.state = "IN_GAME"