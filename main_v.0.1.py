# Arquivo: main.py
import tkinter as tk
from interface.ui_main import FiscalApp

if __name__ == "__main__":
    # Cria a janela raiz
    root = tk.Tk()
    
    # Inicia a aplicação passando o controle para a Interface
    app = FiscalApp(root)
    
    # Mantém o programa rodando
    root.mainloop()