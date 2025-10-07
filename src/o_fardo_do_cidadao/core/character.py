# /home/wepiphany/Game/src/o_fardo_do_cidadao/core/character.py
# CORRIGIDO: Implementação do método gastar_ponto_aprimoramento e remoção da lógica de UI (display_message).

import math

class Character:
    def __init__(self, name: str):
        self.name = name
        self.attributes = {"Poder": 10, "Agilidade": 10, "Fortitude": 10, "Raciocínio": 10, "Intuição": 10, "Presença": 10}
        self.skills = {"Burocracia": 1, "Persuasão": 1, "Organização": 1, "Negociação": 1, "Discrição": 1, "Informática": 1}
        self.inventory = {}
        self.reputation = {}
        self.quest_journal = {"ativas": [], "completas": {}, "unlocked_quests": []}
        self.status_effects = []
        self.level = 1
        self.xp_atual = 0
        self.xp_para_proximo_nivel = 100
        self.pontos_de_aprimoramento = 0
        self.current_location = "escritorio_protocolo"
        self.game_flags = {'idle_mode': False} 
        self._initialize_derived_stats()

    # MÉTODOS DE SAÚDE
    def aplicar_dano_saude(self, amount: int):
        """Aplica dano à Saúde."""
        self.saude_atual = max(0, self.saude_atual - amount)
        print(f"\nSua saúde foi abalada! [-{amount}] -> Atual: {self.saude_atual}/{self.saude_maxima}")
        if self.saude_atual == 0: print("Sua saúde chegou a zero. Busque tratamento."); self.status_effects.append("Incapacitado")

    def aplicar_cura_saude(self, amount: int):
        """Aplica cura à Saúde, ignorando se já estiver no máximo."""
        if amount > 0 and self.saude_atual < self.saude_maxima: 
            self.saude_atual = min(self.saude_maxima, self.saude_atual + amount)
            print(f"\nVocê se recuperou. [+{amount} Saúde] -> Atual: {self.saude_atual}/{self.saude_maxima}")
        elif amount > 0 and self.saude_atual == self.saude_maxima:
            print(f"\nSeu estado é ótimo; a cura foi ineficaz. (Saúde Máxima)")
            
    # --- MÉTODOS DE PROGRESSÃO/DADOS ---

    def alterar_reputacao(self, faccao: str, valor: int):
        if not faccao: return
        if faccao not in self.reputation: self.reputation[faccao] = 0
        self.reputation[faccao] += valor
        delta = f"+{valor}" if valor > 0 else str(valor)
        print(f"Sua reputação com '{faccao}' mudou em {delta}. Total: {self.reputation[faccao]}")

    def adicionar_item(self, item_id: str, quantidade: int = 1):
        if item_id not in self.inventory: self.inventory[item_id] = 0
        self.inventory[item_id] += quantidade; print(f"Você obteve: {item_id} (x{quantidade})")
        
    def tem_itens(self, ingredients: dict) -> bool:
        for item_id, qty in ingredients.items():
            if self.inventory.get(item_id, 0) < qty: return False
        return True
        
    def consumir_itens(self, ingredients: dict):
        for item_id, qty in ingredients.items():
            self.inventory[item_id] -= qty
            if self.inventory[item_id] == 0: del self.inventory[item_id]
            
    @property
    def saude_maxima(self) -> int: return (self.attributes.get("Fortitude", 10) * 10) + (self.attributes.get("Poder", 10) * 2)
    
    def _initialize_derived_stats(self): self.saude_atual = self.saude_maxima
    
    def get_attribute_modifier(self, attribute_name: str) -> int: return math.floor((self.attributes.get(attribute_name.title(), 10) - 10) / 2)
    
    def get_skill_bonus(self, skill_name: str) -> int: return self.skills.get(skill_name.title(), 0)
    
    def adicionar_experiencia(self, quantidade: int) -> bool:
        if quantidade <= 0: return False
        self.xp_atual += quantidade; print(f"Você ganhou {quantidade} XP! ({self.xp_atual}/{self.xp_para_proximo_nivel})")
        leveled_up = False
        while self.xp_atual >= self.xp_para_proximo_nivel: self._subir_de_nivel(); leveled_up = True
        return leveled_up
        
    def _subir_de_nivel(self):
        self.level += 1; self.xp_atual -= self.xp_para_proximo_nivel
        self.xp_para_proximo_nivel = int(self.xp_para_proximo_nivel * 1.5); self.pontos_de_aprimoramento += 1
        print(f"\n{'='*15}\n!!! LEVEL UP !!! Você alcançou o nível {self.level}!\n{'='*15}\nVocê recebeu 1 Ponto de Aprimoramento!")
        
    # CORRIGIDO: Implementação do método que a UIManager espera (sem lógica de UI/display)
    def gastar_ponto_aprimoramento(self, attribute_or_skill_name: str) -> bool:
        """Gasta 1 ponto de aprimoramento para aumentar um atributo ou skill em 1. Retorna True em sucesso."""
        if self.pontos_de_aprimoramento < 1:
            return False # Sinaliza falha por insuficiência de pontos
            
        name = attribute_or_skill_name.title()
        success = False
        
        if name in self.attributes:
            self.attributes[name] += 1
            self.pontos_de_aprimoramento -= 1
            print(f"\n[Aprimoramento] {name} aumentado para {self.attributes[name]}.")
            success = True
            
        elif name in self.skills:
            self.skills[name] += 1
            self.pontos_de_aprimoramento -= 1
            print(f"\n[Aprimoramento] {name} aumentado para {self.skills[name]}.")
            success = True
            
        # Re-inicializa para recalcular HP máximo, etc.
        self._initialize_derived_stats()
        return success 

    def to_dict(self) -> dict: return self.__dict__
    
    @classmethod
    def from_dict(cls, data: dict):
        player = cls(name=data.get('name'));
        for key, value in data.items():
            if hasattr(player, key): setattr(player, key, value)
        player._initialize_derived_stats(); player.game_flags = data.get('game_flags', {'idle_mode': False}); return player