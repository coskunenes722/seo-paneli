import streamlit as st
from openai import OpenAI
import time
import sqlite3
import pandas as pd
import plotly.graph_objects as go # Gelişmiş grafikler için

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="VetraPos AI Ultimate", layout="wide", page_icon="🚀")

# --- VERİTABANI ---
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

# --- AI FONKSİYONLARI ---
import datetime

def get_canli_skor(marka, sektor):
    # AI'ya markayı gerçekten araştırması için detaylı bir "Persona" veriyoruz
    prompt = f"""
    Sen profesyonel bir Dijital Strateji Analistisin. 
    '{marka}' markasını '{sektor}' sektöründe, yapay zeka modellerinin (ChatGPT, Perplexity, Claude) veri setlerindeki varlığına göre analiz et.
    
    Aşağıdaki metriklere göre 0-100 arası bir AI GÖRÜNÜRLÜK PUANI hesapla:
    1. Marka ismi sektörle ne kadar güçlü eşleşiyor? (0-40 puan)
    2. Kullanıcılar 'en iyi {sektor} çözümleri' diye sorduğunda marka öneriliyor mu? (0-40 puan)
    3. Marka hakkında güncel teknik döküman veya haber varlığı nedir? (0-20 puan)

    Önemli Not: Coca-Cola gibi dev markalar 85-95 arası almalı. VetraPos gibi yeni veya niş projeler, AI tarafından henüz keşfedilme aşamasında oldukları için gerçekçi (örneğin 20-45 arası) puanlar almalı.
    
    SADECE rakam ver. Yanına açıklama yazma.
    """
    try:
        # temperature=0.9 vererek her seferinde aynı (50) sonucunu vermesini engelliyoruz
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9 
        )
        res_content = response.choices[0].message.content.strip()
        
        # Sadece rakamı çekmek için filtreleme
        puan_str = "".join(filter(str.isdigit, res_content))
        puan = int(puan_str) if puan_str else 50
        
        # Puanın 100'ü geçmediğinden emin olalım
        puan = min(100, max(0, puan))

        # VERITABANINA KAYDET (Grafik için tarih damgalı)
        conn = sqlite3.connect('arsiv.db')
        c = conn.cursor()
        tarih_tam = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("INSERT INTO skorlar (marka, puan, tarih) VALUES (?, ?, ?)", (marka, puan, tarih_tam))
        conn.commit()
        conn.close()
        
        return puan
    except Exception as e:
        st.error(f"Skor hatası: {e}")
        return 50

# --- DASHBOARD GÜNCELLEMESİ ---
if nav == "📊 Dashboard":
    st.title(f"📊 {marka_adi} Stratejik Analiz Paneli")
    
    # Her girişte yeni bir analiz tetikle
    with st.spinner(f"{marka_adi} için AI verileri taranıyor..."):
        puan = get_canli_skor(marka_adi, sektor)
        ai_yorum = get_marka_yorumu(marka_adi, sektor)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        # Daha profesyonel renkli Gauge Chart
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = puan,
            delta = {'reference': 50}, # 50'ye göre değişim gösterir
            title = {'text': "AI Bilinirlik Skoru", 'font': {'size': 24}},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1},
                'bar': {'color': "#1f77b4"},
                'steps': [
                    {'range': [0, 30], 'color': "#ff4b4b"},
                    {'range': [30, 70], 'color': "#ffa500"},
                    {'range': [70, 100], 'color': "#00cc96"}]}))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col2:
        st.subheader("🤖 Yapay Zeka Gözünden Marka Analizi")
        st.write(ai_yorum)
        st.info(f"💡 İpucu: Bu puan, AI modellerinin '{marka_adi}' hakkındaki güncel bilgisini temsil eder.")

    st.divider()
    st.subheader("📈 Zaman İçindeki Değişim")
    # Veritabanından geçmiş skorları çek ve çiz
    conn = sqlite3.connect('arsiv.db')
    df_skor = pd.read_sql(f"SELECT tarih, puan FROM skorlar WHERE marka='{marka_adi}' ORDER BY tarih ASC", conn)
    conn.close()
    if not df_skor.empty:
        st.line_chart(df_skor.set_index('tarih'))            
        # Veritabanına kaydet
        tarih = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect('arsiv.db')
        c = conn.cursor()
        c.execute("INSERT INTO skorlar (marka, puan, tarih) VALUES (?, ?, ?)", (marka, puan, tarih))
        conn.commit()
        conn.close()
        return puan
    except Exception as e:
        st.error(f"Skor hesaplama hatası: {e}")
        return 50
