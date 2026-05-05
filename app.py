import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Relatórios CID - Auditoria UFAM", layout="wide")

st.title("📊 Processamento e Auditoria de Relatórios")
st.markdown("---")

arquivo = st.sidebar.file_uploader("Suba o arquivo .xls aqui", type=["xls"])

if arquivo:
    try:
        # 1. Leitura e Limpeza
        df_bruto = pd.read_excel(arquivo, engine='xlrd', header=None)
        # Filtramos apenas linhas que possuem algo na coluna do CID (índice 7)
        cids = df_bruto[7].astype(str).str.strip().str.upper()
        cids = cids[cids != "NAN"] # Remove células vazias
        
        total_planilha = len(cids)

        # --- PROCESSAMENTO DAS TABELAS ---
        
        # ABA 1: INFECCIOSAS
        mapa_inf = {
            "A00-A059": ("A00", "A01", "A02", "A03", "A04", "A05"),
            "A08-A085": ("A08"),
            "A09-A09X": ("A09"),
            "B50-B54": ("B50", "B51", "B52", "B53", "B54"),
            "B018-B019": ("B018", "B019"),
            "B269": ("B269"),
            "A90-A91": ("A90", "A91"),
            "B349": ("B349"),
            "A15-A19": ("A15", "A16", "A17", "A18", "A19"),
            "A390": ("A390")
        }
        res_inf = [{"CID": k, "ABRIL": cids.str.startswith(v).sum()} for k, v in mapa_inf.items()]
        df_inf = pd.DataFrame(res_inf)

        # ABA 2: RESPIRATÓRIAS
        total_j12_j18 = cids.str.startswith(("J12", "J13", "J14", "J15", "J16", "J17", "J18")).sum()
        bronco = cids.str.startswith(("J180", "J18.0")).sum()
        pneu = total_j12_j18 - bronco

        mapa_resp = {
            "J00-J00X": ("J00"), "J01-J01.9": ("J01"), "J02-J02.9": ("J02"), "J03-J03.9": ("J03"),
            "J04-J06.9": ("J04", "J05", "J06"), "J30-J39": tuple([f"J{i}" for i in range(30, 40)]),
            "J10-J11.8": ("J10", "J11"), "J18.0": ("J180", "J18.0"), "J20-J20.9": ("J20"),
            "J21-J21.9": ("J21"), "J45-J46.X": ("J45", "J46"), "J96-J96.9": ("J96"),
            "Outras (J95-J99)": ("J95", "J96", "J97", "J98", "J99") # Adicionado conforme pedido
        }
        res_resp = [{"CID": k, "ABRIL": cids.str.startswith(v).sum()} for k, v in mapa_resp.items()]
        res_resp.insert(7, {"CID": "Pneumonia (J12-J18.9 exceto J18.0)", "ABRIL": pneu})
        df_resp = pd.DataFrame(res_resp)

        # ABA 3: CAUSAS EXTERNAS
        mapa_ext = {
            "W53-W59.9": tuple([f"W5{i}" for i in range(3, 10)]),
            "X20-X29": tuple([f"X{i}" for i in range(20, 30)]),
            "V01-V09": tuple([f"V0{i}" for i in range(1, 10)]),
            "X60-X84": tuple([f"X{i}" for i in range(60, 85)]),
            "W19": ("W19")
        }
        res_ext = [{"Categoria": k, "ABRIL": cids.str.startswith(v).sum()} for k, v in mapa_ext.items()]
        df_ext = pd.DataFrame(res_ext)

        # --- VALIDAÇÃO (O NOVO CORAÇÃO DO APP) ---
        total_contados = df_inf['ABRIL'].sum() + df_resp['ABRIL'].sum() + df_ext['ABRIL'].sum()
        diferenca = total_planilha - total_contados

        st.subheader("🔍 Validação de Dados")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Linhas (Planilha)", total_planilha)
        col2.metric("Total Classificado", total_contados)
        col3.metric("Não Classificados (Outros)", diferenca, delta_color="inverse")

        if diferenca > 0:
            st.warning(f"Atenção: Existem {diferenca} registros que não entraram em nenhuma categoria acima.")

        # --- EXIBIÇÃO DAS ABAS ---
        aba_inf, aba_resp, aba_ext = st.tabs(["Infecciosas", "Respiratórias", "Causas Externas"])
        with aba_inf: st.table(df_inf)
        with aba_resp: st.table(df_resp)
        with aba_ext: st.table(df_ext)

    except Exception as e:
        st.error(f"Erro: {e}")
else:
    st.info("Suba o arquivo para iniciar a auditoria.")
