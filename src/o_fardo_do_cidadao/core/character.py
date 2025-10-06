# /src/o_fardo_do_cidadao/core/character.py
# Adiciona o dicionário de Reputação e o método para alterá-la.

import math

class Character:
    def __init__(self, name: str):
        self.name = name
        self.attributes = {"Poder": 10, "Agilidade": 10, "Fortitude": 10, "Raciocínio": 10, "Intuição": 10, "Presença": 10}
        self.skills = {"Burocracia": 1, "Persuasão": 1, "Organização": 1, "Negociação": 1, "Discrição": 1, "Informática": 1}
        self.inventory = {}
        self.reputation = {} # NOVO: Dicionário para reputação
        self.quest_journal = {"ativas": [], "completas": {}, "unlocked_quests": []}
        self.status_effects = []
        self.level = 1; self.xp_atual = 0; self.xp_para_proximo_nivel = 100; self.pontos_de_aprimoramento = 0
        self.current_location = "escritorio_protocolo"; self.game_flags = {}; self._initialize_derived_stats()

    # NOVO: Método para gerenciar Reputação
    def alterar_reputacao(self, faccao: str, valor: int):
        if not faccao: return
        if faccao not in self.reputation: self.reputation[faccao] = 0
        self.reputation[faccao] += valor
        delta = f"+{valor}" if valor > 0 else str(valor)
        print(f"Sua reputação com '{faccao}' mudou em {delta}. Total: {self.reputation[faccao]}")

    # ATUALIZADO: __str__ agora mostra a reputação
    def __str__(self) -> str:
        header = f"--- Cidadão: {self.name} | Nível: {self.level} ---"; xp_bar = f"XP: {self.xp_atual}/{self.xp_para_proximo_nivel}"
        status = f"Saúde: {self.saude_atual}/{self.saude_maxima} | Compostura: {self.compostura_atual}/{self.compostura_maxima}"
        effects = f"Efeitos: {self.status_effects if self.status_effects else 'Nenhum'}"
        inv_str = "Inventário: " + (", ".join([f"{item}(x{qty})" for item, qty in self.inventory.items()]) if self.inventory else "Vazio")
        rep_str = "Reputação: " + (", ".join([f"{faccao}: {rep}" for faccao, rep in self.reputation.items()]) if self.reputation else "Neutra")
        return f"\n{header}\n{xp_bar}\n{status}\n{effects}\n{inv_str}\n{rep_str}\n"

    # (O resto da classe não muda, mas está abaixo para garantir a integridade)
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
    def aplicar_cura_compostura(self, quantidade: int):
        if quantidade > 0: self.compostura_atual = min(self.compostura_maxima, self.compostura_atual + quantidade); print(f"Você se sente mais calmo. [+{quantidade} Compostura]")
    @property
    def saude_maxima(self) -> int: return (self.attributes.get("Fortitude", 10) * 10) + (self.attributes.get("Poder", 10) * 2)
    @property
    def compostura_maxima(self) -> int: return (self.attributes.get("Fortitude", 10) * 5) + (self.attributes.get("Presença", 10) * 5)
    def _initialize_derived_stats(self): self.saude_atual = self.saude_maxima; self.compostura_atual = self.compostura_maxima
    def get_attribute_modifier(self, attribute_name: str) -> int: return math.floor((self.attributes.get(attribute_name.title(), 10) - 10) / 2)
    def get_skill_bonus(self, skill_name: str) -> int: return self.skills.get(skill_name.title(), 0)
    def apply_composure_damage(self, amount: int):
        self.compostura_atual = max(0, self.compostura_atual - amount)
        print(f"\nSua compostura foi abalada! [-{amount}] -> Atual: {self.compostura_atual}/{self.compostura_maxima}")
        if self.compostura_atual == 0: print("Você está no seu limite..."); self.status_effects.append("Frustrado")
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
    def gastar_ponto_aprimoramento(self, stat: str) -> bool:
        if self.pontos_de_aprimoramento <= 0: print("Você não tem pontos para gastar."); return False
        stat_title = stat.title()
        if stat_title in self.attributes:
            self.attributes[stat_title] += 1; self.pontos_de_aprimoramento -= 1
            print(f"Seu atributo {stat_title} aumentou para {self.attributes[stat_title]}!"); return True
        elif stat_title in self.skills:
            self.skills[stat_title] += 1; self.pontos_de_aprimoramento -= 1
            print(f"Sua perícia {stat_title} aumentou para {self.skills[stat_title]}!"); return True
        else: print(f"'{stat_title}' não é um atributo ou perícia válida."); return False
    def to_dict(self) -> dict: return self.__dict__
    @classmethod
    def from_dict(cls, data: dict):
        player = cls(name=data.get('name'));
        for key, value in data.items():
            if hasattr(player, key): setattr(player, key, value)
        player._initialize_derived_stats(); player.game_flags = data.get('game_flags', {}); return player