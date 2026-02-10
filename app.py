import streamlit as st
from openai import OpenAI
import plotly.graph_objects as go
import re

# --- API YAPILANDIRMASI ---
OPENAI_KEY = "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"
client = OpenAI(api_key=OPENAI_KEY)

# --- ZEKA FONKSİYONLARI ---
def analiz_ve_yol_haritasi(marka, sektor):
    try:
        # 1. Puanlama (Gerçekçi)
        p_prompt = f"'{marka}' ({sektor}) markasının dijital ağırlığını 0-100 arası puanla. Sadece rakam."
        p_res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": p_prompt}]).choices[0].message.content
        puan = int(''.join(filter(str.isdigit, p_res)))

        # 2. Strateji ve Yol Haritası (Tek Promptta Birleştirdik)
        combined_prompt = f"""
        Marka: {marka} ({sektor})
        AI Skoru: {puan}
        Görev: Bu markanın konumunu analiz et ve skoru 50'ye çıkarmak için 3 somut pazarlama stratejisi öner.
        """
        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": combined_prompt}]).choices[0].message.content
        
        return puan, res
    except:
        return 50, "Analiz yapılamadı."

# --- SIDEBAR ---
st.set_page_config(page_title="VetraPos AI Ultimate", layout="wide")
with st.sidebar:
    st.title("🛡️ Operasyon Paneli")
    marka_adi = st.text_input("Markanız", "VetraPos")
    sektor_adi = st.text_input("Sektör", "Sanal POS")
    st.divider()
    nav = st.radio("Menü", ["📊 Dashboard", "✍️ İçerik Üretimi"])

# --- DASHBOARD ---
if nav == "📊 Dashboard":
    st.markdown(f"<h1>🚀 {marka_adi} Analiz Merkezi</h1>", unsafe_allow_html=True)
    
    if st.button("🔄 Verileri Güncelle", use_container_width=True) or "puan" not in st.session_state:
        p, s = analiz_ve_yol_haritasi(marka_adi, sektor_adi)
        st.session_state["puan"] = p
        st.session_state["strateji"] = s
        st.rerun()

    c1, c2 = st.columns([1, 1.5])
    with c1:
        fig = go.Figure(go.Indicator(mode="gauge+number", value=st.session_state["puan"], title={'text': "AI Skoru"},
                        gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#3B82F6"}}))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("🗺️ Stratejik Yol Haritası")
        st.info(st.session_state["strateji"])

# --- İÇERİK ÜRETİMİ (STRATEJİYE BAĞLI) ---
elif nav == "✍️ İçerik Üretimi":
    st.title("🚀 Strateji Odaklı İçerik Fabrikası")
    
    if "strateji" in st.session_state:
        st.write("💡 **Mevcut Stratejinize Dayalı İçerik Üretiliyor:**")
        st.caption(st.session_state["strateji"][:150] + "...") # Stratejinin kısa özeti
        
        if st.button("🌟 Stratejiye Uygun İçerik Paketini Hazırla", use_container_width=True):
            with st.spinner("Stratejinize uygun içerikler tasarlanıyor..."):
                content_prompt = f"""
                Şu stratejiye uygun olarak {marka_adi} için 1 Blog yazısı ve 1 Sosyal Medya postu hazırla:
                Strateji: {st.session_state['strateji']}
                Lütfen [BLOG] ve [SOSYAL] başlıklarıyla yaz.
                """
                res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": content_prompt}]).choices[0].message.content
                st.markdown(res)
    else:
        st.warning("Önce Dashboard üzerinden bir analiz yapmalısınız!")