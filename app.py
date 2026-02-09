import streamlit as st
from openai import OpenAI
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import datetime
import re

# --- 1. API YAPILANDIRMASI ---
# Üçlü tırnak kullanımı, kopyalama hatalarını engeller.
OPENAI_KEY = """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"""
client = OpenAI(api_key=OPENAI_KEY)

# --- 2. SAYFA AYARLARI ---
st.set_page_config(page_title="VetraPos AI Ultimate", layout="wide", page_icon="🚀")

# --- 3. ZEKA FONKSİYONLARI (KESİN VE DOĞRU MANTIK) ---
def analiz_yap(marka, sektor):
    try:
        # GERÇEKÇİ PUANLAMA MANTIĞI - BOZMAYIN
        p_prompt = f"""
        Görev: Bir markanın küresel dijital ağırlığını 0-100 arası puanla.
        Marka: {marka} | Sektör: {sektor}
        
        KESİN KURALLAR:
        1. Coca-Cola, Apple, Google, Nike gibi devler: 95-100 arası.
        2. Bilindik yerel büyük firmalar: 60-85 arası.
        3. Yeni girişimler veya KOBİ'ler (VetraPos vb.): 5-30 arası.
        Sadece rakam ver.
        """
        p_res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": p_prompt}], timeout=15).choices[0].message.content
        digits = ''.join(filter(str.isdigit, p_res))
        puan = int(digits) if digits else 50
        
        # STRATEJİK ANALİZ MANTIĞI
        y_prompt = f"{marka} markasının {sektor} sektöründeki pazar konumunu gerçekçi verilerle 3 maddede özetle."
        yorum = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": y_prompt}], timeout=15).choices[0].message.content
        
        return puan, yorum
    except Exception as e:
        return 50, f"Bağlantı Sorunu: {str(e)}"

# --- 4. SIDEBAR VE MARKA YÖNETİMİ ---
with st.sidebar:
    st.title("🚀 Operasyon Paneli")
    marka_adi = st.text_input("Markanız", "VetraPos")
    sektor_adi = st.text_input("Sektör", "Sanal POS")
    
    # Marka değiştiğinde verileri temizle
    if "aktif_marka" not in st.session_state or st.session_state["aktif_marka"] != marka_adi:
        st.session_state["aktif_marka"] = marka_adi
        st.session_state["puan"] = None
        st.session_state["yorum"] = None

    st.divider()
    nav = st.radio("Menü", ["📊 Dashboard", "✍️ İçerik Üretimi", "📜 Arşiv"])

# --- 5. DASHBOARD (PROFESYONEL GÖRÜNÜM) ---
if nav == "📊 Dashboard":
    st.markdown(f"<h1 style='text-align: center; color: #1E3A8A;'>🛡️ {marka_adi} Stratejik Analiz Merkezi</h1>", unsafe_allow_html=True)
    
    if st.button("🔄 Verileri Derinlemesine Güncelle", use_container_width=True) or st.session_state["puan"] is None:
        with st.spinner(f"{marka_adi} analiz ediliyor..."):
            p, y = analiz_yap(marka_adi, sektor_adi)
            st.session_state["puan"] = p
            st.session_state["yorum"] = y
            st.rerun()

    # Dashboard Görselleştirme
    c1, c2 = st.columns([1, 1.5])
    with c1:
        fig = go.Figure(go.Indicator(mode="gauge+number", value=st.session_state["puan"], 
                        title={'text': "AI Skoru", 'font': {'size': 24}},
                        gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#3B82F6"},
                               'steps': [{'range': [0, 50], 'color': '#FECACA'}, {'range': [50, 100], 'color': '#BBF7D0'}]}))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("🤖 Gerçekçi Strateji Özeti")
        st.success(st.session_state["yorum"])