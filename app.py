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
def get_canli_skor(marka, sektor):
    # Yapay zekaya daha katı ve net bir talimat veriyoruz
    prompt = f"""
    Sen profesyonel bir dijital pazarlama denetçisisin. 
    '{marka}' markasının '{sektor}' sektöründeki yapay zeka modelleri (ChatGPT, Claude, Perplexity) tarafından bilinirlik ve önerilme oranını analiz et.
    
    Lütfen şu kriterlere göre 0 ile 100 arasında bir puan ver:
    - Marka ne kadar sık referans gösteriliyor?
    - Sektörel sorgularda ilk 5 öneri arasında mı?
    - Hakkındaki teknik veriler ne kadar güncel?

    SADECE rakam olarak (örneğin: 74) cevap ver. Başka hiçbir kelime yazma.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7 # Her seferinde aynı 50 cevabını vermemesi için çeşitlilik ekledik
        )
        res_content = response.choices[0].message.content.strip()
        
        # İçindeki tüm rakamları bulup birleştiriyoruz
        puan_liste = [s for s in res_content if s.isdigit()]
        if puan_liste:
            puan = int("".join(puan_liste))
            # Puanın 0-100 arasında kalmasını garanti ediyoruz
            puan = max(0, min(100, puan))
        else:
            puan = 50 # Hiç rakam bulunamazsa
            
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