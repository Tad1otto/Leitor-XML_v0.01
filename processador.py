# Arquivo: core/processador.py (VERSÃO FINAL - COM CAMINHO PERSONALIZADO)
import os
import xml.etree.ElementTree as ET
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# Importações do Core (Sem SAP/Conciliador)
from core.xml_parser import XMLParser
from core.excel_writer import ExcelReportWriter
from core.logger import SistemaLog
from core.validators import Validador
import config

class ProcessadorFiscal:
    
    @staticmethod
    def _processar_um_xml(caminho_arquivo, ns):
        """
        Versão Simples: Apenas extração de dados XML.
        """
        try:
            tree = ET.parse(caminho_arquivo)
            root = tree.getroot()
            tag = root.tag.lower()
            
            local_nfe = []
            local_cte = []

            if 'nfe' in tag:
                tipo = "NFe"
                chave = XMLParser.obter_chave(root, ns, "NFe")
                
                # --- [NFe] Cabeçalho ---
                n_nf = XMLParser.pegar_texto(root, './/nfe:ide/nfe:nNF', ns)
                serie = XMLParser.pegar_texto(root, './/nfe:ide/nfe:serie', ns)
                modelo = XMLParser.pegar_texto(root, './/nfe:ide/nfe:mod', ns)
                nat_op = XMLParser.pegar_texto(root, './/nfe:ide/nfe:natOp', ns)
                tp = XMLParser.pegar_texto(root, './/nfe:ide/nfe:tpNF', ns)
                mov = "ENTRADA" if tp == '0' else "SAÍDA" if tp == '1' else tp
                
                # Data e Hora
                data_emi, hora_emi = XMLParser.obter_data_hora(root, ns, "NFe") 
                
                # --- [NFe] Emitente e Destinatário ---
                emit = XMLParser.obter_emitente(root, ns, tipo)
                dest_nome = XMLParser.pegar_texto(root, './/nfe:dest/nfe:xNome', ns)
                dest_doc = XMLParser.pegar_texto(root, './/nfe:dest/nfe:CNPJ', ns) or XMLParser.pegar_texto(root, './/nfe:dest/nfe:CPF', ns)
                
                uf_dest = XMLParser.obter_uf_destinatario(root, ns)
                inf_cpl = XMLParser.obter_inf_complementar(root, ns)
                simples = XMLParser.verificar_simples(root, ns)
                val_xml_total = XMLParser.obter_valor_total_xml(root, ns, tipo)

                # --- [NFe] Itens ---
                for det in root.findall('.//nfe:det', ns):
                    prod = det.find('nfe:prod', ns)
                    trib = XMLParser.extrair_tributos(det, ns)
                    piscof = XMLParser.extrair_pis_cofins(det, ns)
                    ipi_data = XMLParser.extrair_ipi(det, ns)
                    ref = XMLParser.extrair_reforma(det, ns)

                    local_nfe.append({
                        # REMOVIDO: Empresa e Filial
                        "Tipo": tipo,
                        "Mov": mov,
                        "Data Emissão": data_emi,
                        "Hora Emissão": hora_emi,
                        "Modelo": modelo,
                        "Numero NF": n_nf, 
                        "Serie": serie,
                        "Natureza Op.": nat_op,
                        "Fornecedor/Emitente": emit["Nome"],
                        "CNPJ": emit["CNPJ"],
                        "UF Emit.": emit["UF"],
                        "Destinatario/Tomador": dest_nome,
                        "CNPJ/CPF": dest_doc,
                        "UF Destinatario": uf_dest,
                        "Item": det.get('nItem'),
                        "Pedido Compra (xPed)": XMLParser.pegar_texto(prod, 'nfe:xPed', ns),
                        "Item Pedido": XMLParser.pegar_texto(prod, 'nfe:nItemPed', ns),
                        "EAN/GTIN": XMLParser.pegar_texto(prod, 'nfe:cEAN', ns),
                        "Cod": XMLParser.pegar_texto(prod, 'nfe:cProd', ns),
                        "Produto": XMLParser.pegar_texto(prod, 'nfe:xProd', ns),
                        "NCM": XMLParser.pegar_texto(prod, 'nfe:NCM', ns),
                        "CFOP": XMLParser.pegar_texto(prod, 'nfe:CFOP', ns),
                        "Cod. ANP": XMLParser.pegar_texto(prod, 'nfe:comb/nfe:cProdANP', ns),
                        "Unid.": XMLParser.pegar_texto(prod, 'nfe:uCom', ns),
                        "Qtde": XMLParser.pegar_float(prod, 'nfe:qCom', ns),
                        "Valor Unit.": XMLParser.pegar_float(prod, 'nfe:vUnCom', ns),
                        "Valor Desconto": XMLParser.pegar_float(prod, 'nfe:vDesc', ns),
                        "Valor Frete": XMLParser.pegar_float(prod, 'nfe:vFrete', ns),
                        "Valor Seguro": XMLParser.pegar_float(prod, 'nfe:vSeg', ns),
                        "Outras Desp.": XMLParser.pegar_float(prod, 'nfe:vOutro', ns),
                        "Valor Total": XMLParser.pegar_float(prod, 'nfe:vProd', ns),
                        "Valor Total Nota": val_xml_total,
                        # Impostos
                        "Origem": XMLParser.extrair_origem(det, ns),
                        "CST": trib.get("CST", ""),
                        "Simples Nac.": simples,
                        "Credito Simples Nacional": trib.get("CRED", 0.0),
                        "Base Cálc. ICMS": trib.get("BASE", 0.0), "ALIQ. ICMS": trib.get("ALIQ", 0.0), "Valor ICMS": trib.get("VAL", 0.0),
                        "CEST": XMLParser.pegar_texto(prod, 'nfe:CEST', ns),
                        "MVA": trib.get("MVA", 0.0), "Base ST": trib.get("BASE_ST", 0.0), "Aliq. ICMS ST": trib.get("ALIQ_ST", 0.0), 
                        "Red. ST": trib.get("RED_ST", 0.0), "Valor ICMS ST": trib.get("VAL_ST", 0.0),
                        "Base Pis": piscof.get("PIS_BC", 0.0), "CST Pis": piscof.get("PIS_CST", ""), "Aliquota Pis": piscof.get("PIS_ALIQ", 0.0), "Valor Pis": piscof.get("PIS_VAL", 0.0),
                        "Base Cofins": piscof.get("COF_BC", 0.0), "CST Cofins": piscof.get("COF_CST", ""), "Aliquota Cofins": piscof.get("COF_ALIQ", 0.0), "Valor Cofins": piscof.get("COF_VAL", 0.0),
                        "Base IPI": ipi_data.get("IPI_BC", 0.0), "CST IPI": ipi_data.get("IPI_CST", ""), "Aliquota IPI": ipi_data.get("IPI_ALIQ", 0.0), "Valor IPI": ipi_data.get("IPI_VAL", 0.0),
                        "CST Reforma": ref.get("CST", ""), "ClassTrib": ref.get("CLASS", ""), "Base CBS": ref.get("BC_CBS", 0.0), "Aliq. CBS": ref.get("ALIQ_CBS", 0.0), "Valor CBS": ref.get("V_CBS", 0.0), "Base IBS": ref.get("BC_IBS", 0.0), "Aliq. IBS": ref.get("ALIQ_IBS", 0.0), "Valor IBS": ref.get("V_IBS", 0.0),
                        "Dados Complementares": inf_cpl, "Chave de Acesso": f"'{chave}"
                    })

            elif 'cte' in tag:
                tipo = "CTe"
                chave = XMLParser.obter_chave(root, ns, "CTe")
                
                # --- [CTe] Dados Básicos ---
                n_ct = XMLParser.pegar_texto(root, './/cte:ide/cte:nCT', ns)
                serie = XMLParser.pegar_texto(root, './/cte:ide/cte:serie', ns)
                cfop = XMLParser.pegar_texto(root, './/cte:ide/cte:CFOP', ns)
                
                # Data Emissão (Usa a nova função)
                data_emi, hora_emi = XMLParser.obter_data_hora(root, ns, "CTe")
                
                val_total = XMLParser.obter_valor_total_xml(root, ns, tipo)
                dest_nome, dest_doc = XMLParser.obter_pagador_cte(root, ns)
                emit = XMLParser.obter_emitente(root, ns, tipo)
                
                # --- [CTe] Novos Extratores (Logística e Atores) ---
                v_carga, peso, unit_med = XMLParser.obter_dados_carga_cte(root, ns)
                placa, rntrc = XMLParser.obter_modal_rodoviario(root, ns)
                chaves_nfe = XMLParser.obter_chaves_nfe_vinculadas(root, ns)
                rota_dados = XMLParser.obter_rota_e_obs(root, ns)
                atores = XMLParser.obter_atores_cte(root, ns)

                # --- [CTe] ICMS ---
                base_icms = 0.0; aliq_icms = 0.0; val_icms = 0.0
                imp = root.find('.//cte:imp/cte:ICMS', ns)
                if imp:
                    for child in imp:
                        if 'ICMS' in child.tag:
                            base_icms = XMLParser.pegar_float(child, 'cte:vBC', ns)
                            aliq_icms = XMLParser.pegar_float(child, 'cte:pICMS', ns) / 100.0
                            val_icms = XMLParser.pegar_float(child, 'cte:vICMS', ns)
                            if val_icms > 0: break # Pega o primeiro que tiver valor

                local_cte.append({
                    # REMOVIDO: Empresa e Filial
                    "Chave de Acesso": f"'{chave}",
                    "Data Emissão": data_emi,
                    "Numero CTe": n_ct,
                    "Serie": serie,
                    "CFOP": cfop,
                    
                    # Financeiro
                    "Valor Total Frete": val_total,
                    "Valor da Carga": v_carga,
                    "Peso/Qtde": peso,
                    "Unid. Medida": unit_med,
                    
                    # Atores Envolvidos
                    "Tomador (Pagador)": dest_nome,
                    "CNPJ Tomador": dest_doc,
                    "Emitente (Transportadora)": emit["Nome"],
                    "CNPJ Emitente": emit["CNPJ"],
                    "UF Emit.": emit["UF"],
                    
                    # Logística Detalhada
                    "Placa Veículo": placa,
                    "RNTRC": rntrc,
                    "Remetente (Origem)": atores["Remetente_Nome"],
                    "Origem (Mun. Ini)": rota_dados["Inicio"],
                    "UF Origem": rota_dados["UF_Inicio"],
                    "Destinatário (Destino)": atores["Destinatario_Nome"],
                    "Destino (Mun. Fim)": rota_dados["Fim"],
                    "UF Destino": rota_dados["UF_Fim"],
                    "Observações": rota_dados["Obs"],
                    
                    # Tributos
                    "Base Cálc. ICMS": base_icms, 
                    "ALIQ. ICMS": aliq_icms, 
                    "Valor ICMS": val_icms,
                    "NFes Vinculadas": chaves_nfe
                })

            return local_nfe, local_cte

        except Exception as e:
            SistemaLog.registrar_erro(f"Falha ao processar arquivo: {os.path.basename(caminho_arquivo)}", e)
            return [], []

    @staticmethod
    def executar(pasta_xml, caminho_saida, callback_log, callback_progresso, callback_retry=None):
        # 1. Definição do Caminho de Saída (Agora vem do argumento)
        saida = caminho_saida

        # 2. VALIDAÇÃO PRÉVIA
        valid_xml, msg_xml = Validador.validar_pasta_xml(pasta_xml)
        if not valid_xml: raise Exception(msg_xml)

        arqs = [f for f in os.listdir(pasta_xml) if f.lower().endswith('.xml')]
        total = len(arqs)
        
        callback_log(f"Iniciando leitura de {total} arquivos (Modo Simples)...")
        
        lista_nfe = []
        lista_cte = []
        
        # 3. PROCESSAMENTO PARALELO
        with ThreadPoolExecutor() as executor:
            futuros = []
            for f in arqs:
                caminho_completo = os.path.join(pasta_xml, f)
                # Chamada sem o SAP
                futuros.append(executor.submit(ProcessadorFiscal._processar_um_xml, caminho_completo, config.NS_MAP))
            
            for i, futuro in enumerate(as_completed(futuros)):
                nfe, cte = futuro.result()
                
                if nfe: lista_nfe.extend(nfe)
                if cte: lista_cte.extend(cte)
                
                if i % 10 == 0 or i == total - 1:
                    pct = int(((i+1)/total)*100)
                    callback_progresso(pct, f"Processando: {i+1}/{total} ({pct}%)")
        
        # 4. EXPORTAÇÃO
        callback_log("Gerando arquivo Excel...")
        
        while True:
            try:
                # Passamos None para a conciliação
                ExcelReportWriter.gerar_relatorio(
                    saida,
                    None, # df_concilia é None
                    pd.DataFrame(lista_nfe),
                    pd.DataFrame(lista_cte)
                )
                break 
            
            except PermissionError:
                if callback_retry:
                    tenta_de_novo = callback_retry(
                        "Arquivo Aberto", 
                        f"O arquivo Excel parece estar aberto:\n{saida}\n\nPor favor, feche-o e clique em 'Tentar Novamente'."
                    )
                    if tenta_de_novo:
                        callback_log("Tentando salvar novamente...")
                        continue 
                raise Exception("Gravação cancelada: O arquivo Excel estava aberto.")
                
            except Exception as e:
                SistemaLog.registrar_erro("Erro ao salvar Excel final", e)
                raise Exception(f"Erro ao gerar o relatório Excel: {e}")
        
        return saida
