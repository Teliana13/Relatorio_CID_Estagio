import streamlit as st
import pandas as pd
import io
import plotly.express as px

st.set_page_config(page_title="Gestão CID - Auditoria Epidemiológica", layout="wide")

st.title("🏥 Sistema Unificado de Relatórios e Auditoria")
st.markdown("---")

arquivo = st.sidebar.file_uploader("Upload do arquivo .xls (Sistema Hospitalar)", type=["xls"])

if arquivo:
    try:
        # Processamento inicial e limpeza de resíduos (NaN)
        df_bruto = pd.read_excel(arquivo, engine='xlrd', header=None)
        cids = df_bruto[7].astype(str).str.strip().str.upper()
        cids = cids[cids != "NAN"]
        total_planilha = len(cids)

        # ==========================================
        # 1. ABA INFECCIOSAS (Conforme Tabela Original)
        # ==========================================
        mapa_inf = {
            "A00-A059 (Inf. Bacterianas)": ("A00", "A01", "A02", "A03", "A04", "A05"),
            "A08-A085 (Inf. Virais)": ("A08"),
            "A09-A09X (Diarréia/Gastro)": ("A09"),
            "B50-B54 (Inf. Viral N/E)": ("B50", "B51", "B52", "B53", "B54"),
            "B018-B019 (Malaria)": ("B018", "B019"),
            "B269 (Caxumba)": ("B269"),
            "A90-A91 (Varicela)": ("A90", "A91"),
            "B349 (Meningococica)": ("B349"),
            "A15-A19 (Tuberculose)": ("A15", "A16", "A17", "A18", "A19"),
            "A390 (Dengue)": ("A390")
        }
        res_inf = [{"CID": k, "ABRIL": cids.str.startswith(v).sum(), "Grupo": "Infecciosas"} for k, v in mapa_inf.items()]
        df_inf = pd.DataFrame(res_inf)

        # ==========================================
        # 2. ABA RESPIRATÓRIAS (Com Regra J18.0 e J95-J99)
        # ==========================================
        # Lógica para separar Pneumonia de Broncopneumonia
        t_pneu_geral = cids.str.startswith(("J12", "J13", "J14", "J15", "J16", "J17", "J18")).sum()
        bronco = cids.str.startswith(("J180", "J18.0")).sum()
        pneu_liquida = t_pneu_geral - bronco

        mapa_resp = {
            "J00-J00X (Nasofaringite)": ("J00"),
            "J01-J01.9 (Sinusite)": ("J01"),
            "J02-J02.9 (Faringite)": ("J02"),
            "J03-J03.9 (Amigdalite)": ("J03"),
            "J04-J06.9 (Outras Vias Sup.)": ("J04", "J05", "J06"),
            "J30-J39 (Doenças Vias Aéreas)": tuple([f"J{i}" for i in range(30, 40)]),
            "J10-J11.8 (Influenza)": ("J10", "J11"),
            "J18.0 (Broncopneumonia)": ("J180", "J18.0"),
            "J20-J20.9 (Bronquite Aguda)": ("J20"),
            "J21-J21.9 (Bronqueolite)": ("J21"),
            "J45-J46.X (Asma)": ("J45", "J46"),
            "J96-J96.9 (Insuf. Respiratória)": ("J96"),
            "J95-J99 (Outras Respiratórias)": ("J95", "J96", "J97", "J98", "J99")
        }
        res_resp = [{"CID": k, "ABRIL": cids.str.startswith(v).sum(), "Grupo": "Respiratórias"} for k, v in mapa_resp.items()]
        # Inserção da Pneumonia calculada
        res_resp.insert(7, {"CID": "Pneumonia (J12-J18.9 exceto J18.0)", "ABRIL": pneu_liquida, "Grupo": "Respiratórias"})
        df_resp = pd.DataFrame(res_resp)

        # ==========================================
        # 3. ABA CAUSAS EXTERNAS (Versão Completa)
        # ==========================================
        mapa_ext = {
            "W53-W59.9 (Mordedura Animal)": tuple([f"W5{i}" for i in range(3, 10)]),
            "X20-X29 (Acidente Ofídico)": tuple([f"X{i}" for i in range(20, 30)]),
            "V01-V09 (Acidente Trânsito)": tuple([f"V0{i}" for i in range(1, 10)]),
            "W32-W34.9 (Arma de Fogo)": ("W32", "W33", "W34"),
            "W26-W26.9 (Arma Branca)": ("W26"),
            "T20-T32.9 (Queimadura)": tuple([f"T{i}" for i in range(20, 33)]),
            "W69-W75 (Afogamento)": tuple([f"W{i}" for i in range(69, 76)]),
            "X85-Y0.9 (Agressão)": ("X85", "X86", "X87", "X88", "X89", "Y0"),
            "X60-X84 (Suicídio)": tuple([f"X{i}" for i in range(60, 85)]),
            "X40-X49.9 (Envenenamento)": tuple([f"X{i}" for i in range(40, 50)]),
            "T17.2 (Garganta)": ("T172", "T17.2"),
            "T17.0 (Nariz)": ("T170", "T17.0"),
            "T16 (Ouvido)": ("T16"),
            "T15 (Olhos)": ("T15"),
            "W80 (Ingestão/Obstrução)": ("W80"),
            "Y20 (Enforcamento)": ("Y20"),
            "X90 (Intox. Específica)": ("X90"),
            "Y08 (Agressão Sexual/Z044)": ("Y08", "Z044"),
            "A05.9 (Prod. Tóxicos)": ("A059", "A05.9"),
            "W19 (Quedas)": ("W19"),
            "T15-T19.9 (Corpo Estranho Geral)": tuple([f"T{i}" for i in range(15, 20)]),
            "R99 (Óbito S/ Assistência)": ("R99")
        }
        res_ext = [{"CID": k, "ABRIL": cids.str.startswith(v).sum(), "Grupo": "Causas Externas"} for k, v in mapa_ext.items()]
        df_ext = pd.DataFrame(res_ext)

        # ==========================================
        # 4. VALIDAÇÃO E MÉTRICAS
        # ==========================================
        total_contados = df_inf['ABRIL'].sum() + df_resp['ABRIL'].sum() + df_ext['ABRIL'].sum()
        diferenca = total_planilha - total_contados

        st.subheader("🔍 Painel de Validação e Consistência")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Linhas", total_planilha)
        c2.metric("Total Classificado", total_contados)
        c3.metric("Não Classificados (Outros)", diferenca, delta_color="inverse")

        if diferenca > 0:
            st.info(f"💡 Existem {diferenca} registros que não se enquadram nestas três categorias (ex: Cardiologia, Obstetrícia, etc).")

        # Exibição das Abas
        aba1, aba2, aba3, aba4 = st.tabs(["Infecciosas", "Respiratórias", "Causas Externas", "📈 Dashboard"])
        
        with aba1: st.table(df_inf[["CID", "ABRIL"]])
        with aba2: st.table(df_resp[["CID", "ABRIL"]])
        with aba3: st.table(df_ext[["CID", "ABRIL"]])
        
        with aba4:
            st.subheader("Visualização Epidemiológica")
            df_geral = pd.concat([df_inf, df_resp, df_ext]).rename(columns={"ABRIL": "Casos", "CID": "Patologia"})
            df_geral = df_geral[df_geral["Casos"] > 0].sort_values(by="Casos", ascending=False)

            col_a, col_b = st.columns(2)
            with col_a:
                fig_bar = px.bar(df_geral.head(15), x="Casos", y="Patologia", color="Grupo", 
                                 title="Top 15 Patologias Detectadas", orientation='h', text_auto=True)
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col_b:
                fig_pie = px.pie(df_geral, values='Casos', names='Grupo', hole=0.4, title="Distribuição por Grande Grupo")
                st.plotly_chart(fig_pie, use_container_width=True)

    except Exception as e:
        st.error(f"Ocorreu um erro no processamento: {e}")
else:
    st.info("Aguardando upload do arquivo .xls para iniciar a análise.")
