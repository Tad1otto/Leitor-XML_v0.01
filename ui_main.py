# Arquivo: interface/ui_main.py (VERSÃO FINAL - COM ÍCONE EMBUTIDO)
import os
import sys
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox

# Adiciona o diretório pai ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import config
from core.processador import ProcessadorFiscal
from interface.ui_utils import ViewLogger, UIHelper

# --- FUNÇÃO MÁGICA: Encontra arquivos dentro do .EXE ---
def resource_path(relative_path):
    """ Retorna o caminho absoluto do recurso, seja como script ou EXE congelado """
    try:
        # PyInstaller cria uma pasta temporária em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
# -------------------------------------------------------

class FiscalApp:
    def __init__(self, root):
        self.root = root
        self.logger = None
        self.setup_ui()
        
    def setup_ui(self):
        # Configurações da Janela Principal
        self.root.title(config.TITULO_JANELA)
        
        # --- CARREGAMENTO DO ÍCONE ---
        try:
            # Procura o ícone usando o caminho inteligente
            caminho_icone = resource_path("icone_limpo.ico")
            self.root.iconbitmap(caminho_icone)
        except Exception:
            pass # Se falhar, usa o padrão do Windows
        # -----------------------------

        self.root.geometry("700x750") 
        self.root.configure(bg="#F5F7FA")

        # =====================================================================
        # 1. HEADER (TOPO)
        # =====================================================================
        cor_header = getattr(config, 'COR_PRINCIPAL', '#00061A') 
        
        header_frame = tk.Frame(self.root, bg=cor_header, height=140)
        header_frame.pack(side="top", fill="x")
        header_frame.pack_propagate(False)

        header_content = tk.Frame(header_frame, bg=cor_header)
        header_content.place(relx=0.5, rely=0.5, anchor="center")

        lbl_icon = tk.Label(header_content, text="📑", font=("Segoe UI Emoji", 48), 
                            bg=cor_header, fg="white")
        lbl_icon.pack(side="left", padx=(0, 15))

        text_container = tk.Frame(header_content, bg=cor_header)
        text_container.pack(side="left")

        lbl_titulo = tk.Label(text_container, text="LEITOR XML", 
                              font=("Segoe UI", 22, "bold"), 
                              bg=cor_header, fg="white", anchor="w")
        lbl_titulo.pack(fill="x")

        lbl_subtitulo = tk.Label(text_container, text="Extrator de Dados Fiscais & Logísticos", 
                                 font=("Segoe UI", 10), 
                                 bg=cor_header, fg="#AEC0E5", anchor="w")
        lbl_subtitulo.pack(fill="x")

        # =====================================================================
        # 2. RODAPÉ (PRESO AO FUNDO)
        # =====================================================================
        texto_rodape = getattr(config, 'RODAPE', 'Desenvolvido por Gabriel Tadiotto')
        
        lbl_rodape = tk.Label(self.root, text=texto_rodape, 
                              bg="#F5F7FA", fg="#999", font=("Segoe UI", 8))
        lbl_rodape.pack(side="bottom", pady=15)

        # =====================================================================
        # 3. CORPO (MEIO)
        # =====================================================================
        card_frame = tk.Frame(self.root, bg="white", bd=0)
        # O corpo preenche o espaço entre o Header e o Rodapé
        card_frame.pack(fill="both", expand=True, padx=40, pady=(40, 20))
        card_frame.config(highlightbackground="#E1E4E8", highlightthickness=1)

        # Título da Ação
        tk.Label(card_frame, text="Iniciar Processamento", 
                 font=("Segoe UI", 14, "bold"), bg="white", fg="#333").pack(pady=(30, 10))

        tk.Label(card_frame, text="Selecione a pasta dos XMLs e defina onde salvar o relatório.", 
                 font=("Segoe UI", 10), bg="white", fg="#666").pack(pady=(0, 25))

        # --- BOTÃO PRINCIPAL ---
        self.btn = tk.Button(card_frame, text="SELECIONAR PASTA E GERAR RELATÓRIO", 
                             command=self.iniciar_processamento,
                             font=("Segoe UI", 11, "bold"), 
                             bg=cor_header, 
                             fg="white",
                             activebackground="#2c3e50", activeforeground="white",
                             relief="flat",
                             height=2, width=45, cursor="hand2")
        self.btn.pack(pady=10)

        # --- BARRA DE PROGRESSO ---
        progress_frame = tk.Frame(card_frame, bg="white")
        progress_frame.pack(fill="x", padx=40, pady=(30, 5))

        self.lbl_progresso = tk.Label(progress_frame, text="Aguardando ação do usuário...", 
                                      font=("Segoe UI", 9), bg="white", fg="#888", anchor="w")
        self.lbl_progresso.pack(fill="x")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("blue.Horizontal.TProgressbar", background=cor_header, troughcolor="#F0F0F0", bordercolor="#F0F0F0")

        self.progress = ttk.Progressbar(progress_frame, style="blue.Horizontal.TProgressbar", 
                                        orient="horizontal", length=100, mode="determinate")
        self.progress.pack(fill="x", pady=5)

        # --- LOG ---
        log_frame = tk.Frame(card_frame, bg="white", pady=10)
        log_frame.pack(fill="both", expand=True, padx=40, pady=(0, 30))

        tk.Label(log_frame, text="Log de Execução:", font=("Segoe UI", 9, "bold"), bg="white", fg="#444").pack(anchor="w")

        txt_log = scrolledtext.ScrolledText(log_frame, height=10, font=("Consolas", 9), 
                                            bg="#F8F9FA", fg="#333", relief="flat", bd=1)
        txt_log.config(highlightbackground="#E1E4E8", highlightthickness=1)
        txt_log.pack(fill="both", expand=True, pady=5)
        
        self.logger = ViewLogger(txt_log)

    def atualizar_progresso(self, valor, texto):
        self.progress['value'] = valor
        self.lbl_progresso.config(text=texto)
        self.root.update()

    def iniciar_processamento(self):
        # 1. Selecionar Pasta XML
        pasta = filedialog.askdirectory(title="Selecione a pasta com os XMLs")
        if not pasta: return

        # 2. Escolher onde Salvar
        arquivo_saida = filedialog.asksaveasfilename(
            title="Salvar Relatório Como",
            defaultextension=".xlsx",
            filetypes=[("Arquivo Excel", "*.xlsx")],
            initialfile="Relatorio_XML.xlsx",
            initialdir=pasta
        )
        
        if not arquivo_saida: return
        
        # 3. Executar Lógica
        try:
            self.btn.config(state="disabled", text="PROCESSANDO...", bg="#555")
            self.root.update()
            
            saida_final = ProcessadorFiscal.executar(
                pasta_xml=pasta,
                caminho_saida=arquivo_saida,
                callback_log=self.logger.log,
                callback_progresso=self.atualizar_progresso,
                callback_retry=tk.messagebox.askretrycancel
            )
            
            self.logger.log("Processo finalizado com sucesso.")
            UIHelper.sucesso("Sucesso", f"Relatório salvo em:\n{saida_final}")
            try: os.startfile(saida_final)
            except: pass

        except Exception as e:
            self.logger.log(f"ERRO FATAL: {e}")
            UIHelper.erro("Erro no Processamento", str(e))
        
        finally:
            cor_padrao = getattr(config, 'COR_PRINCIPAL', '#00061A')
            self.btn.config(state="normal", text="SELECIONAR PASTA E GERAR RELATÓRIO", bg=cor_padrao)
