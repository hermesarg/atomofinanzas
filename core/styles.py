import streamlit as st

def apply_styles():
    st.markdown(
        """
    <style>
    :root { --at-orange: #ff8a1f; --at-ink: var(--text-color); }
    .st-key-mobile_nav_stable { display:none; }
    @media (max-width:850px) { .st-key-topnav_stable { display:none; } .st-key-mobile_nav_stable { display:block; position:sticky; top:2.8rem; z-index:99; background:var(--background-color); } }
    .block-container {
        padding-top: .55rem;
        padding-bottom: 2.5rem;
        max-width: 1180px;
    }
    
    /* Tipografía de prueba: grotesca, pesada y compacta, sin depender de internet */
    h1, h2, h3, .at-brand, [data-testid="stMetricValue"] {
        font-family: "Segoe UI Variable Display", "Segoe UI", Arial, sans-serif;
    }
    h1, h2, h3, .at-brand {
        font-weight: 800 !important;
        letter-spacing: -0.035em;
    }
    
    /* Navegación fija */
    .st-key-desktop_nav, .st-key-mobile_nav {
        position: sticky;
        top: 2.8rem;
        z-index: 999;
        background: var(--background-color);
        backdrop-filter: blur(10px);
        border-bottom: 1px solid rgba(128,128,128,.18);
        padding-top: .2rem;
        padding-bottom: .15rem;
    }
    
    /* Mobile: menú desplegable. Desktop: botones. */
    .st-key-mobile_nav { display: none; }
    
    @media (max-width: 850px) {
        .block-container {
            padding-left: .75rem;
            padding-right: .75rem;
            padding-top: .5rem;
        }
        .st-key-desktop_nav { display: none; }
        .st-key-mobile_nav { display: block; }
        h1 { font-size: 2rem !important; }
        h2 { font-size: 1.55rem !important; }
        h3 { font-size: 1.25rem !important; }
    }
    
    @media (max-width:850px) {
        .st-key-brand_header [data-testid="stHorizontalBlock"] { flex-wrap:nowrap !important; gap:.5rem !important; align-items:center !important; }
        .st-key-brand_header [data-testid="stColumn"]:first-child { min-width:44px !important; width:44px !important; flex:0 0 44px !important; }
        .st-key-brand_header [data-testid="stColumn"]:last-child { min-width:0 !important; width:auto !important; flex:1 1 0 !important; }
        .st-key-brand_header img { width:44px !important; }
        .st-key-brand_header h1 { font-size:1.45rem !important; padding:0 !important; }
        .st-key-brand_header .stCaptionContainer { font-size:.7rem !important; }
    }
    /* Cards */
    .at-card {
        border: 1px solid rgba(128,128,128,.18);
        border-radius: 18px;
        padding: .8rem .9rem;
        margin-bottom: .8rem;
        box-shadow: 0 2px 10px rgba(0,0,0,.035);
        background: var(--secondary-background-color);
    }
    .at-muted { color: #707784; font-size: .92rem; }
    .at-big { font-size: 1.7rem; font-weight: 700; margin: .15rem 0; }
    .at-chip {
        display: inline-block;
        padding: .22rem .55rem;
        border-radius: 999px;
        background: rgba(128,128,128,.10);
        margin-right: .25rem;
        font-size: .84rem;
    }
    
    /* Electro financiero */
    .electro-card {
        border: 1px solid rgba(255,138,31,.24);
        border-radius: 20px;
        padding: .9rem 1rem;
        margin-bottom: .9rem;
        background: var(--secondary-background-color);
        box-shadow: 0 8px 26px rgba(0,0,0,.045), inset 0 0 0 1px rgba(255,194,122,.035);
    }
    .electro-title {
        font-family: "Segoe UI Variable Display", "Segoe UI", Arial, sans-serif;
        font-weight: 850;
        letter-spacing: -.035em;
        font-size: 1.55rem;
        margin-bottom: .1rem;
    }
    .electro-state {
        font-size: 1.05rem;
        font-weight: 650;
        margin-bottom: .55rem;
    }
    .electro-svg {
        width: 100%;
        height: 115px;
        display:block;
        margin:.25rem 0 .4rem 0;
        filter: drop-shadow(0 0 4px rgba(255,138,31,.18));
    }
    .electro-baseline {
        stroke: rgba(128,128,128,.16);
    }
    .electro-wave {
        stroke: url(#atomoElectroGradient);
    }
    .electro-grid {
        display:grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap:.65rem;
        margin-top:.7rem;
    }
    .electro-mini {
        border:1px solid rgba(255,138,31,.15);
        border-radius:14px;
        padding:.62rem;
        background:rgba(255,138,31,.025);
    }
    .electro-mini-title {
        font-weight:750;
        font-size:.95rem;
    }
    .electro-mini-value {
        font-size:1.2rem;
        font-weight:800;
        margin:.1rem 0;
    }
    .electro-note {
        color:#707784;
        font-size:.86rem;
    }
    .yield-card {
        border:1px solid rgba(128,128,128,.18);
        border-radius:16px;
        padding:.9rem 1rem;
        margin:.5rem 0;
    }
    @media (max-width: 850px) {
        .electro-grid { grid-template-columns: 1fr; }
        .electro-svg { height: 95px; }
    }
    
    .period-card {
        border:1px solid rgba(255,138,31,.28);
        background:rgba(255,138,31,.07);
        border-radius:14px;
        padding:.55rem .8rem;
        margin:.15rem 0 .7rem 0;
        font-size:.9rem;
    }

    .st-key-home_electro_card {
        border:1px solid rgba(255,138,31,.22);
        border-radius:18px;
        padding:.7rem .9rem;
        margin:.7rem 0;
        background:rgba(255,138,31,.045);
    }

    .help-card {
        border-left:4px solid var(--at-orange);
        background:rgba(255,138,31,.065);
        border-radius: 10px;
        padding: .65rem .85rem;
        margin: .5rem 0;
    }
    .demo-banner {
        border:1px solid rgba(255,138,31,.30);
        background:rgba(255,138,31,.08);
        color:var(--text-color);
        border-radius:14px;
        padding:.65rem .9rem;
        margin-bottom:.8rem;
    }
    .st-key-demo_welcome {
        border:1px solid rgba(255,138,31,.20);
        background:rgba(255,138,31,.035);
        border-radius:18px;
        padding:.8rem .9rem .9rem .9rem;
        margin:0 0 .9rem 0;
    }
    .st-key-demo_welcome h3 {
        margin-top:0 !important;
        padding-top:0 !important;
    }
    
    .sidebar-avatar {
        text-align:center;
        margin-bottom:.4rem;
    }
    .sidebar-title {
        font-weight:850;
        letter-spacing:-.03em;
        font-size:1.35rem;
        text-align:center;
        margin:.1rem 0 .35rem 0;
    }
    .compact-note { font-size:.88rem; color:#707784; }
    
    
    [data-testid="stSidebar"] img { border-radius:18px; }
    .atomo-brand {
      font-family:"Segoe UI Variable Display","Segoe UI",Arial,sans-serif;
      font-size:1.55rem; font-weight:850; letter-spacing:-.04em;
      color:var(--at-ink); margin:-.2rem 0 .25rem 0;
    }
    .atomo-kicker { color:#737985; font-size:.82rem; margin-bottom:.45rem; }
    [data-testid="stMetric"] { padding:.15rem 0; }
    .st-key-desktop_nav label p { font-size:.9rem !important; }
    
    
    .st-key-header_logo { overflow: visible !important; }
    .st-key-header_logo img {
        object-fit: contain !important;
        max-width: 64px !important;
        max-height: 64px !important;
    }
    [data-testid="stSidebar"] img {
        object-fit: contain !important;
    }
    
    
    /* V7: navegación y densidad */
    .st-key-topnav_stable {
        position: sticky;
        top: 2.8rem;
        z-index: 999;
        background: var(--background-color);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(128,128,128,.16);
        padding: .25rem 0 .35rem 0;
        margin-bottom: .65rem;
    }
    .st-key-topnav_stable button {
        min-height: 2.35rem !important;
        padding: .28rem .45rem !important;
        font-size: .86rem !important;
    }
    .block-container { max-width: 1180px !important; padding-top: 3.5rem !important; }
    [data-testid="stSidebar"] img { object-fit: contain !important; }
    .atomo-brand { margin-top: .1rem !important; }
    
    .at-muted, .electro-note, .compact-note, .atomo-kicker { color:var(--text-color); opacity:.76; }

    /* Mobile final: gana sobre reglas anteriores y conserva modo claro/oscuro */
    @media (max-width: 850px) {
        .block-container {
            max-width:100% !important;
            padding-top:3rem !important;
            padding-left:.65rem !important;
            padding-right:.65rem !important;
            padding-bottom:1.8rem !important;
        }
        .st-key-mobile_nav_stable {
            display:block !important;
            position:sticky;
            top:2.75rem;
            z-index:999;
            padding:.2rem 0 .35rem 0;
            margin-bottom:.35rem;
            background:var(--background-color);
            border-bottom:1px solid rgba(128,128,128,.14);
            backdrop-filter:blur(12px);
        }
        .st-key-brand_header {
            margin-bottom:.2rem !important;
        }
        .st-key-brand_header h1 {
            line-height:1.08 !important;
        }
        .st-key-demo_welcome [data-testid="stHorizontalBlock"] {
            flex-wrap:wrap !important;
            gap:.35rem !important;
        }
        .st-key-demo_welcome [data-testid="stColumn"] {
            min-width:100% !important;
            flex:1 1 100% !important;
        }
        .st-key-demo_welcome button {
            min-height:2.45rem !important;
        }
        .electro-card {
            border-radius:16px;
            padding:.72rem .72rem;
        }
        .electro-title {
            font-size:1.35rem;
        }
        .electro-state {
            font-size:.95rem;
            line-height:1.35;
        }
        .electro-svg {
            height:82px;
            margin:.15rem 0 .25rem 0;
        }
        .electro-mini {
            padding:.58rem;
        }
        [data-testid="stMetricValue"] {
            font-size:1.55rem !important;
        }
        [data-testid="stSidebar"] {
            max-width:min(88vw, 320px) !important;
        }
    }
    </style>
    """,
        unsafe_allow_html=True,
    )
    
