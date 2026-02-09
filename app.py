import streamlit as st
from openai import OpenAI
import time
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import datetime  # Hatayı çözen kritik kütüphane

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
    prompt = f"""
    Sen dijital bir denetçisin. '{marka}' markasını '{sektor}' sektöründe AI görünürlüğü açısından analiz et.
    Coca-Cola gibi dev markalar 85-95 arası, VetraPos gibi yeni girişimler 20-45 arası puan almalı.
    SADECE rakam ver (Örn: 72).
    """
    try:
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], temperature=0.8).choices[0].message.content
        puan = int(''.join(filter(str.isdigit, res)))
        tarih = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect('arsiv.db')
        c = conn.cursor()
        c.execute("INSERT INTO skorlar (marka, puan, tarih) VALUES (?, ?, ?)", (marka, puan, tarih))
        conn.commit()
        conn.close()
        return puan
    except:
        return 50

def get_marka_yorumu(marka, sektor):
    prompt = f"Yapay zeka modelleri şu an {marka} markasını {sektor} sektöründe nasıl görüyor? 3 maddelik özet ver."
    return client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}]).choices[0].message.content

# --- ARAYÜZ ---
with st.sidebar:
    st.title(f"👋 {st.session_state['aktif_kullanici']}")
    marka_adi = st.text_input("Markanız", "VetraPos")
    sektor_adi = st.text_input("Sektör", "Sanal POS")
    st.divider()
    nav = st.radio("Menü", ["📊 Dashboard", "🕵️ Rakip Tarayıcı", "✍️ İçerik Üretimi", "📜 Arşiv"])
    if st.button("Güvenli Çıkış"):
        st.session_state["giris_yapildi"] = False
        st.rerun()

# --- DASHBOARD ---
if nav == "📊 Dashboard":
    st.title(f"📊 {marka_adi} Performans Dashboard")
    with st.spinner("Analiz ediliyor..."):
        puan = get_canli_skor(marka_adi, sektor_adi)
        yorum = get_marka_yorumu(marka_adi, sektor_adi)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        fig = go.Figure(go.Indicator(
            mode = "gauge+number", value = puan,
            title = {'text': "AI Bilinirlik Skoru"},
            gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': "darkblue"},
                     'steps' : [{'range': [0, 40], 'color': "red"}, {'range': [70, 100], 'color': "green"}]}))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("🤖 Yapay Zeka Raporu")
        st.success(yorum)

    st.divider()
    st.subheader("📈 Skor Gelişim Trendi")
    conn = sqlite3.connect('arsiv.db')
    df = pd.read_sql(f"SELECT tarih, puan FROM skorlar WHERE marka='{marka_adi}' ORDER BY tarih ASC", conn)
    conn.close()
    if not df.empty: st.line_chart(df.set_index('tarih'))

# --- DİĞER SEKMEER ---
elif nav == "🕵️ Rakip Tarayıcı":
    st.title("🕵️ Rakip Analizi")
    r_url = st.text_input("Rakip URL")
    if st.button("Analiz Et"):
        st.info("Rakip stratejisi hazırlanıyor...")
        # Analiz fonksiyonu buraya gelecek

