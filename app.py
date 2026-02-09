import streamlit as st
from openai import OpenAI
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import datetime
import re

# --- API ---
OPENAI_KEY = "sk-proj-..." # Kendi key'inizi buraya girin
client = OpenAI(api_key=OPENAI_KEY)

# --- 1. DİNAMİK VERİ ÇEKME FONKSİYONLARI ---
def analiz_yap(marka, sektor):
    # Marka değiştiğinde AI'dan yeni ve özgün veriler alır
    try:
        p_prompt = f"{marka} ({sektor}) için global AI bilinirlik puanı ver (0-100). Sadece rakam."
        p_res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": p_prompt}]).choices[0].message.content
        puan = int(''.join(filter(str.isdigit, p_res)))
        
        y_prompt = f"{marka} markasının {sektor} sektöründeki konumu hakkında 3 maddelik stratejik özet yaz."
        yorum = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": y_prompt}]).choices[0].message.content
        
        return puan, yorum
    except:
        return 50, "Analiz şu an yapılamıyor."

# --- ARAYÜZ ---
with st.sidebar:
    st.title("👋 Admin Panel")
    yeni_marka = st.text_input("Markanız", "VetraPos")
    # Marka değiştiyse verileri sıfırla
    if "eski_marka" not in st.session_state or st.session_state["eski_marka"] != yeni_marka:
        st.session_state["eski_marka"] = yeni_marka
        st.session_state["puan"] = None
        st.session_state["yorum"] = None
    
    sektor_adi = st.text_input("Sektör", "Sanal POS")
    nav = st.radio("Menü", ["📊 Dashboard", "✍️ İçerik Üretimi"])

# --- DASHBOARD ---
if nav == "📊 Dashboard":
    st.markdown(f"<h1 style='text-align: center;'>🚀 {yeni_marka} Operasyon Merkezi</h1>", unsafe_allow_html=True)
    
    # Butona basıldığında veya veri yoksa analiz yap
    if st.button("🔄 Verileri Derinlemesine Güncelle", use_container_width=True) or st.session_state["puan"] is None:
        with st.spinner(f"{yeni_marka} analiz ediliyor..."):
            p, y = analiz_yap(yeni_marka, sektor_adi)
            st.session_state["puan"] = p
            st.session_state["yorum"] = y
            st.rerun() # Verileri ekrana basmak için yenile

    # GÖRSELLEŞTİRME
    puan = st.session_state["puan"]
    yorum = st.session_state["yorum"]
    
    c1, c2 = st.columns([1, 1.5])
    with c1:
        fig = go.Figure(go.Indicator(mode="gauge+number", value=puan, title={'text': "AI Skoru"},
                        gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#3B82F6"},
                        'steps': [{'range': [0, 70], 'color': '#FDE68A'}, {'range': [70, 100], 'color': '#BBF7D0'}]}))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("🤖 Stratejik Özet")
        st.success(yorum)

    st.divider()
    st.subheader("🔍 Live Search: Gerçek Zamanlı Google Analizi")
    kw = st.text_input("Hedef Anahtar Kelime", "Sanal pos firmaları")
    if st.button("🔎 Google Sıralamasını Tara"):
        with st.spinner("Google SERP verileri taranıyor..."):
            serp_res = google_serp_analiz(marka_adi, kw)
            st.info(serp_res)

# --- 3. İÇERİK ÜRETİMİ (TAM DOLU SEKMELER) ---
elif nav == "✍️ İçerik Üretimi":
    st.title("🚀 360° İçerik & Görsel Fabrikası")
    topic = st.text_input("📝 Ana Konu Başlığı")
    gen_image = st.toggle("🖼️ Yapay Zeka Görseli Üret (DALL-E 3)", value=True)

    if st.button("🌟 Tüm İçerik Paketini Hazırla", use_container_width=True):
        with st.spinner("AI İçerik ve Görsel üretiliyor..."):
            prompt = f"Konu: {topic}. Lütfen [BLOG_B]...[BLOG_S], [SOSYAL_B]...[SOSYAL_S], [BULTEN_B]...[BULTEN_S] etiketleriyle yaz."
            full_res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}]).choices[0].message.content
            
            img_url = None
            if gen_image:
                try:
                    img_url = client.images.generate(model="dall-e-3", prompt=f"Marketing visual for: {topic}", n=1).data[0].url
                except: pass

            def parse(tag):
                m = re.search(f"\[{tag}_B\](.*?)\[{tag}_S\]", full_res, re.DOTALL)
                return m.group(1).strip() if m else ""

            tab1, tab2, tab3 = st.tabs(["📝 Blog & SEO", "📱 Sosyal Medya", "📧 E-Bülten"])
            with tab1:
                if img_url: st.image(img_url)
                st.markdown(parse("BLOG") if parse("BLOG") else full_res)
                icerik_kaydet("admin", marka_adi, topic, parse("BLOG"), tip="Blog")
            with tab2: st.markdown(parse("SOSYAL"))
            with tab3: st.markdown(parse("BULTEN"))