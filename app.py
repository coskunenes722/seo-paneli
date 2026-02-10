import streamlit as st
from openai import OpenAI
import plotly.graph_objects as go
import re

# --- API YAPILANDIRMASI ---
OPENAI_KEY = "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"
client = OpenAI(api_key=OPENAI_KEY)

def analiz_gercekci(marka, sektor):
    try:
        # SERT FİLTRE PROMPT'U
        p_prompt = f"""
        Görev: Markanın dijital bilinirliğini (AI Skoru) 0-100 arası puanla.
        Marka: {marka} | Sektör: {sektor}
        
        KESİN PUANLAMA KRİTERLERİ:
        - Coca-Cola, Google, Amazon: 95-100 puan.
        - Türkiye genelinde herkesin bildiği markalar: 60-85 puan.
        - VetraPos gibi yeni veya gelişmekte olan girişimler: 5-25 PUANI GEÇEMEZ.
        
        Sadece rakam ver. Eğer marka çok yeniyse 15-20 arası bir değer ver.
        """
        p_res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": p_prompt}]).choices[0].message.content
        puan = int(''.join(filter(str.isdigit, p_res)))
        
        # Yol Haritası (Neden düşük puan aldığını açıklayan içerik)
        h_prompt = f"{marka} markasının skoru {puan}. Bu skorun neden düşük olduğunu ve gerçekçi büyüme adımlarını özetle."
        harita = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": h_prompt}]).choices[0].message.content
        
        return puan, harita
    except:
        return 10, "Kota veya bağlantı sorunu nedeniyle analiz yapılamadı."

# --- ARAYÜZ ---
with st.sidebar:
    st.title("🛡️ Operasyon Paneli")
    marka_adi = st.text_input("Markanız", "VetraPos")
    sektor_adi = st.text_input("Sektör", "Sanal POS")
    st.divider()
    nav = st.radio("Menü", ["📊 Dashboard", "✍️ İçerik Üretimi"])

if nav == "📊 Dashboard":
    st.markdown(f"<h1>🚀 {marka_adi} Analiz Merkezi</h1>", unsafe_allow_html=True)
    
    if st.button("🔄 Gerçekçi Analiz Yap", use_container_width=True) or "puan" not in st.session_state:
        with st.spinner("Piyasa verileri kıyaslanıyor..."):
            p, h = analiz_gercekci(marka_adi, sektor_adi)
            st.session_state["puan"] = p
            st.session_state["harita"] = h
            st.rerun()

    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.markdown(f"### 🎯 Mevcut Durum")
        fig = go.Figure(go.Indicator(mode="gauge+number", value=st.session_state["puan"],
                        gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#3B82F6"}}))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("### 🗺️ Neden Bu Skoru Aldınız?")
        st.info(st.session_state["harita"])
elif nav == "✍️ İçerik Üretimi":
    st.markdown(f"<h1>✍️ {marka_adi} İçerik Fabrikası</h1>", unsafe_allow_html=True)
    
    # Dashboard'daki stratejiye erişim kontrolü
    if "strateji" in st.session_state:
        st.info(f"💡 **Mevcut Strateji Odağı:** {st.session_state['strateji'][:150]}...")
        
        # Konu ve Ton Seçimi için Kolonlar
        c1, c2 = st.columns(2)
        with c1:
            icerik_konusu = st.text_input("📝 İçerik Ana Başlığı", placeholder="Örn: Sanal POS Seçerken Dikkat Edilmesi Gerekenler")
        with c2:
            icerik_tonu = st.selectbox("🎭 İçerik Tonu", ["Profesyonel & Kurumsal", "Samimi & Enerjik", "Teknik & Detaylı"])

        if st.button("🚀 360° İçerik Paketini Hazırla", use_container_width=True):
            if not icerik_konusu:
                st.warning("Lütfen bir konu başlığı girin.")
            else:
                with st.spinner("Yapay Zeka stratejinize uygun içerikleri dokuyor..."):
                    # Tek bir prompt ile tüm paket
                    prompt = f"""
                    Strateji: {st.session_state['strateji']}
                    Konu: {icerik_konusu}
                    Ton: {icerik_tonu}
                    Marka: {marka_adi}
                    
                    Lütfen şu etiketleri kullanarak içerik üret:
                    [BLOG_B] (Kapsamlı SEO uyumlu makale) [BLOG_S]
                    [LINKEDIN_B] (Profesyonel network odaklı post) [LINKEDIN_S]
                    [INSTA_B] (Dikkat çekici kısa post ve hashtagler) [INSTA_S]
                    [MAIL_B] (Müşteriler için ilgi çekici e-bülten) [MAIL_S]
                    """
                    full_res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}]).choices[0].message.content
                    
                    # Veriyi parçalama fonksiyonu
                    def parse_content(tag, text):
                        match = re.search(f"\[{tag}_B\](.*?)\[{tag}_S\]", text, re.DOTALL)
                        return match.group(1).strip() if match else "İçerik üretilemedi."

                    # PROFESYONEL SEKME YAPISI
                    tab_blog, tab_social, tab_mail = st.tabs(["📄 SEO Blog Yazısı", "📱 Sosyal Medya", "📧 E-Bülten"])
                    
                    with tab_blog:
                        st.markdown(parse_content("BLOG", full_res))
                    
                    with tab_social:
                        col_l, col_i = st.columns(2)
                        with col_l:
                            st.subheader("🔗 LinkedIn")
                            st.write(parse_content("LINKEDIN", full_res))
                        with col_i:
                            st.subheader("📸 Instagram")
                            st.write(parse_content("INSTA", full_res))
                            
                    with tab_mail:
                        st.code(parse_content("MAIL", full_res), language="markdown")
    else:
        st.warning("⚠️ Lütfen önce Dashboard sekmesinden 'Verileri Güncelle' butonuna basarak bir strateji oluşturun.")