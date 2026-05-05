import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Relatórios CID - Estágio UFAM", layout="wide")

st.title("📊 Processamento Automático de Relatórios")
st.markdown("---")

arquivo = st.sidebar.file_uploader("Suba o arquivo .xls de Abril aqui", type=["xls"])

if arquivo:
    try:
        # Leitura e limpeza básica
        df_bruto = pd.read_excel(arquivo, engine='xlrd', header=None)
        # O CID costuma estar na coluna 8 (índice 7)
        cids = df_bruto[7].astype(str).str.strip().str.upper()

        aba1, aba2, aba3 = st.tabs(["Infecciosas", "Respiratórias", "Causas Externas"])

        # --- ABA 1: INFECCIOSAS ---
        with aba1:
            st.subheader("Doenças Infecciosas")
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
            st.table(pd.DataFrame(res_inf))

        # --- ABA 2: RESPIRATÓRIAS (VERSÃO COMPLETA) ---
        with aba2:
            st.subheader("Doenças do Aparelho Respiratório")
            
            # Lógica especial para Pneumonia que exclui Broncopneumonia
            total_j12_j18 = cids.str.startswith(("J12", "J13", "J14", "J15", "J16", "J17", "J18")).sum()
            broncopneumonia = cids.str.startswith(("J180", "J18.0")).sum()
            pneumonia_final = total_j12_j18 - broncopneumonia

            mapa_resp = {
                "J00-J00X (Nasofaringite)": ("J00"),
                "J01-J01.9 (Sinusite)": ("J01"),
                "J02-J02.9 (Faringite)": ("J02"),
                "J03-J03.9 (Amigdalite)": ("J03"),
                "J04-J06.9 (Outras Vias Superiores)": ("J04", "J05", "J06"),
                "J30-J39 (Outras Doenças Vias Aéreas)": tuple([f"J{i}" for i in range(30, 40)]),
                "J10-J11.8 (Influenza)": ("J10", "J11"),
                "J18.0 (Broncopneumonia)": ("J180", "J18.0"),
                "J20-J20.9 (Bronquite Aguda)": ("J20"),
                "J21-J21.9 (Bronqueolite Aguda)": ("J21"),
                "J45-J46.X (Asma)": ("J45", "J46"),
                "J96-J96.9 (Insuficiência Respiratória)": ("J96")
            }
            
            res_resp = []
            for k, v in mapa_resp.items():
                res_resp.append({"CID": k, "ABRIL": cids.str.startswith(v).sum()})
            
            # Adiciona a Pneumonia calculada manualmente na lista
            res_resp.insert(7, {"CID": "(J12 a J18.9) - J18.0 (Pneumonia)", "ABRIL": pneumonia_final})
            
            st.table(pd.DataFrame(res_resp))

        # --- ABA 3: CAUSAS EXTERNAS (VERSÃO COMPLETA) ---
        with aba3:
            st.subheader("Causas Externas")
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
                "T17.2 (C. Estrangeiro Garganta)": ("T172", "T17.2"),
                "T17.0 (C. Estrangeiro Nariz)": ("T170", "T17.0"),
                "T16 (C. Estrangeiro Ouvido)": ("T16"),
                "T15 (C. Estrangeiro Olhos)": ("T15"),
                "W80 (C. Estrangeiro Ingestão)": ("W80"),
                "Y20 (Enforcamento)": ("Y20"),
                "X90 (Envenenamento Específico)": ("X90"),
                "Y08 (Estupro/Agressão)": ("Y08", "Z044"),
                "A05.9 (Ing. Prod. Tóxicos)": ("A059", "A05.9"),
                "W19 (Quedas)": ("W19"),
                "T15-T19.9 (Corpo Estranho Geral)": tuple([f"T{i}" for i in range(15, 20)])
            }
            
            res_ext = [{"Categoria": k, "ABRIL": cids.str.startswith(v).sum()} for k, v in mapa_ext.items()]
            st.table(pd.DataFrame(res_ext))

        st.success("✅ Todas as tabelas foram atualizadas com as siglas oficiais!")

    except Exception as e:
        st.error(f"Erro no processamento: {e}")
else:
    st.info("Aguardando upload do arquivo para processar as 3 abas oficiais.")
