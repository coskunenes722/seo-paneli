import streamlit as st
from openai import OpenAI
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import datetime
import re

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="VetraPos AI Ultimate", layout="wide", page_icon="🚀")

# --- 2. VERİTABANI VE İLK KURULUM ---
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

# --- 3. YARDIMCI FONKSİYONLAR ---
def icerik_kaydet(kullanici, marka, konu, icerik, tip="Makale"):
    conn = sqlite3.connect('arsiv.db')
    c = conn.cursor()
    tarih = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO icerikler (kullanici, marka, konu, icerik, tarih, tip) VALUES (?, ?, ?, ?, ?, ?)",
              (kullanici, marka, konu, icerik, tarih, tip))
    conn.commit()
    conn.close()

# --- 4. API YAPILANDIRMASI ---
OPENAI_KEY = "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
"
client = OpenAI(api_key=OPENAI_KEY)

# --- 5. ZEKA FONKSİYONLARI ---
def analiz_yap(marka, sektor):
    try:
        # Puan Analizi
        p_prompt = f"'{marka}' markasının '{sektor}' sektöründeki AI bilinirlik puanını (0-100) ver. Sadece rakam."
        p_res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": p_prompt}]).choices[0].message.content
        puan = int(''.join(filter(str.isdigit, p_res)))
        
        # Özet Analizi
        y_prompt = f"{marka} markasının {sektor} sektöründeki konumu hakkında 3 maddelik stratejik özet yaz."
        yorum = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": y_prompt}]).choices[0].message.content
        
        return puan, yorum
    except:
        return 50, "Analiz şu an yapılamıyor. Lütfen API anahtarınızı kontrol edin."

# --- 6. ARAYÜZ (SIDEBAR) ---
with st.sidebar:
    st.title("🚀 Admin Panel")
    marka_adi = st.text_input("Markanız", "VetraPos")
    sektor_adi = st.text_input("Sektör", "Sanal POS")
    
    # MARKA DEĞİŞİM KONTROLÜ (Verileri tazelemek için)
    if "aktif_marka" not in st.session_state or st.session_state["aktif_marka"] != marka_adi:
        st.session_state["aktif_marka"] = marka_adi
        st.session_state["puan"] = None
        st.session_state["yorum"] = None

    st.divider()
    # Menü İsimleri (Kodla eşleşmesi için sabitlenmiştir)
    nav = st.radio("Sistem Menüsü", ["📊 Dashboard", "✍️ İçerik Üretimi", "🕵️ Rakip Tarayıcı", "📜 Arşiv"])

# --- 7. DASHBOARD MODÜLÜ ---
if nav == "📊 Dashboard":
    st.markdown(f"<h1 style='text-align: center; color: #1E3A8A;'>🚀 {marka_adi} Operasyon Merkezi</h1>", unsafe_allow_html=True)
    
    # Veri Yoksa veya Butona Basıldıysa Analiz Yap
    if st.button("🔄 Verileri Derinlemesine Güncelle", use_container_width=True) or st.session_state["puan"] is None:
        with st.spinner(f"{marka_adi} için küresel veriler analiz ediliyor..."):
            p, y = analiz_yap(marka_adi, sektor_adi)
            st.session_state["puan"] = p
            st.session_state["yorum"] = y
            # Skoru Veritabanına Kaydet (Trend grafiği için)
            conn = sqlite3.connect('arsiv.db')
            conn.execute("INSERT INTO skorlar (marka, puan, tarih) VALUES (?, ?, ?)", 
                         (marka_adi, p, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            conn.close()
            st.rerun()

    # Görselleştirme
    col1, col2 = st.columns([1, 1.5])
    with col1:
        fig = go.Figure(go.Indicator(mode="gauge+number", value=st.session_state["puan"], 
                        title={'text': "AI Skoru", 'font': {'size': 24}},
                        gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#3B82F6"},
                               'steps': [{'range': [0, 50], 'color': '#FECACA'}, {'range': [50, 100], 'color': '#BBF7D0'}]}))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("🤖 Stratejik Analiz Özeti")
        st.success(st.session_state["yorum"])

    st.divider()
    st.subheader("📈 Sektörel Görünürlük Trendi")
    conn = sqlite3.connect('arsiv.db')
    df_trend = pd.read_sql(f"SELECT tarih, puan FROM skorlar WHERE marka='{marka_adi}' ORDER BY tarih ASC", conn)
    if not df_trend.empty:
        st.line_chart(df_trend.set_index('tarih'))
    conn.close()

# --- 8. İÇERİK ÜRETİMİ MODÜLÜ ---
elif nav == "✍️ İçerik Üretimi":
    st.title("🚀 360° İçerik & Görsel Fabrikası")
    topic = st.text_input("📝 Ana Konu Başlığı", placeholder="Örn: Coca-Cola'nın Pazarlama Stratejisi")
    
    if st.button("🌟 Tüm İçerik Paketini Hazırla", use_container_width=True):
        if not topic:
            st.error("Lütfen bir konu başlığı girin!")
        else:
            with st.spinner("AI İçerikler hazırlanıyor..."):
                prompt = f"Konu: {topic}. Lütfen [BLOG_B]...[BLOG_S], [SOSYAL_B]...[SOSYAL_S] etiketleriyle yaz."
                res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}]).choices[0].message.content
                
                def parse(tag):
                    m = re.search(f"\[{tag}_B\](.*?)\[{tag}_S\]", res, re.DOTALL)
                    return m.group(1).strip() if m else ""

                tab1, tab2 = st.tabs(["📝 Blog", "📱 Sosyal Medya"])
                with tab1: st.markdown(parse("BLOG") if parse("BLOG") else res)
                with tab2: st.markdown(parse("SOSYAL"))
                icerik_kaydet("admin", marka_adi, topic, res, tip="Tam Paket")

# --- 9. DİĞER MODÜLLER (BOŞ KALMAMASI İÇİN) ---
elif nav == "🕵️ Rakip Tarayıcı":
    st.title("🕵️ Rakip Analiz Laboratuvarı")
    st.info("Bu modül geliştirme aşamasındadır.")
elif nav == "📜 Arşiv":
    st.title("📜 İçerik Arşivi")
    conn = sqlite3.connect('arsiv.db')
    df = pd.read_sql("SELECT tarih, marka, konu FROM icerikler ORDER BY id DESC", conn)
    st.table(df)
    conn.close()