# --- 3. İÇERİK FABRİKASI (GELİŞMİŞ VE GÖRSEL DESTEKLİ) ---
elif nav == "✍️ İçerik Fabrikası":
    st.title("✍️ 360° İçerik Strateji Merkezi & Görsel Fabrikası")
    st.info("Bir konu girin, AI sizin için tüm platformlara uygun içerik paketini ve görselleri hazırlasın.")

    with st.container():
        c1, c2 = st.columns([2, 1])
        with c1:
            topic = st.text_input("Ana İçerik Konusu", placeholder="Örn: Sanal POS Seçerken Dikkat Edilmesi Gerekenler")
        with c2:
            target_tone = st.selectbox("İçerik Dili", ["Kurumsal & Güven Verici", "Samimi & Akıcı", "Teknik & Detaylı", "Satış Odaklı"])

    # Platform Seçenekleri ve Görsel İsteği
    st.markdown("##### 🚀 Üretilecek Paket İçeriği")
    col_a, col_b, col_c, col_d, col_e = st.columns(5)
    do_blog = col_a.checkbox("📝 SEO Blog", value=True)
    do_social = col_b.checkbox("📱 Sosyal Medya", value=True)
    do_mail = col_c.checkbox("📧 E-Bülten", value=True)
    do_video = col_d.checkbox("🎬 Video/Reels", value=True)
    do_image = col_e.checkbox("🖼️ Görsel Üret (DALL-E 3)", value=True) # Yeni Görsel Seçeneği

    if st.button("🌟 Tüm İçerik & Görsel Paketini Oluştur"):
        if not topic:
            st.warning("Lütfen bir konu başlığı girin.")
        else:
            with st.spinner("Yapay Zeka tüm paketini hazırlıyor..."):
                # Ana İçerik Üretimi
                prompt = f"""
                Konu: {topic}
                Marka: {marka_adi}
                Üslup: {target_tone}
                
                Lütfen aşağıdaki formatta bir içerik paketi hazırla:
                1. [BLOG]: SEO uyumlu başlık, 500 kelimelik makale, Meta Description ve Slug önerisi.
                2. [SOSYAL MEDYA]: LinkedIn (profesyonel), Instagram (ilgi çekici) ve Twitter (flood) için 3 ayrı post.
                3. [E-BÜLTEN]: Dikkat çekici konu başlığı ve kısa, aksiyona davet eden (CTA) mail metni.
                4. [VIDEO SCRIPT]: 60 saniyelik bir Reels videosu için sahne sahne konuşma metni.
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                full_content = response.choices[0].message.content
                
                # Görsel Üretimi (SADECE do_image seçiliyse)
                image_url = None
                if do_image:
                    image_prompt = f"Marka: {marka_adi}. Konu: {topic}. Bu içeriği temsil eden, modern, profesyonel ve ilgi çekici bir dijital sanat eseri oluştur. Metin içermesin."
                    try:
                        image_response = client.images.generate(
                            model="dall-e-3",
                            prompt=image_prompt,
                            size="1024x1024",
                            quality="standard",
                            n=1,
                        )
                        image_url = image_response.data[0].url
                        st.success("🖼️ Görsel başarıyla oluşturuldu!")
                    except Exception as e:
                        st.error(f"Görsel oluşturulurken bir hata oluştu: {e}")
                
                # İçeriği Kaydet
                icerik_kaydet(st.session_state["aktif_kullanici"], marka_adi, topic, full_content, tip="Tam Paket")
                
                # Görsel Arayüzde Sekmeli Gösterim
                tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Makale & SEO", "📱 Sosyal Medya", "📧 E-Bülten", "🎬 Video Senaryosu", "🖼️ Oluşturulan Görsel"])
                
                with tab1:
                    st.subheader("📝 Blog Yazısı ve SEO Künyesi")
                    st.markdown(full_content) # Tüm içeriği burada gösteriyoruz, istersen regex ile ayırabiliriz.
                    st.download_button("📄 Makaleyi İndir", full_content, f"{topic}_makale.txt")

                with tab2:
                    st.subheader("📱 Sosyal Medya Paylaşımları")
                    st.info("LinkedIn, Instagram ve X için hazır metinler.")
                    # Buraya spesifik sosyal medya prompt sonuçları gelebilir

                with tab3:
                    st.subheader("📧 Newsletter Taslağı")
                    st.write("Aboneleriniz için hazır mail metni.")

                with tab4:
                    st.subheader("🎬 Reels / TikTok Senaryosu")
                    st.success("Kamerayı karşınıza alın ve okumaya başlayın!")
                
                with tab5: # Yeni Görsel Sekmesi
                    st.subheader("🖼️ Oluşturulan Yapay Zeka Görseli")
                    if image_url:
                        st.image(image_url, caption=f"{topic} için Yapay Zeka Görseli")
                        st.download_button(label="Görseli İndir", data=requests.get(image_url).content, file_name=f"{topic}_gorsel.png", mime="image/png")
                    else:
                        st.info("Henüz bir görsel oluşturulmadı veya bir hata oluştu.")