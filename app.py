import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components
import yfinance as yf

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
    div[data-testid="stMetricLabel"] > div { color: #888 !important; font-weight: bold; }
    .yildiz { color: #00FF41; font-weight: bold; font-size: 1.1rem; border-left: 3px solid #00FF41; padding-left: 10px; }
    .kaybeden { color: #FF003C; font-weight: bold; font-size: 1.1rem; border-left: 3px solid #FF003C; padding-left: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- FORMATLAMA FONKSİYONU ---
def para_formatla(deger):
    return f"{deger:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " TL"

# --- PORTFÖY VERİLERİ ---
portfoy = [
    # 17.02.2026 İşlemleri
    {"hisse": "EKOS.IS", "maliyet": 6.09, "lot": 834, "tarih": "17.02.2026"},

    # 18.02.2026 İşlemleri
    {"hisse": "AGROT.IS", "maliyet": 3.29, "lot": 3052, "tarih": "18.02.2026"},
    {"hisse": "AKYHO.IS", "maliyet": 2.98, "lot": 2596, "tarih": "18.02.2026"},
    {"hisse": "ARENA.IS", "maliyet": 28.85, "lot": 262, "tarih": "18.02.2026"},
    {"hisse": "BEGYO.IS", "maliyet": 4.97, "lot": 1512, "tarih": "18.02.2026"},
    {"hisse": "BUCIM.IS", "maliyet": 7.07, "lot": 1062, "tarih": "18.02.2026"},
    {"hisse": "EBEBK.IS", "maliyet": 63.63, "lot": 119, "tarih": "18.02.2026"},
    {"hisse": "KARTN.IS", "maliyet": 84.02, "lot": 90, "tarih": "18.02.2026"},
    {"hisse": "KLMSN.IS", "maliyet": 32.35, "lot": 234, "tarih": "18.02.2026"},
    {"hisse": "LILAK.IS", "maliyet": 34.12, "lot": 221, "tarih": "18.02.2026"},
    {"hisse": "LYDHO.IS", "maliyet": 194.04, "lot": 40, "tarih": "18.02.2026"},
    {"hisse": "MAKIM.IS", "maliyet": 17.02, "lot": 441, "tarih": "18.02.2026"},
    {"hisse": "RAYSG.IS", "maliyet": 230.14, "lot": 34, "tarih": "18.02.2026"},
    {"hisse": "SANFM.IS", "maliyet": 7.47, "lot": 1005, "tarih": "18.02.2026"},
    {"hisse": "SRVGY.IS", "maliyet": 3.54, "lot": 2843, "tarih": "18.02.2026"},

    # 19.02.2026 İşlemleri
    {"hisse": "DGNMO.IS", "maliyet": 5.13, "lot": 1943, "tarih": "18.02.2026"},

    # 19.02.2026 İşlemleri
    {"hisse": "AVTUR.IS", "maliyet": 18.61, "lot": 404, "tarih": "19.02.2026"},
    
    # 23.02.2026 İşlemleri
    {"hisse": "EFOR.IS", "maliyet": 23.96, "lot": 209, "tarih": "23.02.2026"},
    {"hisse": "DCTTR.IS", "maliyet": 8.85, "lot": 579, "tarih": "23.02.2026"}
]

kapatilan_portfoy = [
    {"hisse": "PENTA.IS", "maliyet": 15.25, "satis": 16.68, "lot": 166, "tarih": "18.02.2026"},
    {"hisse": "PENTA.IS", "maliyet": 15.25, "satis": 15.64, "lot": 165, "tarih": "19.02.2026"}
]

@st.cache_data(ttl=300)
def get_current_price(symbol, maliyet):
    hisse_kodu = symbol.replace(".IS", "")
    
    # 1. PLAN: Yerel Kaynak (İş Yatırım) - Bot korumasına karşı daha sağlam kimlik
    try:
        url = f"https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx/HisseTekil?hisse={hisse_kodu}"
        kimlik = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest'
        }
        istek = requests.get(url, headers=kimlik, timeout=5)
        
        if istek.status_code == 200:
            icerik = istek.json()
            if icerik.get("value") and len(icerik["value"]) > 0:
                anlik_deger = icerik["value"][0].get("Son")
                if anlik_deger is not None:
                    return float(str(anlik_deger).replace(",", "."))
    except:
        pass # İlk aşama başarısız olursa çökme, devam et.
        
    # 2. PLAN (YEDEK): Küresel Kaynak (Yahoo Finance) - Bulut İP kısıtlamasını aşmak için
    try:
        data = yf.Ticker(symbol).history(period="1d")
        if not data.empty:
            return float(data['Close'].iloc[-1])
    except:
        pass
        
    # Her iki kapı da duvar olursa sıfır bas
    return 0.0

def ana_uygulama():
    zaman = pd.Timestamp.now('Europe/Istanbul').strftime('%d.%m.%Y %H:%M')

    c_baslik, c_sayac = st.columns([4, 1])
    with c_baslik:
        st.markdown(f"<h1>>_ BIST_TEST_TERMINAL | {zaman}</h1>", unsafe_allow_html=True)
    with c_sayac:
        st.markdown('''
            <div style="text-align: right; padding-top: 15px;">
                <img src="https://api.visitorbadge.io/api/visitors?path=ilke-k-bist.streamlit.app&label=TRAFIK&labelColor=%23111111&countColor=%2300ff41&style=flat" alt="Trafik Sayacı" />
            </div>
        ''', unsafe_allow_html=True)

    # --- 1. AKTİF POZİSYON HESAPLAMALARI ---
    satirlar_acik = []
    t_maliyet_aktif, t_guncel_aktif = 0, 0
    en_iyi_hisse, en_iyi_oran = "-", -999
    en_kotu_hisse, en_kotu_oran = "-", 999

    for v in portfoy:
        son_f = get_current_price(v["hisse"], v["maliyet"])
        yuzde = ((son_f - v["maliyet"]) / v["maliyet"]) * 100 if v["maliyet"] > 0 else 0
        net = (son_f - v["maliyet"]) * v["lot"]
        buyukluk = son_f * v["lot"]
        
        t_maliyet_aktif += (v["maliyet"] * v["lot"])
        t_guncel_aktif += buyukluk
        h_adi = v["hisse"].replace(".IS", "")
        
        if yuzde > en_iyi_oran: en_iyi_oran, en_iyi_hisse = yuzde, h_adi
        if yuzde < en_kotu_oran: en_kotu_oran, en_kotu_hisse = yuzde, h_adi

        satirlar_acik.append({
            "Tarih": v.get("tarih", "-"),
            "Hisse": h_adi, "Maliyet": v["maliyet"], "Lot": v["lot"],
            "Fiyat": round(son_f, 2), "K/Z (%)": round(yuzde, 2), "Net K/Z": round(net, 2),
            "Büyüklük": round(buyukluk, 2)
        })

    t_net_aktif = t_guncel_aktif - t_maliyet_aktif
    t_yuzde_aktif = (t_net_aktif / t_maliyet_aktif) * 100 if t_maliyet_aktif > 0 else 0

    # --- 2. GERÇEKLEŞMİŞ (KAPALI) HESAPLAMALARI ---
    satirlar_kapali = []
    t_maliyet_kapali, t_satis_kapali = 0, 0
    for v in kapatilan_portfoy:
        y = ((v["satis"] - v["maliyet"]) / v["maliyet"]) * 100 if v["maliyet"] > 0 else 0
        n = (v["satis"] - v["maliyet"]) * v["lot"]
        t_maliyet_kapali += (v["maliyet"] * v["lot"])
        t_satis_kapali += (v["satis"] * v["lot"])
        satirlar_kapali.append({
            "Tarih": v.get("tarih", "-"), "Hisse": v["hisse"].replace(".IS", ""),
            "Maliyet": v["maliyet"], "Satış": v["satis"], "Lot": v["lot"],
            "K/Z (%)": round(y, 2), "Net K/Z": round(n, 2)
        })
    t_net_kapali = t_satis_kapali - t_maliyet_kapali
    t_yuzde_kapali = (t_net_kapali / t_maliyet_kapali) * 100 if t_maliyet_kapali > 0 else 0

    # --- ÖZET METRİKLER ---
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("AKTİF PORTFÖY DEĞERİ", para_formatla(t_guncel_aktif))
    c2.metric("AKTİF K/Z (Unrealized)", para_formatla(t_net_aktif), f"{t_yuzde_aktif:.2f}%")
    c3.metric("GERÇEKLEŞMİŞ K/Z (Realized)", para_formatla(t_net_kapali), f"{t_yuzde_kapali:.2f}%", delta_color="off")
    c4.markdown(f"<div class='yildiz'>⭐ YILDIZ<br>{en_iyi_hisse} (+%{en_iyi_oran:.2f})</div>", unsafe_allow_html=True)
    c5.markdown(f"<div class='kaybeden'>⚠️ ZAYIF<br>{en_kotu_hisse} (%{en_kotu_oran:.2f})</div>", unsafe_allow_html=True)

    st.markdown("---")

    # --- AKTİF TABLO VE TOPLAM ---
    st.markdown("### [ AKTİF_POZİSYONLAR ]")
    df_acik = pd.DataFrame(satirlar_acik)
    toplam_row_acik = pd.DataFrame([{"Tarih": "-", "Hisse": "TOPLAM", "Maliyet": 0, "Lot": 0, "Fiyat": 0, "K/Z (%)": t_yuzde_aktif, "Net K/Z": t_net_aktif, "Büyüklük": t_guncel_aktif}])
    df_acik_final = pd.concat([df_acik, toplam_row_acik], ignore_index=True)

    st.dataframe(
        df_acik_final.drop(columns=["Büyüklük"]).style.format({
            "Maliyet": "{:.2f} TL", "Fiyat": "{:.2f} TL", "K/Z (%)": "% {:.2f}", "Net K/Z": "{:.2f} TL"
        }).map(lambda x: 'color: #00FF41; font-weight: bold' if isinstance(x, (int, float)) and x > 0 else ('color: #FF003C; font-weight: bold' if isinstance(x, (int, float)) and x < 0 else ''), 
               subset=['K/Z (%)', 'Net K/Z'])
          .map(lambda x: 'background-color: #1a1a1a; font-weight: bold; color: #ffffff' if x == "TOPLAM" else '', subset=['Hisse']),
        width='stretch', hide_index=True # BARKOD: use_container_width KALDIRILDI, YENİ FORMAT EKLENDİ
    )

    # --- GEÇMİŞ TABLO VE TOPLAM ---
    if kapatilan_portfoy:
        st.markdown('<br><h3 style="color: #00a2ff !important;">[ GEÇMİŞ_İŞLEMLER ]</h3>', unsafe_allow_html=True)
        df_kapali = pd.DataFrame(satirlar_kapali)
        toplam_row_kapali = pd.DataFrame([{"Tarih": "-", "Hisse": "TOPLAM", "Maliyet": 0, "Satış": 0, "Lot": 0, "K/Z (%)": t_yuzde_kapali, "Net K/Z": t_net_kapali}])
        df_kapali_final = pd.concat([df_kapali, toplam_row_kapali], ignore_index=True)

        st.dataframe(
            df_kapali_final.style.format({
                "Maliyet": "{:.2f} TL", "Satış": "{:.2f} TL", "K/Z (%)": "% {:.2f}", "Net K/Z": "{:.2f} TL"
            }).map(lambda x: 'color: #00a2ff; font-weight: bold' if isinstance(x, (int, float)) and x > 0 else ('color: #FF003C; font-weight: bold' if isinstance(x, (int, float)) and x < 0 else ''), 
                   subset=['K/Z (%)', 'Net K/Z'])
              .map(lambda x: 'background-color: #1a1a1a; font-weight: bold; color: #ffffff' if x == "TOPLAM" else '', subset=['Hisse']),
            width='stretch', hide_index=True # BARKOD: use_container_width KALDIRILDI, YENİ FORMAT EKLENDİ
        )

    st.markdown("---")
    tab1, tab2 = st.tabs(["🔥 ISI HARİTASI", "📈 TRADINGVIEW"])
    with tab1:
        fig = px.treemap(df_acik, path=[px.Constant("BIST Portföyü"), 'Hisse'], values='Büyüklük',
                         color='K/Z (%)', color_continuous_scale=['#FF003C', '#111111', '#00FF41'], color_continuous_midpoint=0)
        fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), paper_bgcolor='#050505', plot_bgcolor='#050505', font=dict(color='#00FF41'))
        st.plotly_chart(fig, width='stretch') # BARKOD: YENİ FORMAT EKLENDİ
    with tab2:
        tv_secim = st.selectbox("İncelenecek Hisseyi Seçin:", [h["Hisse"] for h in satirlar_acik])
        tv_sembol = f"BIST:{tv_secim}"
        st.markdown(f"<div style='text-align: center; margin-bottom: 15px;'><a href='https://tr.tradingview.com/chart/?symbol={tv_sembol}' target='_blank' style='background-color: #111111; border: 1px solid #00FF41; color: #00FF41; padding: 10px 20px; text-decoration: none; font-weight: bold; border-radius: 5px; font-family: monospace;'>⚡ {tv_secim} GRAFİĞİNİ TRADINGVIEW'DA AÇ</a></div>", unsafe_allow_html=True)
        tv_html = f'<div class="tradingview-widget-container"><div id="tradingview_123"></div><script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script><script type="text/javascript">new TradingView.widget({{"width": "100%","height": 500,"symbol": "{tv_sembol}","interval": "D","timezone": "Europe/Istanbul","theme": "dark","style": "1","locale": "tr","enable_publishing": false,"backgroundColor": "#050505","hide_top_toolbar": false,"save_image": false,"container_id": "tradingview_123"}});</script></div>'
        components.html(tv_html, height=500)

if __name__ == "__main__":
    ana_uygulama()
