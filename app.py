import streamlit as st
from openai import OpenAI
import plotly.graph_objects as go
import re

# --- API YAPILANDIRMASI ---
OPENAI_KEY = "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"
client = OpenAI(api_key=OPENAI_KEY)

def analiz_gercekci(marka, sektor):
    try:
        # SERT FİLTRE PROMPT'U
        p_prompt = f"""
        Görev: Markanın dijital bilinirliğini (AI Skoru) 0-100 arası puanla.
        Marka: {marka} | Sektör: {sektor}
        
        KESİN PUANLAMA KRİTERLERİ:
        - Coca-Cola, Google, Amazon: 95-100 puan.
        - Türkiye genelinde herkesin bildiği markalar: 60-85 puan.
        - VetraPos gibi yeni veya gelişmekte olan girişimler: 5-25 PUANI GEÇEMEZ.
        
        Sadece rakam ver. Eğer marka çok yeniyse 15-20 arası bir değer ver.
        """
        p_res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": p_prompt}]).choices[0].message.content
        puan = int(''.join(filter(str.isdigit, p_res)))
        
        # Yol Haritası (Neden düşük puan aldığını açıklayan içerik)
        h_prompt = f"{marka} markasının skoru {puan}. Bu skorun neden düşük olduğunu ve gerçekçi büyüme adımlarını özetle."
        harita = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": h_prompt}]).choices[0].message.content
        
        return puan, harita
    except:
        return 10, "Kota veya bağlantı sorunu nedeniyle analiz yapılamadı."

# --- ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Operasyon Paneli")
    marka_adi = st.text_input("Markanız", "VetraPos")
    sektor_adi = st.text_input("Sektör", "Sanal POS")
    st.divider()
    nav = st.radio("Menü", ["📊 Dashboard", "✍️ İçerik Üretimi"])

if nav == "📊 Dashboard":
    st.markdown(f"<h1>🚀 {marka_adi} Analiz Merkezi</h1>", unsafe_allow_html=True)
    
    if st.button("🔄 Gerçekçi Analiz Yap", use_container_width=True) or "puan" not in st.session_state:
        with st.spinner("Piyasa verileri kıyaslanıyor..."):
            p, h = analiz_gercekci(marka_adi, sektor_adi)
            st.session_state["puan"] = p
            st.session_state["harita"] = h
            st.rerun()

    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.markdown(f"### 🎯 Mevcut Durum")
        fig = go.Figure(go.Indicator(mode="gauge+number", value=st.session_state["puan"],
                        gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#3B82F6"}}))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("### 🗺️ Neden Bu Skoru Aldınız?")
        st.info(st.session_state["harita"])