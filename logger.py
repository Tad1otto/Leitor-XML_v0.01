# Arquivo: core/logger.py
import logging
import os
import traceback
from datetime import datetime

class SistemaLog:
    _configurado = False

    @staticmethod
    def configurar():
        if SistemaLog._configurado: return
        
        # Cria arquivo de log na pasta raiz do projeto
        # Volta um nível (..) para sair de 'core' e gravar na raiz
        caminho_log = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'execucao.log')
        
        logging.basicConfig(
            filename=caminho_log,
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%d/%m/%Y %H:%M:%S',
            encoding='utf-8' # Garante que acentos funcionem no log
        )
        SistemaLog._configurado = True

    @staticmethod
    def registrar_erro(mensagem, erro_tecnico: Exception = None):
        """Grava o erro no arquivo e imprime no console do Spyder"""
        SistemaLog.configurar()
        
        texto_erro = f"{mensagem}"
        if erro_tecnico:
            texto_erro += f"\n   |__ Tipo: {type(erro_tecnico).__name__}"
            texto_erro += f"\n   |__ Detalhe: {str(erro_tecnico)}"
            # O traceback ajuda a saber em qual linha do código deu erro
            texto_erro += f"\n   |__ Rastro:\n{traceback.format_exc()}"
        
        logging.error(texto_erro)
        print(f"❌ [LOG GRAVADO]: {mensagem}") # Aviso visual no console