def get_marka_yorumu(marka, sektor):
    prompt = f"Yapay zeka modelleri şu an {marka} markasını {sektor} sektöründe nasıl görüyor? 3 maddelik çok kısa bir özet ver."
    return client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}]).choices[0].message.content

# --- ARAYÜZ (SIDEBAR) ---
with st.sidebar:
    st.title(f"👋 {st.session_state['aktif_kullanici']}")
    marka_adi = st.text_input("Markanız", "VetraPos")
    sektor = st.text_input("Sektör", "Sanal POS")
    st.divider()
    nav = st.radio("Menü", ["📊 Dashboard", "🕵️ Rakip Tarayıcı", "✍️ İçerik Üretimi", "📜 Arşiv"])
    if st.button("Güvenli Çıkış"):
        st.session_state["giris_yapildi"] = False
        st.rerun()

# --- 1. DASHBOARD (CANLI VERİLER) ---
if nav == "📊 Dashboard":
    st.title(f"📊 {marka_adi} Performans Dashboard")
    
    with st.spinner("Canlı veriler analiz ediliyor..."):
        current_score = get_canli_skor(marka_adi, sektor)
        ai_yorum = get_marka_yorumu(marka_adi, sektor)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Hız Göstergesi (Gauge Chart)
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = current_score,
            title = {'text': "AI Bilinirlik Skoru"},
            gauge = {'axis': {'range': [None, 100]},
                     'bar': {'color': "darkblue"},
                     'steps' : [
                         {'range': [0, 40], 'color': "red"},
                         {'range': [40, 70], 'color': "orange"},
                         {'range': [70, 100], 'color': "green"}]}))
        st.plotly_chart(fig_gauge, use_container_width=True)
        
    with col2:
        st.subheader("🤖 Yapay Zeka Bilinirlik Raporu")
        st.success(ai_yorum)
        
    st.divider()
    
    # Zaman Çizelgesi (Line Chart)
    st.subheader("📈 Skor Gelişim Trendi")
    conn = sqlite3.connect('arsiv.db')
    df_skor = pd.read_sql(f"SELECT tarih, puan FROM skorlar WHERE marka='{marka_adi}' ORDER BY tarih ASC", conn)
    conn.close()
    
    if not df_skor.empty:
        st.line_chart(df_skor.set_index('tarih'))
    else:
        st.info("Veriler toplandıkça gelişim grafiği burada oluşacak.")

# --- 2. RAKİP TARAYICI (ÖZEL ALAN) ---
elif nav == "🕵️ Rakip Tarayıcı":
    st.title("🕵️ Rakip Site Tarayıcı")
    st.info("Analiz etmek istediğiniz rakip sitenin URL'sini aşağıya girin.")
    
    # URL kutusu artık sadece burada
    r_url = st.text_input("Rakip Site URL (https://...)", placeholder="Örn: https://www.rakipsite.com")
    
    if st.button("Rakibi Analiz Et ve Boşlukları Bul"):
        if r_url:
            with st.spinner(f"{r_url} taranıyor..."):
                prompt = f"{r_url} rakibini analiz et ve {marka_adi} için strateji üret."
                res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}]).choices[0].message.content
                st.markdown(res)
        else:
            st.warning("Lütfen bir URL girin.")

# --- 3. İÇERİK ÜRETİMİ ---
elif nav == "✍️ İçerik Üretimi":
    st.title("✍️ İçerik Fabrikası")
    konu = st.text_input("Konu nedir?")
    if st.button("Üret ve Kaydet"):
        with st.spinner("Yazılıyor..."):
            res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": f"{konu} blog yaz."}]).choices[0].message.content
            st.markdown(res)
            # Kaydetme fonksiyonu buraya eklenebilir