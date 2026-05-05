import streamlit as st
import pandas as pd
import io

# Configuração visual
st.set_page_config(page_title="Relatórios CID - Estágio", layout="wide")

st.title("📊 Sistema de Processamento de Relatórios CID")
st.markdown("---")

# Menu Lateral
st.sidebar.header("Configurações")
arquivo_subido = st.sidebar.file_uploader("Suba o arquivo .xls aqui", type=["xls"])

if arquivo_subido:
    try:
        # Leitura dos dados (O motor 'xlrd' será instalado via requirements.txt)
        df_bruto = pd.read_excel(arquivo_subido, engine='xlrd', header=None)
        coluna_cid = df_bruto[7].astype(str).str.strip().str.upper()

        # Organização por Abas
        aba1, aba2, aba3 = st.tabs(["Infecciosas", "Respiratórias", "Causas Externas"])

        # --- ABA 1: DOENÇAS INFECCIOSAS ---
        with aba1:
            st.subheader("Tabela: Doenças Infecciosas")
            # Dicionário fiel à sua tabela original
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
            
            res_inf = []
            for cid_ref, prefixos in mapa_inf.items():
                contagem = coluna_cid.str.startswith(prefixos).sum()
                res_inf.append({"CID": cid_ref, "ABRIL": contagem})
            
            df_inf = pd.DataFrame(res_inf)
            st.dataframe(df_inf, use_container_width=True)

        # --- ABA 2: RESPIRATÓRIAS ---
        with aba2:
            st.subheader("Tabela: Doenças do Aparelho Respiratório")
            mapa_resp = {
                "J00": ("J00"),
                "J01": ("J01"),
                "J12-J18": ("J12", "J13", "J14", "J15", "J16", "J17", "J18"),
                "J18.0 (Broncopneumonia)": ("J180", "J18.0"),
                "J45-J46": ("J45", "J46")
            }
            res_resp = [{"CID": k, "ABRIL": coluna_cid.str.startswith(v).sum()} for k, v in mapa_resp.items()]
            st.dataframe(pd.DataFrame(res_resp), use_container_width=True)

        # --- ABA 3: CAUSAS EXTERNAS ---
        with aba3:
            st.subheader("Tabela: Causas Externas")
            mapa_ext = {
                "W19 (Quedas)": ("W19"),
                "W53-W59 (Mordeduras)": ("W53", "W54", "W55", "W56", "W57", "W58", "W59"),
                "X60-X84 (Suicídio)": tuple([f"X{i}" for i in range(60, 85)])
            }
            res_ext = [{"Categoria": k, "ABRIL": coluna_cid.str.startswith(v).sum()} for k, v in mapa_ext.items()]
            st.dataframe(pd.DataFrame(res_ext), use_container_width=True)

        st.success("Processamento concluído! Você pode copiar os dados acima para sua planilha.")

    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
else:
    st.info("Aguardando o upload do arquivo .xls no menu lateral.")
