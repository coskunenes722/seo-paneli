import streamlit as st
from openai import OpenAI
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import datetime
import re

# --- 1. API ANAHTARI (Lütfen tırnaklar arasına sadece anahtarı yazın) ---
# Üçlü tırnak kullanımı, kopyalama sırasında oluşabilecek alt satır hatalarını engeller.
OPENAI_KEY = """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"""

client = OpenAI(api_key=OPENAI_KEY)

# --- 2. SAYFA AYARLARI ---
st.set_page_config(page_title="VetraPos AI Ultimate", layout="wide", page_icon="🚀")

# --- 3. VERİTABANI KURULUMU ---
def init_db():
    conn = sqlite3.connect('arsiv.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS icerikler 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, kullanici TEXT, marka TEXT, konu TEXT, icerik TEXT, tarih TEXT, tip TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS skorlar 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, marka TEXT, puan INTEGER, tarih TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 4. ZEKA FONKSİYONLARI ---
def analiz_yap(marka, sektor):
    try:
        # GERÇEKÇİ PUANLAMA İSTEMİ
        p_prompt = f"""
        Görev: Bir markanın dijital dünyadaki gerçek ağırlığını puanla.
        Kriterler: Küresel bilinirlik, arama hacmi, sosyal medya gücü ve sektördeki hakimiyet.
        Marka: {marka}
        Sektör: {sektor}
        
        Önemli Kural: Coca Cola, Apple gibi devler 95-100 almalıdır. 
        Yerel veya yeni markalar (VetraPos gibi) 10-30 arası başlamalıdır.
        Sadece 0-100 arası bir rakam ver. Başka hiçbir şey yazma.
        """
        
        p_res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": p_prompt}], timeout=15).choices[0].message.content
        digits = ''.join(filter(str.isdigit, p_res))
        puan = int(digits) if digits else 50
        
        # Stratejik özet kısmında da gerçekçi olmasını istiyoruz
        y_prompt = f"{marka} markasının {sektor} pazarındaki güncel konumunu gerçek piyasa verilerine dayanarak 3 maddede özetle."
        yorum = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": y_prompt}], timeout=15).choices[0].message.content
        
        return puan, yorum
    except Exception as e:
        return 50, f"Hata: {str(e)}"# --- 5. SIDEBAR (MARKA KONTROLÜ) ---
with st.sidebar:
    st.title("🚀 Admin Panel")
    marka_adi = st.text_input("Markanız", "Coca Cola")
    sektor_adi = st.text_input("Sektör", "İçecek")
    
    # Marka değiştiğinde eski verileri temizle
    if "aktif_marka" not in st.session_state or st.session_state["aktif_marka"] != marka_adi:
        st.session_state["aktif_marka"] = marka_adi
        st.session_state["puan"] = None
        st.session_state["yorum"] = None

    st.divider()
    nav = st.radio("Sistem Menüsü", ["📊 Dashboard", "✍️ İçerik Üretimi", "📜 Arşiv"])

# --- 6. DASHBOARD MODÜLÜ ---
if nav == "📊 Dashboard":
    st.markdown(f"<h1 style='text-align: center; color: #1E3A8A;'>🚀 {marka_adi} Operasyon Merkezi</h1>", unsafe_allow_html=True)
    
    # Analiz butonu veya ilk yükleme
    if st.button("🔄 Verileri Derinlemesine Güncelle", use_container_width=True) or st.session_state["puan"] is None:
        with st.spinner(f"{marka_adi} analiz ediliyor..."):
            p, y = analiz_yap(marka_adi, sektor_adi)
            st.session_state["puan"] = p
            st.session_state["yorum"] = y
            # Kaydet
            conn = sqlite3.connect('arsiv.db')
            conn.execute("INSERT INTO skorlar (marka, puan, tarih) VALUES (?, ?, ?)", 
                         (marka_adi, p, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            conn.close()
            st.rerun()

    # Görselleştirme
    c1, c2 = st.columns([1, 1.5])
    with c1:
        fig = go.Figure(go.Indicator(mode="gauge+number", value=st.session_state["puan"], 
                        title={'text': "AI Skoru", 'font': {'size': 24}},
                        gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#3B82F6"},
                               'steps': [{'range': [0, 50], 'color': '#FECACA'}, {'range': [50, 100], 'color': '#BBF7D0'}]}))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("🤖 Stratejik Analiz")
        st.success(st.session_state["yorum"])

# --- 7. İÇERİK ÜRETİMİ MODÜLÜ ---
elif nav == "✍️ İçerik Üretimi":
    st.title("🚀 360° İçerik Fabrikası")
    topic = st.text_input("📝 Ana Konu Başlığı")
    
    if st.button("🌟 Tüm İçerik Paketini Hazırla", use_container_width=True):
        with st.spinner("AI İçerikler hazırlanıyor..."):
            try:
                prompt = f"Konu: {topic}. Lütfen [BLOG_B]...[BLOG_S], [SOSYAL_B]...[SOSYAL_S] etiketleriyle yaz."
                res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}]).choices[0].message.content
                
                def parse(tag):
                    m = re.search(f"\[{tag}_B\](.*?)\[{tag}_S\]", res, re.DOTALL)
                    return m.group(1).strip() if m else ""

                t1, t2 = st.tabs(["📝 Blog", "📱 Sosyal Medya"])
                with t1: st.markdown(parse("BLOG") if parse("BLOG") else res)
                with t2: st.markdown(parse("SOSYAL"))
            except Exception as e:
                st.error(f"İçerik üretim hatası: {e}")