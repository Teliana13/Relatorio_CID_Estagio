import streamlit as st
import pandas as pd
import io
import plotly.express as px

st.set_page_config(page_title="Gestão CID - Auditoria Epidemiológica", layout="wide")

st.title("🏥 Sistema Unificado de Relatórios, Auditoria e Download")
st.markdown("---")

arquivo = st.sidebar.file_uploader("Upload do arquivo .xls (Sistema Hospitalar)", type=["xls"])

if arquivo:
    try:
        # Processamento inicial
        df_bruto = pd.read_excel(arquivo, engine='xlrd', header=None)
        cids = df_bruto[7].astype(str).str.strip().str.upper()
        cids = cids[cids != "NAN"]
        total_planilha = len(cids)

        # ==========================================
        # 1. PROCESSAMENTO DAS TABELAS (LÓGICA COMPLETA)
        # ==========================================
        
        # --- INFECCIOSAS ---
        mapa_inf = {
            "A00-A059 (Inf. Bacterianas)": ("A00", "A01", "A02", "A03", "A04", "A05"),
            "A08-A085 (Inf. Virais)": ("A08"), "A09-A09X (Diarréia)": ("A09"),
            "B50-B54 (Inf. Viral N/E)": ("B50", "B51", "B52", "B53", "B54"),
            "B018-B019 (Malaria)": ("B018", "B019"), "B269 (Caxumba)": ("B269"),
            "A90-A91 (Varicela)": ("A90", "A91"), "B349 (Meningococica)": ("B349"),
            "A15-A19 (Tuberculose)": ("A15", "A16", "A17", "A18", "A19"), "A390 (Dengue)": ("A390")
        }
        df_inf = pd.DataFrame([{"CID": k, "ABRIL": cids.str.startswith(v).sum(), "Grupo": "Infecciosas"} for k, v in mapa_inf.items()])

        # --- RESPIRATÓRIAS ---
        t_pneu_geral = cids.str.startswith(("J12", "J13", "J14", "J15", "J16", "J17", "J18")).sum()
        bronco = cids.str.startswith(("J180", "J18.0")).sum()
        pneu_liquida = t_pneu_geral - bronco
        mapa_resp = {
            "J00-J00X": ("J00"), "J01-J01.9": ("J01"), "J02-J02.9": ("J02"), "J03-J03.9": ("J03"),
            "J04-J06.9": ("J04", "J05", "J06"), "J30-J39": tuple([f"J{i}" for i in range(30, 40)]),
            "J10-J11.8": ("J10", "J11"), "J18.0 (Broncopneumonia)": ("J180", "J18.0"),
            "J20-J20.9": ("J20"), "J21-J21.9": ("J21"), "J45-J46.X": ("J45", "J46"), 
            "J96-J96.9": ("J96"), "J95-J99 (Outras)": ("J95", "J96", "J97", "J98", "J99")
        }
        res_resp = [{"CID": k, "ABRIL": cids.str.startswith(v).sum(), "Grupo": "Respiratórias"} for k, v in mapa_resp.items()]
        res_resp.insert(7, {"CID": "Pneumonia (J12-J18.9 exceto J18.0)", "ABRIL": pneu_liquida, "Grupo": "Respiratórias"})
        df_resp = pd.DataFrame(res_resp)

        # --- CAUSAS EXTERNAS ---
        mapa_ext = {
            "W53-W59.9 (Mordedura)": tuple([f"W5{i}" for i in range(3, 10)]),
            "X20-X29 (Ac. Ofídico)": tuple([f"X{i}" for i in range(20, 30)]),
            "V01-V09 (Trânsito)": tuple([f"V0{i}" for i in range(1, 10)]),
            "W32-W34.9 (Arma Fogo)": ("W32", "W33", "W34"), "W26 (Arma Branca)": ("W26"),
            "T20-T32.9 (Queimadura)": tuple([f"T{i}" for i in range(20, 33)]),
            "X60-X84 (Suicídio)": tuple([f"X{i}" for i in range(60, 85)]), "W19 (Quedas)": ("W19"),
            "R99 (Óbito S/ Assist.)": ("R99")
        }
        df_ext = pd.DataFrame([{"CID": k, "ABRIL": cids.str.startswith(v).sum(), "Grupo": "Causas Externas"} for k, v in mapa_ext.items()])

        # ==========================================
        # 2. VALIDAÇÃO E BOTÃO DE DOWNLOAD
        # ==========================================
        total_contados = df_inf['ABRIL'].sum() + df_resp['ABRIL'].sum() + df_ext['ABRIL'].sum()
        diferenca = total_planilha - total_contados

        st.subheader("🔍 Painel de Validação")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total da Planilha", total_planilha)
        c2.metric("Total Classificado", total_contados)
        c3.metric("Não Classificados", diferenca)

        # LÓGICA DE DOWNLOAD (Cria Excel com 3 Abas)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_inf[["CID", "ABRIL"]].to_excel(writer, sheet_name='Infecciosas', index=False)
            df_resp[["CID", "ABRIL"]].to_excel(writer, sheet_name='Respiratórias', index=False)
            df_ext[["CID", "ABRIL"]].to_excel(writer, sheet_name='Causas Externas', index=False)
        
        st.download_button(
            label="📥 Baixar Planilha Completa (3 Abas)",
            data=buffer.getvalue(),
            file_name="Relatorio_Epidemiologico_Final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # ==========================================
        # 3. EXIBIÇÃO DAS ABAS E GRÁFICOS
        # ==========================================
        tab1, tab2, tab3, tab4 = st.tabs(["Infecciosas", "Respiratórias", "Causas Externas", "📈 Dashboard"])
        
        with tab1: st.table(df_inf[["CID", "ABRIL"]])
        with tab2: st.table(df_resp[["CID", "ABRIL"]])
        with tab3: st.table(df_ext[["CID", "ABRIL"]])
        
        with tab4:
            df_geral = pd.concat([df_inf, df_resp, df_ext]).rename(columns={"ABRIL": "Casos", "CID": "Patologia"})
            df_geral = df_geral[df_geral["Casos"] > 0].sort_values(by="Casos", ascending=False)
            col_a, col_b = st.columns(2)
            with col_a:
                st.plotly_chart(px.bar(df_geral.head(10), x="Casos", y="Patologia", color="Grupo", orientation='h', title="Top 10 Patologias"), use_container_width=True)
            with col_b:
                st.plotly_chart(px.pie(df_geral, values='Casos', names='Grupo', hole=0.4, title="Distribuição por Grupo"), use_container_width=True)

    except Exception as e:
        st.error(f"Erro: {e}")
else:
    st.info("Aguardando arquivo .xls para iniciar.")
