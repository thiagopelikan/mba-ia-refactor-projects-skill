"""Ponto de entrada da aplicação — delega ao composition root em `src/app.py`.

Uso:
    SECRET_KEY=<chave> PORT=5055 python app.py
(ou `python -m src.app`; veja .env.example para todas as variáveis.)
"""
from src.app import main

if __name__ == "__main__":
    main()
