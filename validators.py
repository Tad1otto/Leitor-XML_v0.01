# Arquivo: core/validators.py
import os

class Validador:
    @staticmethod
    def validar_pasta_xml(pasta):
        if not os.path.exists(pasta):
            return False, "A pasta selecionada não existe."
        
        arqs = [f for f in os.listdir(pasta) if f.lower().endswith('.xml')]
        
        if len(arqs) == 0:
            return False, "Nenhum arquivo .XML encontrado nesta pasta."
            
        return True, f"{len(arqs)} arquivos encontrados."