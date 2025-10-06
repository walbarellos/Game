# /src/o_fardo_do_cidadao/engine/game_logic.py

import random
from collections import namedtuple
from enum import Enum, auto
from o_fardo_do_cidadao.core.character import Character

XP_POR_TESTE_SUCESSO = 10

# NOVO: Enum para definir claramente os graus de sucesso
class SuccessTier(Enum):
    CRITICAL_FAILURE = auto()
    FAILURE = auto()
    SUCCESS_WITH_COST = auto() # Ainda não implementado, mas a estrutura está pronta
    SUCCESS = auto()
    CRITICAL_SUCCESS = auto()

# ALTERADO: Adicionado 'tier' ao resultado
SkillCheckResult = namedtuple("SkillCheckResult", ["success", "margin", "xp_gain", "tier"])

def perform_skill_check(character: Character, skill: str, attribute: str, dc: int) -> SkillCheckResult:
    """
    Executa um teste de perícia com graus de sucesso e falha.
    """
    roll = random.randint(1, 20)
    modifier = character.get_attribute_modifier(attribute)
    bonus = character.get_skill_bonus(skill)
    total = roll + modifier + bonus
    margin = total - dc
    success = margin >= 0
    xp_gain = 0
    tier: SuccessTier

    # NOVO: Lógica para determinar o grau de sucesso
    if roll == 1:
        tier = SuccessTier.CRITICAL_FAILURE
        success = False
    elif roll == 20:
        tier = SuccessTier.CRITICAL_SUCCESS
        success = True
    elif not success:
        tier = SuccessTier.FAILURE
    else: # success is True
        if margin >= 10: # Sucesso por uma margem ampla
            tier = SuccessTier.CRITICAL_SUCCESS
        else:
            tier = SuccessTier.SUCCESS

    print(f"Teste de {skill} ({attribute}): Rolagem={roll}, Mod={modifier}, Bônus={bonus} -> Total={total} vs CD={dc}")

    # NOVO: Lógica de recompensa/penalidade baseada no tier
    if tier == SuccessTier.SUCCESS:
        xp_gain = XP_POR_TESTE_SUCESSO
        print("Sucesso!")
    elif tier == SuccessTier.CRITICAL_SUCCESS:
        xp_gain = XP_POR_TESTE_SUCESSO * 2 # Recompensa dobrada!
        print("SUCESSO CRÍTICO!")
    elif tier == SuccessTier.FAILURE:
        composure_damage = abs(margin)
        character.apply_composure_damage(composure_damage)
        print("Falha.")
    elif tier == SuccessTier.CRITICAL_FAILURE:
        composure_damage = abs(margin) + 5 # Penalidade extra!
        character.apply_composure_damage(composure_damage)
        print("FALHA CRÍTICA!")
        
    return SkillCheckResult(success=success, margin=margin, xp_gain=xp_gain, tier=tier)