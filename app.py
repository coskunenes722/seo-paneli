import streamlit as st
from openai import OpenAI
import plotly.graph_objects as go
import re

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="VetraPos Strateji Merkezi", layout="wide", page_icon="🛡️")

# --- 2. API YAPILANDIRMASI ---
OPENAI_KEY = "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"
client = OpenAI(api_key=OPENAI_KEY)

# --- 3. ZEKA FONKSİYONLARI ---
def analiz_ve_yol_haritasi(marka, sektor):
    try:
        # Puanlama
        p_prompt = f"'{marka}' ({sektor}) markasının dijital ağırlığını 0-100 arası puanla. Sadece rakam."
        p_res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": p_prompt}], timeout=10).choices[0].message.content
        puan = int(''.join(filter(str.isdigit, p_res)))

        # Strateji & Yol Haritası
        combined_prompt = f"Marka: {marka} ({sektor}). AI Skoru: {puan}. Bu skoru yükseltmek için 3 somut strateji yaz."
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": combined_prompt}], timeout=15).choices[0].message.content
        
        return puan, res
    except Exception as e:
        return 0, f"Bağlantı veya Kota Sorunu: {str(e)}"

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Operasyon Paneli")
    marka_adi = st.text_input("Markanız", "VetraPos")
    sektor_adi = st.text_input("Sektör", "Sanal POS")
    st.divider()
    nav = st.radio("Navigasyon", ["📊 Dashboard", "✍️ İçerik Üretimi"])

# --- 5. DASHBOARD (TASARIM DÜZELTİLDİ) ---
if nav == "📊 Dashboard":
    st.markdown(f"<h1 style='text-align: center; color: #1E3A8A;'>🛡️ {marka_adi} Analiz Merkezi</h1>", unsafe_allow_html=True)
    
    if st.button("🔄 Verileri Derinlemesine Güncelle", use_container_width=True) or "puan" not in st.session_state:
        with st.spinner("Yapay Zeka raporu hazırlıyor..."):
            p, s = analiz_ve_yol_haritasi(marka_adi, sektor_adi)
            st.session_state["puan"] = p
            st.session_state["strateji"] = s
            st.rerun()

    # ÜST BÖLÜM: PUAN VE GÖSTERGE
    col1, col2 = st.columns([1, 1.5], gap="large")
    
    with col1:
        st.markdown("### 🎯 Mevcut AI Skoru")
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=st.session_state["puan"],
            gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#3B82F6"}, 'bgcolor': "white",
                   'steps': [{'range': [0, 40], 'color': '#FEE2E2'}, {'range': [40, 70], 'color': '#FEF3C7'}, {'range': [70, 100], 'color': '#D1FAE5'}]},
            domain={'x': [0, 1], 'y': [0, 1]}))
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 🗺️ Stratejik Yol Haritası")
        st.info(st.session_state["strateji"])

# --- 6. İÇERİK ÜRETİMİ ---
elif nav == "✍️ İçerik Üretimi":
    st.title("🚀 Strateji Odaklı İçerik Fabrikası")
    if "strateji" in st.session_state:
        st.subheader("📝 Üretilecek İçerik Odağı")
        st.write(f"_{st.session_state['strateji'][:200]}..._")
        
        if st.button("🌟 İçerik Paketini Hazırla", use_container_width=True):
            with st.spinner("Stratejinize uygun içerikler tasarlanıyor..."):
                content_prompt = f"Şu stratejiye uygun olarak {marka_adi} için Blog ve Sosyal Medya postu yaz: {st.session_state['strateji']}"
                res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": content_prompt}]).choices[0].message.content
                st.markdown("---")
                st.markdown(res)
    else:
        st.warning("Lütfen önce Dashboard'da bir analiz başlatın!")