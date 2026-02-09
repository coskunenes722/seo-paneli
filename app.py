import streamlit as st
import os
from openai import OpenAI
import datetime

# --- PROFESYONEL GIRIS SISTEMI BASLANGICI ---
import time # Eger yoksa bunu ekle (sayfa yenileme icin)

# MUSTERI LISTESI (Buraya istedigin kadar kisi ekleyebilirsin)
# Format: "Kullanici Adi": "Sifre"
KULLANICILAR = {
    "admin": "12345",          # Kendin icin
    "ahmet_bey": "ahmet123",   # 1. Musteri
    "guzellik_merkezi": "guzel2024", # 2. Musteri
    "demo_hesap": "demo1"      # Deneme surumu vereceklerin icin
}

if "giris_yapildi" not in st.session_state:
    st.session_state["giris_yapildi"] = False
    st.session_state["aktif_kullanici"] = ""

if not st.session_state["giris_yapildi"]:
    st.markdown("""
    <style>
    .stTextInput > label {font-size:105%; font-weight:bold; color:blue;} 
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🔐 VetraPos SEO - Güvenli Giriş")
    st.info("Lütfen size verilen kullanıcı adı ve şifre ile giriş yapın.")
    
    kullanici_adi = st.text_input("Kullanıcı Adı")
    sifre = st.text_input("Şifre", type="password")
    
    if st.button("Giriş Yap"):
        # Kullanici adi dogru mu ve sifre eslesiyor mu?
        if kullanici_adi in KULLANICILAR and KULLANICILAR[kullanici_adi] == sifre:
            st.session_state["giris_yapildi"] = True
            st.session_state["aktif_kullanici"] = kullanici_adi
            st.success(f"Hoşgeldiniz Sayın {kullanici_adi}! Panel Yükleniyor...")
            time.sleep(1) # 1 saniye bekle
            st.rerun()
        else:
            st.error("Hatalı kullanıcı adı veya şifre!")
    
    st.stop() # Giris yapilmazsa kodun devami calismaz
else:
    # Icerde kimin oldugunu gormek istersen (opsiyonel)
    st.sidebar.success(f"👤 Giriş Yapan: {st.session_state['aktif_kullanici']}")
    if st.sidebar.button("Çıkış Yap"):
        st.session_state["giris_yapildi"] = False
        st.rerun()
# --- PROFESYONEL GIRIS SISTEMI BITISI ---

# --- AYARLAR ---
st.set_page_config(page_title="VetraPos AI SEO", layout="wide")

# ---------------------------------------------------------
# ÖNEMLİ: Şifreni tırnakların içine yapıştır (sk-proj... ile başlayan)
api_key = "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" 
# ---------------------------------------------------------



client = OpenAI(api_key=api_key)

# --- FONKSİYONLAR ---
def get_ai_suggestions(brand, sector):
    prompt = f"Sen {brand} markası için {sector} sektöründe 3 teknik blog konusu öner."
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Hata: {e}"

def write_full_article(topic, brand):
    prompt = f"Konu: {topic}. Marka: {brand}. 600 kelimelik teknik, tablolu, Schema kodlu makale yaz."
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Hata: {e}"

# --- EKRAN TASARIMI ---
st.title("🚀 VetraPos - Yapay Zeka SEO Paneli")

# Sol Menü
st.sidebar.header("⚙️ Ayarlar")
brand_name = st.sidebar.text_input("Marka Adı", value="VetraPos")
sector_name = st.sidebar.text_input("Sektör", value="POS Sistemleri")

# Ana Ekran
col1, col2 = st.columns(2)

with col1:
    st.info("🕵️‍♂️ **1. Adım: Konu Bul**")
    if st.button("Fikir Üret"):
        with st.spinner("Düşünülüyor..."):
            suggestions = get_ai_suggestions(brand_name, sector_name)
            st.success("Öneriler:")
            st.write(suggestions)

with col2:
    st.success("✍️ **2. Adım: Makale Yaz**")
    topic_input = st.text_area("Hangi konuyu yazalım?", placeholder="Soldan bir başlık kopyala...")
    
    if st.button("Makaleyi Yaz"):
        if len(topic_input) > 5:
            with st.spinner("Yazılıyor..."):
                article = write_full_article(topic_input, brand_name)
                st.markdown(article)
                
                # İndirme Butonu
                st.download_button("💾 İndir", article, file_name="makale.md")
        else:
            st.warning("Lütfen bir konu yazın.")