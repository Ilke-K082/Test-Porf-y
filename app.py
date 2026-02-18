import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import streamlit.components.v1 as components

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="BIST_TERMINAL", layout="wide", initial_sidebar_state="collapsed")

# --- HACKER TEMASI (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; font-family: 'Courier New', monospace; }
    h1, h2, h3 { color: #00FF41 !important; text-shadow: 0px 0px 5px #00FF41; }
    div[data-testid="metric-container"] {
        background-color: #111111; border: 1px solid #333; padding: 15px; border-radius: 5px;
        box-shadow: 0px 0px 8px rgba(0, 255, 65, 0.1);
    }
    div[data-testid="stMetricLabel"] > div { color: #00a2ff !important; font-weight: bold; }
    .yildiz { color: #00FF41; font-weight: bold; font-size: 1.2rem; }
    .kaybeden { color: #FF003C; font-weight: bold; font-size: 1.2rem; }
    </style>
""", unsafe_allow_html=True)

# --- FORMATLAMA FONKSİYONU ---
def para_formatla(deger):
    return f"{deger:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " TL"

# --- PORTFÖY VERİLERİ ---
portfoy = [
    {"hisse": "AKYHO.IS", "maliyet": 3.03, "lot": 1724, "tarih": "17.02.2026"},
    {"hisse": "DGNMO.IS", "maliyet": 5.34, "lot": 928, "tarih": "17.02.2026"},
    {"hisse": "SRVGY.IS", "maliyet": 3.69, "lot": 1374, "tarih": "17.02.2026"},
    {"hisse": "KLMSN.IS", "maliyet": 32.92, "lot": 154, "tarih": "17.02.2026"},
    {"hisse": "EKOS.IS", "maliyet": 6.09, "lot": 834, "tarih": "17.02.2026"},
    {"hisse": "ARENA.IS", "maliyet": 29.36, "lot": 172, "tarih": "17.02.2026"},
    {"hisse": "PENTA.IS", "maliyet": 15.25, "lot": 165, "tarih": "17.02.2026"},
    {"hisse": "RAYSG.IS", "maliyet": 234.30, "lot": 22, "tarih": "17.02.2026"},
    {"hisse": "BUCIM.IS", "maliyet": 7.19, "lot": 696, "tarih": "17.02.2026"}
]

kapatilan_portfoy = [
    {"hisse": "PENTA.IS", "maliyet": 15.25, "satis": 16.68, "lot": 166, "tarih": "18.02.2026"}
]

@st.cache_data(ttl=300)
def get_current_price(symbol, maliyet):
    try:
        data = yf.Ticker(symbol).history(period="1d")
        return data['Close'].iloc[-1] if not data.empty else maliyet
    except: return maliyet

def ana_uygulama():
    # Sunucu saatine 3 saat ekleyip Türkiye saatini buluyoruz
    tr_saati = datetime.now() + timedelta(hours=3)
    zaman = tr_saati.strftime('%d.%m.%Y %H:%M')
    st.markdown(f"<h1>>_ BIST_TEST_PORTFY_TERMINAL | {zaman}</h1>", unsafe_allow_html=True)

    # --- HESAPLAMALAR ---
    satirlar_acik = []
    t_maliyet, t_guncel = 0, 0
    en_iyi_hisse, en_iyi_oran = "-", -999
    en_kotu_hisse, en_kotu_oran = "-", 999

    for v in portfoy:
        son_f = get_current_price(v["hisse"], v["maliyet"])
        yuzde = ((son_f - v["maliyet"]) / v["maliyet"]) * 100
        net = (son_f - v["maliyet"]) * v["lot"]
        buyukluk = son_f * v["lot"]
        
        t_maliyet += (v["maliyet"] * v["lot"])
        t_guncel += buyukluk
        hisse_adi = v["hisse"].replace(".IS", "")
        
        # Yıldız ve Kaybeden tespiti
        if yuzde > en_iyi_oran:
            en_iyi_oran = yuzde
            en_iyi_hisse = hisse_adi
        if yuzde < en_kotu_oran:
            en_kotu_oran = yuzde
            en_kotu_hisse = hisse_adi

        satirlar_acik.append({
            "Hisse": hisse_adi,
            "Maliyet": v["maliyet"],
            "Lot": v["lot"],
            "Fiyat": round(son_f, 2),
            "K/Z (%)": round(yuzde, 2),
            "Net K/Z": round(net, 2),
            "Büyüklük": round(buyukluk, 2)
        })

    t_net = t_guncel - t_maliyet
    t_yuzde = (t_net / t_maliyet) * 100 if t_maliyet > 0 else 0

    # --- ÖZET METRİKLER VE YILDIZLAR ---
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("PORTFÖY DEĞERİ", para_formatla(t_guncel))
    c2.metric("TOPLAM K/Z", para_formatla(t_net), f"{t_yuzde:.2f}%")
    c3.metric("AKTİF HİSSE", len(portfoy))
    c4.markdown(f"<div class='yildiz'>⭐ GÜNÜN YILDIZI<br>{en_iyi_hisse} (+%{en_iyi_oran:.2f})</div>", unsafe_allow_html=True)
    c5.markdown(f"<div class='kaybeden'>⚠️ ZAYIF HALKA<br>{en_kotu_hisse} (%{en_kotu_oran:.2f})</div>", unsafe_allow_html=True)

    st.markdown("---")

    # --- TABLOLAR ---
    st.markdown("### [ AKTİF_POZİSYONLAR ]")
    df_acik = pd.DataFrame(satirlar_acik)
    st.dataframe(
        df_acik.drop(columns=["Büyüklük"]).style.format({
            "Maliyet": "{:.2f} TL", "Fiyat": "{:.2f} TL", 
            "K/Z (%)": "% {:.2f}", "Net K/Z": "{:.2f} TL"
        }).map(lambda x: 'color: #00FF41' if isinstance(x, (int, float)) and x > 0 else ('color: #FF003C' if isinstance(x, (int, float)) and x < 0 else ''), 
               subset=['K/Z (%)', 'Net K/Z']),
        use_container_width=True, hide_index=True
    )

    if kapatilan_portfoy:
        st.markdown('<br><h3 style="color: #00a2ff !important;">[ GEÇMİŞ_İŞLEMLER ]</h3>', unsafe_allow_html=True)
        satirlar_kapali = []
        for v in kapatilan_portfoy:
            y = ((v["satis"] - v["maliyet"]) / v["maliyet"]) * 100
            n = (v["satis"] - v["maliyet"]) * v["lot"]
            satirlar_kapali.append({
                "Tarih": v.get("tarih", "-"), "Hisse": v["hisse"].replace(".IS", ""), "Maliyet": v["maliyet"],
                "Satış": v["satis"], "Lot": v["lot"], "K/Z (%)": round(y, 2), "Net K/Z": round(n, 2)
            })
        df_kapali = pd.DataFrame(satirlar_kapali)
        st.dataframe(
            df_kapali.style.format({
                "Maliyet": "{:.2f} TL", "Satış": "{:.2f} TL", "K/Z (%)": "% {:.2f}", "Net K/Z": "{:.2f} TL"
            }).map(lambda x: 'color: #00a2ff' if isinstance(x, (int, float)) and x > 0 else ('color: #FF003C' if isinstance(x, (int, float)) and x < 0 else ''), 
                   subset=['K/Z (%)', 'Net K/Z']),
            use_container_width=True, hide_index=True
        )

    st.markdown("---")

    # --- ALT PANELLER (SEKMELER) ---
    tab1, tab2 = st.tabs(["🔥 ISI HARİTASI", "📈 TRADINGVIEW"])

    with tab1:
        st.markdown("Kutu büyüklükleri yatırılan sermayeyi, renkler ise Kâr/Zarar durumunu gösterir.")
        fig = px.treemap(df_acik, path=[px.Constant("BIST Portföyü"), 'Hisse'], values='Büyüklük',
                         color='K/Z (%)', color_continuous_scale=['#FF003C', '#111111', '#00FF41'],
                         color_continuous_midpoint=0)
        fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), paper_bgcolor='#050505', plot_bgcolor='#050505', font=dict(color='#00FF41'))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        tv_secim = st.selectbox("İncelenecek Hisseyi Seçin:", [h["Hisse"] for h in satirlar_acik])
        tv_sembol = f"BIST:{tv_secim}"
        
        # BIST kısıtlamalarına karşı hızlı bağlantı butonu
        st.markdown(f"<div style='text-align: center; margin-bottom: 15px;'><a href='https://tr.tradingview.com/chart/?symbol={tv_sembol}' target='_blank' style='background-color: #111111; border: 1px solid #00FF41; color: #00FF41; padding: 10px 20px; text-decoration: none; font-weight: bold; border-radius: 5px; font-family: monospace;'>⚡ {tv_secim} GRAFİĞİNİ TRADINGVIEW'DA AÇ</a></div>", unsafe_allow_html=True)
        
        tv_html = f"""
        <div class="tradingview-widget-container">
          <div id="tradingview_123"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{
          "width": "100%",
          "height": 500,
          "symbol": "{tv_sembol}",
          "interval": "D",
          "timezone": "Europe/Istanbul",
          "theme": "dark",
          "style": "1",
          "locale": "tr",
          "enable_publishing": false,
          "backgroundColor": "#050505",
          "hide_top_toolbar": false,
          "save_image": false,
          "container_id": "tradingview_123"
        }});
          </script>
        </div>
        """
        components.html(tv_html, height=500)

if __name__ == "__main__":
    ana_uygulama()
