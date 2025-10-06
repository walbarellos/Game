# /src/o_fardo_do_cidadao/main.py

import sys
import os

# Adiciona a pasta 'src' ao path do Python para resolver os imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from o_fardo_do_cidadao.engine.game import Game

def main():
    """Cria e executa a instância principal do jogo."""
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
