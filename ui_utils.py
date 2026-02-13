# Arquivo: interface/ui_utils.py
import tkinter as tk
from tkinter import messagebox
import re

class ViewLogger:
    """Gerencia o log na tela (ScrolledText)"""
    def __init__(self, widget):
        self.widget = widget

    def log(self, msg):
        """Escreve uma mensagem no widget de texto e rola para o final"""
        if self.widget:
            self.widget.insert(tk.END, msg + "\n")
            self.widget.see(tk.END)

class UIHelper:
    """Funções utilitárias de interface e formatação visual"""
    
    @staticmethod
    def formatar_documento(doc):
        """Formata CPF/CNPJ para exibição"""
        if not doc: return ""
        d = re.sub(r'\D', '', str(doc))
        if len(d) == 14: return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
        elif len(d) == 11: return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
        return doc

    @staticmethod
    def limpar_nome(nome):
        """Remove códigos do início do nome para exibição"""
        if not nome: return ""
        return re.sub(r'^\d+\s*[-]\s*', '', str(nome)).strip()

    # --- Wrappers para MessageBox (Facilita a leitura no código principal) ---
    @staticmethod
    def erro(titulo, msg):
        messagebox.showerror(titulo, msg)

    @staticmethod
    def sucesso(titulo, msg):
        messagebox.showinfo(titulo, msg)

    @staticmethod
    def aviso(titulo, msg):
        messagebox.showwarning(titulo, msg)

    @staticmethod
    def perguntar(titulo, msg):
        return messagebox.askyesno(titulo, msg)