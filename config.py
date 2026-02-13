# Arquivo: config.py (VERSÃO FINAL - WHITE LABEL)
import os

# --- IDENTIDADE VISUAL ---
TITULO_JANELA = "Leitor XML - Extrator Fiscal"
RODAPE = "Desenvolvido por Gabriel Tadiotto"

# Cores do Layout Moderno
COR_PRINCIPAL = "#00061A"  # Azul Escuro Profissional (O mesmo que você gostou)
COR_FUNDO = "#F5F7FA"      # Cinza Gelo (Fundo das janelas)

# --- CONFIGURAÇÕES TÉCNICAS (Não alterar) ---
# Namespaces para leitura das tags da Receita Federal
NS_MAP = {
    'nfe': 'http://www.portalfiscal.inf.br/nfe',
    'cte': 'http://www.portalfiscal.inf.br/cte'
}

# --- OUTROS ---
PASTA_PADRAO_XML = ""
