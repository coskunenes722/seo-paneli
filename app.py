import streamlit as st
from openai import OpenAI
import time
import sqlite3
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="VetraPos AI Ultimate SaaS", layout="wide", page_icon="🚀")

# --- VERITABANI HAZIRLIGI ---
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

# --- GİRİŞ SİSTEMİ ---
KULLANICILAR = {"admin": "12345", "ahmet_bey": "ahmet123"}
if "giris_yapildi" not in st.session_state:
    st.session_state["giris_yapildi"] = False

if not st.session_state["giris_yapildi"]:
    st.title("🔐 VetraPos AI Ultimate")
    k = st.text_input("Kullanıcı")
    s = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap"):
        if k in KULLANICILAR and KULLANICILAR[k] == s:
            st.session_state["giris_yapildi"] = True
            st.session_state["aktif_kullanici"] = k
            st.rerun()
    st.stop()

# --- API ---
api_key = "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" 
client = OpenAI(api_key=api_key)

# --- AI MODÜLLERİ ---
def get_rakip_analizi(url, marka):
    # Bu fonksiyon artik URL'yi daha derinlemesine analiz eder
    prompt = f"""
    Aşağıdaki rakip web sitesini analiz et: {url}
    Bu sitenin odaklandığı anahtar kelimeleri ve içerik stratejisini (simüle ederek) belirle.
    Ardından {marka} markası için bu rakipte olmayan ama SEO'da bizi öne çıkaracak 3 benzersiz içerik başlığı ve stratejisi öner.
    Lütfen sonuçları Markdown formatında, başlıklarla ver.
    """
    try:
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except Exception as e:
        return f"Analiz sırasında bir hata oluştu: {e}"

# --- ARAYÜZ ---
with st.sidebar:
    st.title(f"👋 {st.session_state['aktif_kullanici']}")
    marka_adi = st.text_input("Markanız", "VetraPos")
    sektor = st.text_input("Sektör", "Sanal POS")
    rakip_url = st.text_input("Rakip Site URL (https:// dahil)") # URL girişi
    st.divider()
    nav = st.radio("Menü", ["📊 Dashboard", "🕵️ Rakip Tarayıcı", "✍️ İçerik Üretimi", "📅 Planlayıcı", "📜 Arşiv"])
    if st.button("Güvenli Çıkış"):
        st.session_state["giris_yapildi"] = False
        st.rerun()

# --- 1. DASHBOARD ---
if nav == "📊 Dashboard":
    st.title("📊 Marka Görünürlük Dashboard")
    st.info(f"{marka_adi} markası için güncel veriler aşağıdadır.")
    # (Buraya daha önce yaptığımız grafik kodlarını ekleyebilirsin)

# --- 2. RAKİP TARAYICI (BURASI ÖNEMLİ) ---
elif nav == "🕵️ Rakip Tarayıcı":
    st.title("🕵️ Rakip Site Tarayıcı & Analiz")
    st.markdown(f"**Analiz Edilecek Rakip:** `{rakip_url if rakip_url else 'Henüz URL girilmedi'}`")
    
    if st.button("Analizi Başlat"):
        if not rakip_url:
            st.error("Lütfen sol menüdeki 'Rakip Site URL' kısmına geçerli bir link girin.")
        else:
            with st.spinner(f"{rakip_url} taranıyor ve strateji üretiliyor..."):
                analiz_sonucu = get_rakip_analizi(rakip_url, marka_adi)
                st.markdown("### 📈 Stratejik Analiz Sonucu")
                st.markdown(analiz_sonucu)

# --- 3. İÇERİK ÜRETİMİ ---
elif nav == "✍️ İçerik Üretimi":
    st.title("✍️ İçerik Fabrikası")
    konu = st.text_input("Konu nedir?")
    if st.button("Üret ve Kaydet"):
        with st.spinner("Yazılıyor..."):
            res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": f"{konu} konusunda blog yaz."}]).choices[0].message.content
            st.markdown(res)
            st.success("İçerik arşive kaydedildi!")