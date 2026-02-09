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
    
    st.title("🚀 Yapay Zeka SEO Paneli")
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

# --- YENI GELISMIS FONKSIYONLAR ---
def get_ai_suggestions(brand, sector):
    # 3 degil, artik 5 konu oneriyoruz ve daha detayli istiyoruz
    prompt = f"""
    Sen {brand} markası için {sector} sektöründe uzman bir SEO stratejistisin.
    
    Lütfen şu 3 başlık altında detaylı bir analiz yap:
    
    1. **5 Adet Teknik Blog Konusu:** {brand} markasının otoritesini artıracak, az bilinen ama çok aranan 5 teknik konu öner.
    2. **Anahtar Kelime Analizi:** {sector} sektörü için hacmi yüksek ama rekabeti düşük 10 adet "Long-tail" (uzun kuyruklu) anahtar kelime öner.
    3. **Rakip Analizi:** {sector} sektöründeki rakiplerin genellikle neleri eksik yaptığını ve {brand} markasının nasıl öne çıkabileceğini anlatan 3 maddelik strateji ver.
    
    Lütfen çıktılarını şık bir formatta, başlıklarla ayırarak ver.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Hata: {e}"

def write_full_article(topic, brand):
    # Makale yazma kismi ayni kalsin, guzel calisiyor
    prompt = f"Konu: {topic}. Marka: {brand}. 600 kelimelik teknik, tablolu, Schema kodlu, SEO uyumlu makale yaz."
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Hata: {e}"# --- EKRAN TASARIMI ---
st.title("🚀 Yapay Zeka SEO Paneli")

# Sol Menü
st.sidebar.header("⚙️ Ayarlar")
marka_adi = st.sidebar.text_input("Marka Adı", value="")
sektor = st.sidebar.text_input("Sektör", value="")

# Ana Ekran
# --- BURADAN ASAGISINI KOPYALA VE YAPISTIR ---
col1, col2 = st.columns([1,1])

with col1:
    st.info("🕵️ **1. Adım: Rakip & Kelime Analizi**")
    if st.button("🚀 Detaylı SEO Analizi Yap"):
        if not marka_adi or not sektor:
            st.error("Lütfen önce sol menüden Marka ve Sektör girin!")
        else:
            with st.spinner("Yapay zeka rakipleri geziyor, kelimeleri topluyor..."):
                # Analiz Fonksiyonunu cagir
                analiz_sonucu = get_ai_suggestions(marka_adi, sektor)
                st.markdown(analiz_sonucu)
                st.success("Analiz bitti! Şimdi yandaki panelden makale yazdırabilirsin. 👉")

with col2:
    st.success("✍️ **2. Adım: Makale Yaz**")
    topic_input = st.text_area("Hangi konuyu yazalım?", placeholder="Soldaki analizden bir başlık kopyalayıp buraya yapıştırın...")
    
    if st.button("Makaleyi Yaz"):
        if not topic_input or len(topic_input) < 5:
            st.warning("Lütfen geçerli bir konu başlığı girin.")
        else:
            with st.spinner("Makale yazılıyor, biraz uzun sürebilir..."):
                article = write_full_article(topic_input, marka_adi)
                st.markdown(article)
                
                # İndirme Butonu
                st.download_button("💾 Makaleyi İndir", article, file_name="seo-makale.md")