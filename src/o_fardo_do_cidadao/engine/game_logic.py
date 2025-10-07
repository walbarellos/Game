# /src/o_fardo_do_cidadao/engine/game_logic.py
# Base lógica pura e robusta para Skill Checks e Combate.

import random
from collections import namedtuple
from enum import Enum, auto
from o_fardo_do_cidadao.core.character import Character 

XP_POR_TESTE_SUCESSO = 10

class SuccessTier(Enum):
    CRITICAL_FAILURE = auto()
    FAILURE = auto()
    SUCCESS_WITH_COST = auto() 
    SUCCESS = auto()
    CRITICAL_SUCCESS = auto()

# CORRIGIDO: Adicionado 'dc' e 'total' ao SkillCheckResult
SkillCheckResult = namedtuple("SkillCheckResult", ["success", "margin", "xp_gain", "tier", "roll", "dc", "total"])

def perform_skill_check(character: Character, skill: str, attribute: str, dc: int) -> SkillCheckResult:
    """
    Executa um teste de perícia central. Aplica penalidade de Saúde em caso de falha.
    """
    roll = random.randint(1, 20)
    modifier = character.get_attribute_modifier(attribute) 
    bonus = character.get_skill_bonus(skill)
    total = roll + modifier + bonus
    margin = total - dc
    success = margin >= 0
    xp_gain = 0
    tier: SuccessTier

    # --- Lógica de Determinação de Tier (Robusta) ---
    if roll == 1:
        tier = SuccessTier.CRITICAL_FAILURE
        success = False
    elif roll == 20:
        tier = SuccessTier.CRITICAL_SUCCESS
        success = True
    elif not success:
        tier = SuccessTier.FAILURE
    else:
        if margin >= 5: 
            tier = SuccessTier.CRITICAL_SUCCESS
        else:
            tier = SuccessTier.SUCCESS

    # --- Lógica de Recompensa/Penalidade (Alinhada à Saúde) ---
    
    if tier == SuccessTier.SUCCESS:
        xp_gain = XP_POR_TESTE_SUCESSO

    elif tier == SuccessTier.CRITICAL_SUCCESS:
        xp_gain = XP_POR_TESTE_SUCESSO * 2

    elif tier == SuccessTier.FAILURE:
        saude_damage = 1
        character.aplicar_dano_saude(saude_damage)
        
    elif tier == SuccessTier.CRITICAL_FAILURE:
        saude_damage = 5 
        character.aplicar_dano_saude(saude_damage)
        
    # --- Retorno ---
    return SkillCheckResult(success=success, margin=margin, xp_gain=xp_gain, tier=tier, roll=roll, dc=dc, total=total)
