# Arquivo: core/xml_parser.py
import xml.etree.ElementTree as ET
import re

class XMLParser:
    
    @staticmethod
    def pegar_texto(elemento: ET.Element, caminho: str, ns: dict) -> str:
        if elemento is None: return ""
        try:
            node = elemento.find(caminho, ns)
            if node is not None and node.text:
                return str(node.text).strip()
            return ""
        except:
            return ""

    @staticmethod
    def pegar_float(elemento: ET.Element, caminho: str, ns: dict) -> float:
        txt = XMLParser.pegar_texto(elemento, caminho, ns)
        if not txt: return 0.0
        try:
            return float(txt)
        except:
            return 0.0

    @staticmethod
    def obter_chave(root: ET.Element, ns: dict, tipo="NFe") -> str:
        try:
            # Tenta pegar pelo atributo Id da tag infNFe/infCte
            tag_inf = './/nfe:infNFe' if tipo == "NFe" else './/cte:infCte'
            inf = root.find(tag_inf, ns)
            
            if inf is not None:
                chave_suja = inf.get('Id', '')
                return re.sub(r'\D', '', chave_suja)
            
            # Fallback para XMLs de protocolo/distribuição
            tag_prot = f'.//nfe:prot{tipo}/nfe:infProt/nfe:ch{tipo}'
            prot = root.find(tag_prot, ns)
            if prot is not None and prot.text:
                return prot.text.strip()
            return ""
        except:
            return ""

    @staticmethod
    def obter_emitente(root: ET.Element, ns: dict, tipo="NFe") -> dict:
        dados = {"Nome": "", "CNPJ": "", "UF": ""}
        try:
            prefix = "nfe" if tipo == "NFe" else "cte"
            emit = root.find(f'.//{prefix}:emit', ns)
            if emit is not None:
                dados["Nome"] = XMLParser.pegar_texto(emit, f'{prefix}:xNome', ns)
                dados["CNPJ"] = XMLParser.pegar_texto(emit, f'{prefix}:CNPJ', ns) or \
                                XMLParser.pegar_texto(emit, f'{prefix}:CPF', ns)
                
                ender = emit.find(f'{prefix}:enderEmit', ns)
                if ender is not None:
                    dados["UF"] = XMLParser.pegar_texto(ender, f'{prefix}:UF', ns)
        except: pass
        return dados
    
    @staticmethod
    def obter_uf_destinatario(root: ET.Element, ns: dict) -> str:
        try:
            dest = root.find('.//nfe:dest', ns)
            if dest:
                ender = dest.find('nfe:enderDest', ns)
                if ender: return XMLParser.pegar_texto(ender, 'nfe:UF', ns)
        except: pass
        return ""

    @staticmethod
    def obter_valor_total_xml(root: ET.Element, ns: dict, tipo="NFe") -> float:
        if tipo == "NFe":
            return XMLParser.pegar_float(root, './/nfe:total/nfe:ICMSTot/nfe:vNF', ns)
        else:
            # CTe: Valor Total da Prestação
            vprest = root.find('.//cte:vPrest', ns)
            if vprest is not None:
                return XMLParser.pegar_float(vprest, 'cte:vTPrest', ns)
        return 0.0

    @staticmethod
    def obter_inf_complementar(root: ET.Element, ns: dict) -> str:
        return XMLParser.pegar_texto(root, './/nfe:infAdic/nfe:infCpl', ns)

    @staticmethod
    def verificar_simples(root: ET.Element, ns: dict) -> str:
        crt = XMLParser.pegar_texto(root, './/nfe:emit/nfe:CRT', ns)
        return "Sim" if crt == '1' else "Não"

    @staticmethod
    def extrair_tributos(det: ET.Element, ns: dict) -> dict:
        dados = {}
        imposto = det.find('nfe:imposto', ns)
        if not imposto: return dados
        
        icms = imposto.find('nfe:ICMS', ns)
        if icms:
            for child in icms:
                if 'ICMS' in child.tag:
                    dados["CST"] = XMLParser.pegar_texto(child, 'nfe:CST', ns) or XMLParser.pegar_texto(child, 'nfe:CSOSN', ns)
                    dados["BASE"] = XMLParser.pegar_float(child, 'nfe:vBC', ns)
                    dados["ALIQ"] = XMLParser.pegar_float(child, 'nfe:pICMS', ns) / 100
                    dados["VAL"] = XMLParser.pegar_float(child, 'nfe:vICMS', ns)
                    
                    # Substituição Tributária (ST)
                    dados["MVA"] = XMLParser.pegar_float(child, 'nfe:pMVAST', ns) / 100
                    dados["BASE_ST"] = XMLParser.pegar_float(child, 'nfe:vBCST', ns)
                    dados["ALIQ_ST"] = XMLParser.pegar_float(child, 'nfe:pICMSST', ns) / 100
                    dados["VAL_ST"] = XMLParser.pegar_float(child, 'nfe:vICMSST', ns)
                    
                    # Lógica de Redução BC ST
                    raw_red_st = XMLParser.pegar_float(child, 'nfe:pRedBCST', ns)
                    if raw_red_st == 1.0:
                        dados["RED_ST"] = 0.0
                    elif 0.0 < raw_red_st < 1.0:
                        dados["RED_ST"] = 1.0 - raw_red_st
                    else:
                        dados["RED_ST"] = raw_red_st / 100
                    
                    dados["CRED"] = XMLParser.pegar_float(child, 'nfe:vCredICMSSN', ns)
                    break
        return dados
    
    @staticmethod
    def extrair_reforma(det, ns):
        """
        Extrai dados da Reforma Tributária (CBS/IBS) para atender ao processador.
        Chaves geradas: CST, CLASS, BC_CBS, ALIQ_CBS, V_CBS, BC_IBS, ALIQ_IBS, V_IBS
        """
        dados = {}
        imposto = det.find('nfe:imposto', ns)
        if not imposto: return dados
        
        # --- 1. Busca CBS (Contribuição sobre Bens e Serviços) ---
        cbs = imposto.find('nfe:CBS', ns)
        if cbs:
            # Procura CST dentro de subgrupos da CBS (ex: CBS01, CBS02...)
            # Como a tag muda (nfe:CBS01, nfe:CBS02), iteramos nos filhos
            for child in cbs:
                dados["CST"] = XMLParser.pegar_texto(child, 'nfe:CST', ns)
                dados["CLASS"] = XMLParser.pegar_texto(child, 'nfe:cClass', ns) # Tenta achar Classificação
                dados["BC_CBS"] = XMLParser.pegar_float(child, 'nfe:vBC', ns)
                dados["ALIQ_CBS"] = XMLParser.pegar_float(child, 'nfe:pAliq', ns) / 100
                dados["V_CBS"] = XMLParser.pegar_float(child, 'nfe:vCBS', ns)
                if "CST" in dados: break # Se achou, para.

        # --- 2. Busca IBS (Imposto sobre Bens e Serviços) ---
        ibs = imposto.find('nfe:IBS', ns)
        if ibs:
            for child in ibs:
                dados["BC_IBS"] = XMLParser.pegar_float(child, 'nfe:vBC', ns)
                dados["ALIQ_IBS"] = XMLParser.pegar_float(child, 'nfe:pAliq', ns) / 100
                dados["V_IBS"] = XMLParser.pegar_float(child, 'nfe:vIBS', ns)
                
                # Se não achou CLASS na CBS, tenta no IBS
                if "CLASS" not in dados:
                     dados["CLASS"] = XMLParser.pegar_texto(child, 'nfe:cClass', ns)
                if "vBC" in str(child.tag) or "vIBS" in str(child.tag): break

        return dados

    @staticmethod
    def extrair_pis_cofins(det: ET.Element, ns: dict) -> dict:
        dados = {}
        imposto = det.find('nfe:imposto', ns)
        if not imposto: return dados
        
        pis = imposto.find('nfe:PIS', ns)
        if pis:
            for child in pis:
                dados["PIS_CST"] = XMLParser.pegar_texto(child, 'nfe:CST', ns)
                dados["PIS_BC"] = XMLParser.pegar_float(child, 'nfe:vBC', ns)
                dados["PIS_ALIQ"] = XMLParser.pegar_float(child, 'nfe:pPIS', ns) / 100
                dados["PIS_VAL"] = XMLParser.pegar_float(child, 'nfe:vPIS', ns)
                if "CST" in dados: break
        
        cof = imposto.find('nfe:COFINS', ns)
        if cof:
            for child in cof:
                dados["COF_CST"] = XMLParser.pegar_texto(child, 'nfe:CST', ns)
                dados["COF_BC"] = XMLParser.pegar_float(child, 'nfe:vBC', ns)
                dados["COF_ALIQ"] = XMLParser.pegar_float(child, 'nfe:pCOFINS', ns) / 100
                dados["COF_VAL"] = XMLParser.pegar_float(child, 'nfe:vCOFINS', ns)
                if "CST" in dados: break
        return dados

    @staticmethod
    def extrair_ipi(det: ET.Element, ns: dict) -> dict:
        dados = {}
        ipi = det.find('.//nfe:imposto/nfe:IPI', ns)
        if ipi:
            ipitrib = ipi.find('nfe:IPITrib', ns)
            if ipitrib:
                dados["IPI_CST"] = XMLParser.pegar_texto(ipitrib, 'nfe:CST', ns)
                dados["IPI_BC"] = XMLParser.pegar_float(ipitrib, 'nfe:vBC', ns)
                dados["IPI_ALIQ"] = XMLParser.pegar_float(ipitrib, 'nfe:pIPI', ns) / 100
                dados["IPI_VAL"] = XMLParser.pegar_float(ipitrib, 'nfe:vIPI', ns)
        return dados

    @staticmethod
    def obter_pagador_cte(root: ET.Element, ns: dict):
        toma = root.find('.//cte:ide/cte:toma3', ns)
        toma4 = root.find('.//cte:ide/cte:toma4', ns)
        
        toma_ele = None
        if toma: 
            toma_tag = toma.find('cte:toma', ns)
            tipo = toma_tag.text if toma_tag is not None else '0'
            # 0: Remetente, 1: Expedidor, 2: Recebedor, 3: Destinatário
            mapa = {'0': 'rem', '1': 'exped', '2': 'receb', '3': 'dest'}
            role = mapa.get(tipo, 'rem')
            toma_ele = root.find(f'.//cte:{role}', ns)
        elif toma4:
            toma_ele = toma4
            
        nome = ""
        doc = ""
        if toma_ele:
            nome = XMLParser.pegar_texto(toma_ele, 'cte:xNome', ns)
            doc = XMLParser.pegar_texto(toma_ele, 'cte:CNPJ', ns) or XMLParser.pegar_texto(toma_ele, 'cte:CPF', ns)
            
        return nome, doc

    @staticmethod
    def extrair_origem(node: ET.Element, ns: dict) -> str:
        imp = node.find('nfe:imposto', ns)
        if not imp: return ""
        icms = imp.find('nfe:ICMS', ns)
        if not icms: return ""
        
        for child in icms:
            orig = XMLParser.pegar_texto(child, 'nfe:orig', ns)
            if orig: return orig
        return ""
    
    @staticmethod
    def obter_data_hora(root: ET.Element, ns: dict, tipo="NFe"):
        prefix = "nfe" if tipo == "NFe" else "cte"
        raw = XMLParser.pegar_texto(root, f'.//{prefix}:ide/{prefix}:dhEmi', ns)
        
        if 'T' in raw:
            try:
                data_iso, hora_full = raw.split('T')
                data_fmt = data_iso
                if len(data_iso) == 10:
                    data_fmt = f"{data_iso[8:10]}/{data_iso[5:7]}/{data_iso[0:4]}"
                hora_fmt = hora_full[:8]
                return data_fmt, hora_fmt
            except:
                pass
        return "", ""

    @staticmethod
    def obter_dados_carga_cte(root: ET.Element, ns: dict):
        v_carga = 0.0
        peso = 0.0
        unidade_medida = ""

        try:
            vc = root.find('.//cte:infCarga', ns)
            if vc is not None:
                v_carga = XMLParser.pegar_float(vc, 'cte:vCarga', ns)

            infos_q = root.findall('.//cte:infCarga/cte:infQ', ns)
            for inf in infos_q:
                q_carga = XMLParser.pegar_float(inf, 'cte:qCarga', ns)
                tp_med = XMLParser.pegar_texto(inf, 'cte:tpMed', ns).upper()
                
                if 'KG' in tp_med or 'PESO' in tp_med:
                    peso = q_carga
                    unidade_medida = tp_med
                    break
                
                if q_carga > 0:
                    peso = q_carga
                    unidade_medida = tp_med

        except: pass
        return v_carga, peso, unidade_medida

    @staticmethod
    def obter_modal_rodoviario(root: ET.Element, ns: dict):
        """Retorna (Placa, RNTRC)."""
        placa = ""
        rntrc = ""
        try:
            rodo = root.find('.//cte:rodo', ns)
            if rodo:
                rntrc = XMLParser.pegar_texto(rodo, 'cte:RNTRC', ns)
                veic = rodo.find('cte:veic', ns)
                if veic:
                    placa = XMLParser.pegar_texto(veic, 'cte:placa', ns)
        except: pass
        return placa, rntrc

    @staticmethod
    def obter_chaves_nfe_vinculadas(root: ET.Element, ns: dict) -> str:
        chaves = []
        try:
            docs = root.findall('.//cte:infDoc/cte:infNFe', ns)
            for doc in docs:
                ch = XMLParser.pegar_texto(doc, 'cte:chave', ns)
                if ch: chaves.append(ch)
        except: pass
        return "; ".join(chaves)

    @staticmethod
    def obter_rota_e_obs(root: ET.Element, ns: dict) -> dict:
        rota = {"Inicio": "", "UF_Inicio": "", "Fim": "", "UF_Fim": "", "Obs": ""}
        try:
            rota["Inicio"] = XMLParser.pegar_texto(root, './/cte:ide/cte:xMunIni', ns)
            rota["UF_Inicio"] = XMLParser.pegar_texto(root, './/cte:ide/cte:UFIni', ns)
            
            rota["Fim"] = XMLParser.pegar_texto(root, './/cte:ide/cte:xMunFim', ns)
            rota["UF_Fim"] = XMLParser.pegar_texto(root, './/cte:ide/cte:UFFim', ns)
            
            obs = root.find('.//cte:compl', ns)
            if obs is not None:
                rota["Obs"] = XMLParser.pegar_texto(obs, 'cte:xObs', ns)
        except: pass
        return rota
    
    @staticmethod
    def obter_atores_cte(root: ET.Element, ns: dict) -> dict:
        atores = {
            "Remetente_Nome": "", "Remetente_CNPJ": "",
            "Destinatario_Nome": "", "Destinatario_CNPJ": ""
        }
        try:
            rem = root.find('.//cte:rem', ns)
            if rem:
                atores["Remetente_Nome"] = XMLParser.pegar_texto(rem, 'cte:xNome', ns)
                atores["Remetente_CNPJ"] = XMLParser.pegar_texto(rem, 'cte:CNPJ', ns) or XMLParser.pegar_texto(rem, 'cte:CPF', ns)

            dest = root.find('.//cte:dest', ns)
            if dest:
                atores["Destinatario_Nome"] = XMLParser.pegar_texto(dest, 'cte:xNome', ns)
                atores["Destinatario_CNPJ"] = XMLParser.pegar_texto(dest, 'cte:CNPJ', ns) or XMLParser.pegar_texto(dest, 'cte:CPF', ns)
        except: pass
        return atores