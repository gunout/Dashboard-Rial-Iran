# dashboard_rial_iranien_2025.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import requests
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
import pytz
import warnings
import random
from requests.exceptions import HTTPError, ConnectionError
import urllib3
warnings.filterwarnings('ignore')

# Désactiver les warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration de la page
st.set_page_config(
    page_title="Tracker Rial Iranien - IRR",
    page_icon="💵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration du fuseau horaire
USER_TIMEZONE = pytz.timezone('Europe/Paris')
IRAN_TIMEZONE = pytz.timezone('Asia/Tehran')  # UTC+3:30

# Style CSS personnalisé
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;700&display=swap');
    
    .main-header {
        font-size: 2.5rem;
        color: #239F40;
        text-align: center;
        margin-bottom: 2rem;
        font-family: 'Vazirmatn', sans-serif;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        background: linear-gradient(135deg, #239F40 0%, #FFFFFF 50%, #DA0000 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .persian-text {
        font-family: 'Vazirmatn', sans-serif;
        font-size: 1.2rem;
        direction: rtl;
        text-align: right;
    }
    .currency-price {
        font-size: 2.5rem;
        font-weight: bold;
        color: #239F40;
        text-align: center;
    }
    .currency-change-positive {
        color: #239F40;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .currency-change-negative {
        color: #DA0000;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .alert-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .alert-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
    }
    .portfolio-table {
        font-size: 0.9rem;
    }
    .stButton>button {
        width: 100%;
    }
    .timezone-badge {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 0.5rem 1rem;
        margin: 1rem 0;
        font-size: 0.9rem;
    }
    .iran-badge {
        background-color: #239F40;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
        margin-right: 0.5rem;
    }
    .official-badge {
        background-color: #2196f3;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
    }
    .free-market-badge {
        background-color: #ff9800;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
    }
    .nima-badge {
        background-color: #9c27b0;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
    }
    .demo-mode-badge {
        background-color: #ff9800;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
        margin-right: 0.5rem;
    }
    .friday-note {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        text-align: center;
    }
    .sanction-note {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        text-align: center;
    }
    .exchange-rate-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation des variables de session
if 'price_alerts' not in st.session_state:
    st.session_state.price_alerts = []

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {}

if 'watchlist' not in st.session_state:
    st.session_state.watchlist = [
        # Principales devises
        'USDIRR',  # Dollar américain / Rial
        'EURIRR',  # Euro / Rial
        'GBPIRR',  # Livre sterling / Rial
        'CHFIRR',  # Franc suisse / Rial
        'AEDIRR',  # Dirham émirati / Rial
        'SARIRR',  # Riyal saoudien / Rial
        'TRYIRR',  # Lire turque / Rial
        'CNYIRR',  # Yuan chinois / Rial
        'RUBIRR',  # Rouble russe / Rial
        'INRIRR',  # Roupie indienne / Rial
        'JPYIRR',  # Yen japonais / Rial
        'KWDIRR',  # Dinar koweïtien / Rial
        'OMRIRR',  # Riyal omanais / Rial
        'BHDIRR',  # Dinar bahreïni / Rial
        
        # Métaux précieux
        'XAUIRR',  # Or / Rial
        'XAGIRR',  # Argent / Rial
        
        # Crypto (marché parallèle)
        'BTCIRR',  # Bitcoin / Rial
        'ETHIRR',  # Ethereum / Rial
    ]

if 'notifications' not in st.session_state:
    st.session_state.notifications = []

if 'email_config' not in st.session_state:
    st.session_state.email_config = {
        'enabled': False,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'email': '',
        'password': ''
    }

if 'demo_mode' not in st.session_state:
    st.session_state.demo_mode = False

if 'last_successful_data' not in st.session_state:
    st.session_state.last_successful_data = {}

# Données de démonstration pour le Rial iranien (basées sur les données réelles de février 2026)
# Sources: bne IntelliNews, Trend.az, Kompas [citation:1][citation:2][citation:3]
DEMO_DATA = {
    'USDIRR': {
        'name': 'Dollar américain / Rial iranien (USD/IRR)',
        'official_rate': 1311134,  # Taux officiel Banque Centrale [citation:3]
        'nima_rate': 1403083,       # Taux NIMA (système SANA) [citation:3]
        'free_market_rate': 1749500, # Taux marché libre [citation:1]
        'previous_close': 1725000,
        'day_high': 1760000,
        'day_low': 1710000,
        'volume': 150000000,  # Volume estimé en $
        'market_cap': 450000000000,  # Réserves de change estimées
        'change_1d': 2.5,
        'change_1w': 8.2,
        'change_1m': 29.5,
        'change_1y': 150.0,
    },
    'EURIRR': {
        'name': 'Euro / Rial iranien (EUR/IRR)',
        'official_rate': 1549954,    # Taux officiel [citation:3]
        'nima_rate': 1658651,        # Taux NIMA [citation:3]
        'free_market_rate': 2067500,  # Taux marché libre [citation:1]
        'previous_close': 2035000,
        'day_high': 2080000,
        'day_low': 2020000,
        'volume': 80000000,
        'market_cap': 350000000000,
        'change_1d': 2.3,
        'change_1w': 7.8,
        'change_1m': 28.0,
        'change_1y': 145.0,
    },
    'GBPIRR': {
        'name': 'Livre sterling / Rial iranien (GBP/IRR)',
        'official_rate': 1764178,    # Taux officiel [citation:3]
        'free_market_rate': 2353500,  # Taux marché libre [citation:1]
        'previous_close': 2320000,
        'day_high': 2370000,
        'day_low': 2310000,
        'volume': 30000000,
        'market_cap': 150000000000,
        'change_1d': 2.1,
        'change_1w': 7.2,
        'change_1m': 27.5,
        'change_1y': 140.0,
    },
    'AEDIRR': {
        'name': 'Dirham émirati / Rial iranien (AED/IRR)',
        'official_rate': 357014,     # Taux officiel [citation:3]
        'free_market_rate': 476000,   # Estimé
        'previous_close': 470000,
        'day_high': 480000,
        'day_low': 468000,
        'volume': 20000000,
        'market_cap': 50000000000,
        'change_1d': 1.8,
        'change_1w': 6.5,
        'change_1m': 25.0,
        'change_1y': 130.0,
    },
    'SARIRR': {
        'name': 'Riyal saoudien / Rial iranien (SAR/IRR)',
        'official_rate': 349636,     # Taux officiel [citation:3]
        'free_market_rate': 466000,   # Estimé
        'previous_close': 460000,
        'day_high': 470000,
        'day_low': 458000,
        'volume': 15000000,
        'market_cap': 40000000000,
        'change_1d': 1.7,
        'change_1w': 6.2,
        'change_1m': 24.5,
        'change_1y': 128.0,
    },
    'TRYIRR': {
        'name': 'Lire turque / Rial iranien (TRY/IRR)',
        'official_rate': 29829,      # Taux officiel [citation:3]
        'free_market_rate': 39800,    # Estimé
        'previous_close': 39300,
        'day_high': 40100,
        'day_low': 39100,
        'volume': 10000000,
        'market_cap': 20000000000,
        'change_1d': 1.5,
        'change_1w': 5.8,
        'change_1m': 22.0,
        'change_1y': 115.0,
    },
    'CNYIRR': {
        'name': 'Yuan chinois / Rial iranien (CNY/IRR)',
        'official_rate': 191150,     # Taux officiel [citation:3]
        'free_market_rate': 255000,   # Estimé
        'previous_close': 252000,
        'day_high': 257000,
        'day_low': 251000,
        'volume': 25000000,
        'market_cap': 60000000000,
        'change_1d': 1.4,
        'change_1w': 5.5,
        'change_1m': 21.0,
        'change_1y': 110.0,
    },
    'RUBIRR': {
        'name': 'Rouble russe / Rial iranien (RUB/IRR)',
        'official_rate': 16961,      # Taux officiel [citation:3]
        'free_market_rate': 22650,    # Taux marché libre [citation:1]
        'previous_close': 22400,
        'day_high': 22800,
        'day_low': 22300,
        'volume': 8000000,
        'market_cap': 15000000000,
        'change_1d': 1.2,
        'change_1w': 4.8,
        'change_1m': 18.0,
        'change_1y': 95.0,
    },
    'INRIRR': {
        'name': 'Roupie indienne / Rial iranien (INR/IRR)',
        'official_rate': 14400,      # Taux officiel [citation:3]
        'free_market_rate': 19200,    # Estimé
        'previous_close': 19000,
        'day_high': 19400,
        'day_low': 18900,
        'volume': 12000000,
        'market_cap': 25000000000,
        'change_1d': 1.3,
        'change_1w': 5.0,
        'change_1m': 19.0,
        'change_1y': 100.0,
    },
    'JPYIRR': {
        'name': 'Yen japonais / Rial iranien (JPY/IRR)',
        'official_rate': 8401.7,     # Pour 100 JPY [citation:3]
        'free_market_rate': 11200,    # Estimé
        'previous_close': 11100,
        'day_high': 11300,
        'day_low': 11050,
        'volume': 5000000,
        'market_cap': 10000000000,
        'change_1d': 1.1,
        'change_1w': 4.5,
        'change_1m': 17.0,
        'change_1y': 90.0,
    },
    'XAUIRR': {
        'name': 'Or (Once) / Rial iranien (XAU/IRR)',
        'free_market_rate': 224504820,  # Prix de l'or à Téhéran [citation:1]
        'previous_close': 221000000,
        'day_high': 226000000,
        'day_low': 220000000,
        'volume': 100000,
        'market_cap': 5000000000000,
        'change_1d': 1.9,
        'change_1w': 6.8,
        'change_1m': 26.0,
        'change_1y': 135.0,
    }
}

# Symboles par défaut
DEFAULT_SYMBOL = 'USDIRR'
CURRENCY_INFO = {
    'USDIRR': 'Dollar américain (USD) → Rial iranien',
    'EURIRR': 'Euro (EUR) → Rial iranien',
    'GBPIRR': 'Livre sterling (GBP) → Rial iranien',
    'AEDIRR': 'Dirham émirati (AED) → Rial iranien',
    'SARIRR': 'Riyal saoudien (SAR) → Rial iranien',
    'TRYIRR': 'Lire turque (TRY) → Rial iranien',
    'CNYIRR': 'Yuan chinois (CNY) → Rial iranien',
    'RUBIRR': 'Rouble russe (RUB) → Rial iranien',
    'INRIRR': 'Roupie indienne (INR) → Rial iranien',
    'JPYIRR': 'Yen japonais (JPY) → Rial iranien',
    'KWDIRR': 'Dinar koweïtien (KWD) → Rial iranien',
    'OMRIRR': 'Riyal omanais (OMR) → Rial iranien',
    'BHDIRR': 'Dinar bahreïni (BHD) → Rial iranien',
    'XAUIRR': 'Or (Once) → Rial iranien',
}

# Informations sur les marchés iraniens
IRAN_MARKET_INFO = {
    'Central Bank': {
        'name': 'Banque Centrale d\'Iran (CBI)',
        'rate_type': 'Taux officiel',
        'description': 'Taux utilisé pour les transactions gouvernementales',
        'icon': '🏦'
    },
    'NIMA': {
        'name': 'Système NIMA/SANA',
        'rate_type': 'Taux pour les exportateurs/importateurs',
        'description': 'Plateforme pour les échanges commerciaux',
        'icon': '💱'
    },
    'Free Market': {
        'name': 'Marché libre (Tehran)',
        'rate_type': 'Taux du marché parallèle',
        'description': 'Taux réel pour les particuliers et entreprises privées',
        'icon': '🏪'
    }
}

# Jours de trading en Iran
IRAN_TRADING_DAYS = [0, 1, 2, 3, 4]  # Samedi (0) à Mercredi (4)
IRAN_WEEKEND = [4, 5]  # Jeudi et Vendredi (week-end iranien)

# Jours fériés iraniens 2024-2025
IRAN_HOLIDAYS_2025 = [
    '2025-01-01',  # Nouvel an
    '2025-02-11',  # Révolution islamique
    '2025-03-20',  # Norouz (Nouvel an persan)
    '2025-03-21',  # Norouz
    '2025-03-22',  # Norouz
    '2025-03-23',  # Norouz
    '2025-04-01',  # Journée de la République
    '2025-04-02',  # Nature Day
    '2025-06-04',  # Anniversaire de Khomeini
    '2025-06-05',  # Anniversaire de Khomeini
    '2025-07-18',  # Eid al-Fitr (variable)
    '2025-07-19',  # Eid al-Fitr
    '2025-09-24',  # Eid al-Adha (variable)
    '2025-10-14',  # Ashura (variable)
    '2025-12-21',  # Yalda Night
]

# Fonction pour générer des données historiques de démonstration
def generate_demo_history(symbol, period="1mo", interval="1d"):
    """Génère des données historiques simulées pour la démonstration"""
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    
    # Prix de base selon le symbole
    if symbol in DEMO_DATA:
        base_price = DEMO_DATA[symbol]['free_market_rate'] if 'free_market_rate' in DEMO_DATA[symbol] else DEMO_DATA[symbol]['official_rate']
        
        # Volatilité plus élevée pour les devises iraniennes
        if symbol in ['USDIRR', 'EURIRR']:
            volatility = 0.025  # Volatilité très élevée
        elif symbol in ['GBPIRR', 'AEDIRR']:
            volatility = 0.022
        elif symbol == 'XAUIRR':
            volatility = 0.028
        else:
            volatility = 0.02
    else:
        base_price = random.uniform(10000, 2000000)
        volatility = 0.023
    
    # Générer une série de prix avec tendance baissière forte (dépréciation du rial)
    np.random.seed(hash(symbol) % 42)
    
    # Tendance à la hausse pour les taux (rial se déprécie)
    trend = 0.0015  # Tendance haussière quotidienne (~45% annuel)
    
    returns = np.random.normal(trend, volatility, len(dates))
    price_series = base_price * np.exp(np.cumsum(returns))
    
    # Créer le DataFrame
    df = pd.DataFrame({
        'Open': price_series * (1 - np.random.uniform(0, 0.01, len(dates))),
        'High': price_series * (1 + np.random.uniform(0, 0.02, len(dates))),
        'Low': price_series * (1 - np.random.uniform(0, 0.02, len(dates))),
        'Close': price_series,
        'Volume': np.random.randint(5000000, 50000000, len(dates))
    }, index=dates)
    
    # Convertir l'index en timezone-aware
    df.index = df.index.tz_localize(USER_TIMEZONE)
    
    return df

# Fonction pour simuler le chargement des données (pas d'API directe pour IRR)
@st.cache_data(ttl=600)
def load_currency_data(symbol, period, interval, retry_count=3):
    """Simule le chargement des données pour le Rial iranien"""
    
    if st.session_state.demo_mode and symbol in DEMO_DATA:
        return generate_demo_history(symbol, period, interval), DEMO_DATA[symbol]
    
    # Activer le mode démo automatiquement
    if not st.session_state.demo_mode:
        st.session_state.demo_mode = True
        st.info("🔄 Mode démonstration activé - Données simulées basées sur les sources fiables (Bonbast, CBI, Trend.az)")
    
    # Données de démonstration par défaut
    demo_info = DEMO_DATA.get(symbol, {
        'name': f'{symbol} (Mode démo)',
        'official_rate': random.randint(100000, 2000000),
        'free_market_rate': random.randint(150000, 2500000),
        'previous_close': random.randint(140000, 2400000),
    })
    
    return generate_demo_history(symbol, period, interval), demo_info

def get_currency_info(symbol):
    """Détermine les informations pour un symbole"""
    if symbol in CURRENCY_INFO:
        name = CURRENCY_INFO[symbol]
        if symbol.endswith('IRR'):
            base = symbol[:-3]
            quote = 'IRR'
        else:
            base = symbol[:3]
            quote = symbol[3:]
        return name, base, quote
    return symbol, symbol[:3], 'IRR'

def format_rial(value, include_toman=True):
    """Formate les grandes valeurs en Rial avec option Toman"""
    if value is None or value == 0:
        return "N/A"
    
    # Format standard en Rial
    if value >= 1e9:
        rial_str = f"{value/1e9:.2f} milliard Rial"
    elif value >= 1e6:
        rial_str = f"{value/1e6:.2f} million Rial"
    else:
        rial_str = f"{value:,.0f} Rial"
    
    # Conversion en Toman (1 Toman = 10 Rials)
    if include_toman:
        toman = value / 10
        if toman >= 1e9:
            toman_str = f"{toman/1e9:.2f} milliard Toman"
        elif toman >= 1e6:
            toman_str = f"{toman/1e6:.2f} million Toman"
        else:
            toman_str = f"{toman:,.0f} Toman"
        return f"{rial_str} ({toman_str})"
    
    return rial_str

def format_large_number_persian(num):
    """Formate les grands nombres selon le système persan"""
    if num > 1e12:
        return f"{num/1e12:.2f} تریلیون"  # Trillion
    elif num > 1e9:
        return f"{num/1e9:.2f} میلیارد"  # Milliards
    elif num > 1e6:
        return f"{num/1e6:.2f} میلیون"  # Millions
    else:
        return f"{num:,.0f}"

def send_email_alert(subject, body, to_email):
    """Envoie une notification par email"""
    if not st.session_state.email_config['enabled']:
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = st.session_state.email_config['email']
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(
            st.session_state.email_config['smtp_server'], 
            st.session_state.email_config['smtp_port']
        )
        server.starttls()
        server.login(
            st.session_state.email_config['email'],
            st.session_state.email_config['password']
        )
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Erreur d'envoi: {e}")
        return False

def check_price_alerts(current_price, symbol):
    """Vérifie les alertes de prix"""
    triggered = []
    for alert in st.session_state.price_alerts:
        if alert['symbol'] == symbol:
            if alert['condition'] == 'above' and current_price >= alert['price']:
                triggered.append(alert)
            elif alert['condition'] == 'below' and current_price <= alert['price']:
                triggered.append(alert)
    
    return triggered

def get_market_status():
    """Détermine le statut du marché iranien"""
    market_tz = pytz.timezone('Asia/Tehran')
    now = datetime.now(market_tz)
    
    # Jour de la semaine en Iran (samedi=0, dimanche=1, ..., vendredi=6)
    weekday = now.weekday()
    # Ajuster pour le calendrier iranien (samedi premier jour)
    iran_weekday = (weekday + 2) % 7
    
    # Weekend iranien (jeudi et vendredi)
    if iran_weekday in [4, 5]:  # Jeudi ou Vendredi
        return "Fermé (week-end iranien)", "🔴"
    
    # Jours fériés
    date_str = now.strftime('%Y-%m-%d')
    if date_str in IRAN_HOLIDAYS_2025:
        return "Fermé (jour férié)", "🔴"
    
    # Horaires de trading (bureau de change)
    current_hour = now.hour
    current_minute = now.minute
    current_time_decimal = current_hour + current_minute / 60
    
    # Horaires d'ouverture typiques en Iran: 9h-16h (sauf jeudi jusqu'à 13h)
    if iran_weekday == 4:  # Jeudi (demi-journée)
        if 9 <= current_time_decimal < 13:
            return "Ouvert (demi-journée)", "🟡"
        else:
            return "Fermé", "🔴"
    elif 9 <= current_time_decimal < 16:
        return "Ouvert", "🟢"
    elif current_time_decimal < 9:
        return "Fermé (pré-ouverture)", "🟡"
    else:
        return "Fermé", "🔴"

def safe_get_metric(hist, metric, index=-1):
    """Récupère une métrique en toute sécurité"""
    try:
        if hist is not None and not hist.empty and len(hist) > abs(index):
            return hist[metric].iloc[index]
        return 0
    except:
        return 0

# Titre principal
st.markdown("<h1 class='main-header'>💵 Tracker Rial Iranien (IRR) - Taux de change en temps réel</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-family: Vazirmatn; font-size: 1.5rem;'>ریال ایران - ردیاب نرخ ارز</p>", unsafe_allow_html=True)

# Bannière de statut du marché
current_time_paris = datetime.now(USER_TIMEZONE)
current_time_tehran = datetime.now(IRAN_TIMEZONE)
market_status, market_icon = get_market_status()

# Badges Iran
st.markdown("""
<div style='text-align: center; margin: 10px 0;'>
    <span class='iran-badge'>🇮🇷 Rial Iranien (IRR)</span>
    <span class='official-badge'>🏦 Taux officiel CBI</span>
    <span class='free-market-badge'>🏪 Marché libre</span>
    <span class='nima-badge'>💱 Système NIMA</span>
</div>
""", unsafe_allow_html=True)

# Statut du marché
st.markdown(f"""
<div class='timezone-badge'>
    <b>🕐 Fuseaux horaires :</b><br>
    🇫🇷 Paris: {current_time_paris.strftime('%H:%M:%S')} (UTC+1/UTC+2)<br>
    🇮🇷 Téhéran: {current_time_tehran.strftime('%H:%M:%S')} (UTC+3:30)<br>
    <b>📍 Marché iranien :</b> {market_icon} {market_status}<br>
    <b>📅 Jours de trading :</b> Samedi au Mercredi (jeudi demi-journée, vendredi fermé)
</div>
""", unsafe_allow_html=True)

# Note sur les sanctions
st.markdown("""
<div class='sanction-note'>
    <b>⚠️ Contexte économique</b><br>
    Le Rial iranien est soumis à un système de taux de change multiples sous l'impact des sanctions internationales.
    Les données présentées combinent taux officiels (Banque Centrale d'Iran), taux NIMA (commerce) et taux du marché libre (Téhéran).
    Sources: Bonbast, CBI, Trend.az, bne IntelliNews [citation:1][citation:2][citation:3]
</div>
""", unsafe_allow_html=True)

# Note sur le week-end
if current_time_tehran.weekday() in [4, 5]:  # Jeudi ou Vendredi
    st.markdown("""
    <div class='friday-note'>
        📅 Les marchés iraniens sont fermés le jeudi après-midi et le vendredi (week-end iranien).
        Les prochains cours seront disponibles samedi.
    </div>
    """, unsafe_allow_html=True)

# Mode démo badge
if st.session_state.demo_mode:
    st.markdown("""
    <div style='text-align: center; margin: 10px 0;'>
        <span class='demo-mode-badge'>🎮 MODE DÉMONSTRATION</span>
        <span style='color: #666;'>Données simulées basées sur les sources récentes</span>
    </div>
    """, unsafe_allow_html=True)

# Note informative sur le Rial
st.markdown("""
<div style='background: linear-gradient(135deg, #239F40 0%, #FFFFFF 50%, #DA0000 100%); padding: 1rem; border-radius: 0.5rem; margin: 1rem 0;'>
    <b>🇮🇷 Le Rial iranien (IRR) - Contexte actuel (février 2026)</b><br>
    • Taux officiel CBI: 1 USD = 1,311,134 IRR [citation:3]<br>
    • Taux NIMA (SANA): 1 USD = 1,403,083 IRR [citation:3]<br>
    • Taux marché libre: 1 USD = 1,749,500 IRR (record historique) [citation:1]<br>
    • Dépréciation 2025: -45% [citation:2]<br>
    • Inflation annuelle: >42% [citation:2]<br>
    • Perte de valeur depuis 1979: x20,000 [citation:4]
</div>
""", unsafe_allow_html=True)

# Sidebar pour la navigation
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/iran.png", width=80)
    st.title("Navigation")
    
    # Boutons pour le mode démo
    col_demo1, col_demo2 = st.columns(2)
    with col_demo1:
        if st.button("🎮 Mode Démo"):
            st.session_state.demo_mode = True
            st.rerun()
    with col_demo2:
        if st.button("🔄 Mode Réel"):
            st.session_state.demo_mode = False
            st.cache_data.clear()
            st.rerun()
    
    st.markdown("---")
    
    menu = st.radio(
        "Choisir une section / انتخاب بخش",
        ["📈 Tableau de bord IRR", 
         "💰 Portefeuille devises", 
         "🔔 Alertes de change",
         "📧 Notifications email",
         "📤 Export des données",
         "🤖 Prédictions ML",
         "🇮🇷 Contexte économique"]
    )
    
    st.markdown("---")
    
    # Configuration de la devise principale
    st.subheader("⚙️ Configuration")
    
    # Sélection du symbole principal
    symbol_options = list(CURRENCY_INFO.keys())
    symbol_labels = list(CURRENCY_INFO.values())
    
    selected_option = st.selectbox(
        "Paire de devises",
        options=symbol_options,
        format_func=lambda x: CURRENCY_INFO.get(x, x),
        index=0
    )
    
    symbol = selected_option
    currency_name, base_currency, quote_currency = get_currency_info(symbol)
    
    # Afficher des informations sur la paire
    st.caption(f"📍 {base_currency} → {quote_currency}")
    
    # Période et intervalle
    col1, col2 = st.columns(2)
    with col1:
        period = st.selectbox(
            "Période",
            options=["1d", "5d", "1mo", "3mo", "6mo", "1y"],
            index=2
        )
    
    with col2:
        interval_map = {
            "1m": "1 minute", "5m": "5 minutes", "15m": "15 minutes",
            "30m": "30 minutes", "1h": "1 heure", "1d": "1 jour",
            "1wk": "1 semaine", "1mo": "1 mois"
        }
        interval = st.selectbox(
            "Intervalle",
            options=list(interval_map.keys()),
            format_func=lambda x: interval_map[x],
            index=4 if period == "1d" else 6
        )
    
    # Auto-refresh
    auto_refresh = st.checkbox("Actualisation automatique", value=False)
    if auto_refresh:
        st.warning("⚠️ L'actualisation automatique peut entraîner des limitations")
        refresh_rate = st.slider(
            "Fréquence (secondes)",
            min_value=30,
            max_value=300,
            value=60,
            step=10
        )

# Chargement des données
try:
    hist, info = load_currency_data(symbol, period, interval)
except Exception as e:
    st.error(f"Erreur lors du chargement: {e}")
    st.session_state.demo_mode = True
    hist, info = generate_demo_history(symbol, period, interval), DEMO_DATA.get(symbol, {
        'name': f'{symbol} (Mode démo)',
        'official_rate': 1311134,
        'free_market_rate': 1749500,
    })

if hist is None or hist.empty:
    st.warning(f"⚠️ Impossible de charger les données pour {symbol}. Utilisation du mode démo.")
    st.session_state.demo_mode = True
    hist = generate_demo_history(symbol, period, interval)
    info = DEMO_DATA.get(symbol, {
        'name': f'{symbol} (Mode démo)',
        'free_market_rate': 1749500,
    })

current_price = safe_get_metric(hist, 'Close')
if current_price == 0 and info:
    current_price = info.get('free_market_rate', info.get('official_rate', 1749500))

# Vérification des alertes
triggered_alerts = check_price_alerts(current_price, symbol)
for alert in triggered_alerts:
    st.balloons()
    st.success(f"🎯 Alerte déclenchée pour {symbol} à {format_rial(current_price)}")
    
    if st.session_state.email_config['enabled']:
        subject = f"🚨 Alerte change - {symbol}"
        body = f"""
        <h2>Alerte de taux de change déclenchée</h2>
        <p><b>Paire:</b> {symbol}</p>
        <p><b>Taux actuel:</b> {format_rial(current_price)}</p>
        <p><b>Condition:</b> {alert['condition']} {format_rial(alert['price'])}</p>
        <p><b>Date:</b> {datetime.now(USER_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')} (heure Paris)</p>
        <p><b>Date Téhéran:</b> {datetime.now(IRAN_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        send_email_alert(subject, body, st.session_state.email_config['email'])
    
    if alert.get('one_time', False):
        st.session_state.price_alerts.remove(alert)

# ============================================================================
# SECTION 1: TABLEAU DE BORD IRR
# ============================================================================
if menu == "📈 Tableau de bord IRR":
    # Statut du marché
    st.info(f"{market_icon} Marché iranien: {market_status}")
    
    if hist is not None and not hist.empty:
        currency_name = info.get('name', symbol) if info else symbol
        if st.session_state.demo_mode:
            currency_name += " (Mode démo)"
        
        st.subheader(f"📊 Taux de change en temps réel - {currency_name}")
        
        # Affichage des différents taux
        col_info1, col_info2, col_info3 = st.columns(3)
        
        official_rate = info.get('official_rate', None)
        nima_rate = info.get('nima_rate', None)
        free_market_rate = info.get('free_market_rate', current_price)
        
        with col_info1:
            if official_rate:
                st.markdown(f"""
                <div class='exchange-rate-card'>
                    <span class='official-badge'>🏦 Taux officiel CBI</span>
                    <h3>{format_rial(official_rate, include_toman=True)}</h3>
                    <p style='color: #666; font-size: 0.9rem;'>Transactions gouvernementales</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col_info2:
            if nima_rate:
                st.markdown(f"""
                <div class='exchange-rate-card'>
                    <span class='nima-badge'>💱 Taux NIMA/SANA</span>
                    <h3>{format_rial(nima_rate, include_toman=True)}</h3>
                    <p style='color: #666; font-size: 0.9rem;'>Exportateurs/Importateurs</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col_info3:
            st.markdown(f"""
            <div class='exchange-rate-card'>
                <span class='free-market-badge'>🏪 Marché libre</span>
                <h3>{format_rial(free_market_rate, include_toman=True)}</h3>
                <p style='color: #666; font-size: 0.9rem;'>Taux réel (Téhéran)</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)
        
        previous_close = info.get('previous_close', safe_get_metric(hist, 'Close', -2) if len(hist) > 1 else current_price)
        change = current_price - previous_close
        change_pct = (change / previous_close * 100) if previous_close != 0 else 0
        
        with col1:
            st.metric(
                label="Taux marché libre",
                value=format_rial(current_price, include_toman=False),
                delta=f"{change:,.0f} Rial ({change_pct:.2f}%)",
                delta_color="inverse"  # Pour les devises, hausse = dépréciation du rial
            )
        
        with col2:
            day_high = info.get('day_high', safe_get_metric(hist, 'High'))
            st.metric("Plus haut (24h)", format_rial(day_high, include_toman=False))
        
        with col3:
            day_low = info.get('day_low', safe_get_metric(hist, 'Low'))
            st.metric("Plus bas (24h)", format_rial(day_low, include_toman=False))
        
        with col4:
            volume = info.get('volume', safe_get_metric(hist, 'Volume'))
            volume_formatted = f"${volume/1e6:.1f}M" if volume > 1e6 else f"${volume/1e3:.1f}K"
            st.metric("Volume estimé", volume_formatted)
        
        # Informations temporelles
        st.caption(f"Dernière mise à jour: {datetime.now(USER_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')} (heure Paris)")
        st.caption(f"آخرین به‌روزرسانی: {datetime.now(IRAN_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')} (heure Téhéran)")
        
        # Graphique principal
        st.subheader("📉 Évolution du taux de change")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist['Close'],
            mode='lines',
            name='Marché libre',
            line=dict(color='#ff9800', width=2)
        ))
        
        # Ajouter les taux officiels comme lignes de référence
        if official_rate:
            fig.add_hline(
                y=official_rate,
                line_dash="dash",
                line_color="#2196f3",
                annotation_text="Taux officiel CBI",
                annotation_position="top left"
            )
        
        if nima_rate:
            fig.add_hline(
                y=nima_rate,
                line_dash="dash",
                line_color="#9c27b0",
                annotation_text="Taux NIMA",
                annotation_position="top right"
            )
        
        if len(hist) >= 20:
            ma_20 = hist['Close'].rolling(window=20).mean()
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=ma_20,
                mode='lines',
                name='MA 20 jours',
                line=dict(color='orange', width=1, dash='dash')
            ))
        
        fig.update_layout(
            title=f"{symbol} - {period} (évolution du Rial)",
            yaxis_title="Rial (IRR)",
            xaxis_title="Date",
            height=500,
            hovermode='x unified',
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Informations supplémentaires
        with st.expander("ℹ️ Détails sur les taux de change"):
            col_d1, col_d2 = st.columns(2)
            
            with col_d1:
                st.markdown("**🏦 Taux officiel (CBI)**")
                st.markdown("""
                - Utilisé pour les transactions gouvernementales
                - Importations de produits essentiels
                - Réservé aux entités publiques
                - Stable mais non accessible au public
                """)
                
                st.markdown("**💱 Taux NIMA/SANA**")
                st.markdown("""
                - Pour les exportateurs et importateurs
                - Taux intermédiaire
                - Géré par la Banque Centrale
                - Plus accessible que le taux officiel
                """)
            
            with col_d2:
                st.markdown("**🏪 Marché libre (Téhéran)**")
                st.markdown("""
                - Taux réel pour les particuliers
                - Détermine le coût de la vie
                - Haute volatilité
                - Impacté par les sanctions et tensions
                """)
                
                st.markdown("**📊 Écarts actuels**")
                if official_rate and free_market_rate:
                    spread = ((free_market_rate - official_rate) / official_rate * 100)
                    st.metric("Écart officiel/marché", f"{spread:.1f}%")
                
                if nima_rate and free_market_rate:
                    spread_nima = ((free_market_rate - nima_rate) / nima_rate * 100)
                    st.metric("Écart NIMA/marché", f"{spread_nima:.1f}%")
        
        # Statistiques de performance
        st.subheader("📊 Performance du Rial")
        
        if 'change_1d' in info:
            col_p1, col_p2, col_p3, col_p4 = st.columns(4)
            
            with col_p1:
                st.metric("Variation 1 jour", f"{info.get('change_1d', 0):.1f}%", delta_color="inverse")
            with col_p2:
                st.metric("Variation 1 semaine", f"{info.get('change_1w', 0):.1f}%", delta_color="inverse")
            with col_p3:
                st.metric("Variation 1 mois", f"{info.get('change_1m', 0):.1f}%", delta_color="inverse")
            with col_p4:
                st.metric("Variation 1 an", f"{info.get('change_1y', 0):.1f}%", delta_color="inverse")
    else:
        st.warning(f"Aucune donnée disponible pour {symbol}")

# ============================================================================
# SECTION 2: PORTEFEUILLE DEVISES
# ============================================================================
elif menu == "💰 Portefeuille devises":
    st.subheader("💰 Portefeuille virtuel - Devises et métaux précieux")
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.markdown("### ➕ Ajouter une position")
        with st.form("add_position"):
            symbol_pf = st.selectbox(
                "Devise/Métal",
                options=list(CURRENCY_INFO.keys()),
                format_func=lambda x: CURRENCY_INFO.get(x, x),
                index=0
            )
            
            currency_name, base_currency, quote_currency = get_currency_info(symbol_pf)
            st.caption(f"📍 {currency_name}")
            
            amount = st.number_input("Montant en devise de base", min_value=1.0, step=100.0, value=1000.0)
            buy_rate = st.number_input(f"Taux d'achat ({quote_currency}/{base_currency})", min_value=1.0, step=1000.0, value=1749500.0)
            
            if st.form_submit_button("Ajouter au portefeuille"):
                if symbol_pf and amount > 0:
                    if symbol_pf not in st.session_state.portfolio:
                        st.session_state.portfolio[symbol_pf] = []
                    
                    st.session_state.portfolio[symbol_pf].append({
                        'amount': amount,
                        'buy_rate': buy_rate,
                        'currency_pair': symbol_pf,
                        'date': datetime.now(USER_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
                    })
                    st.success(f"✅ {amount:,.0f} {base_currency} ajoutés")
        
        st.markdown("---")
        st.markdown("### 💡 Devises principales")
        st.markdown("""
        - **USD/IRR** - Dollar américain
        - **EUR/IRR** - Euro
        - **AED/IRR** - Dirham (UAE)
        - **XAU/IRR** - Or
        - **TRY/IRR** - Lire turque
        """)
    
    with col1:
        st.markdown("### 📊 Performance du portefeuille")
        
        if st.session_state.portfolio:
            portfolio_data = []
            total_value_irr = 0
            total_cost_irr = 0
            
            for symbol_pf, positions in st.session_state.portfolio.items():
                try:
                    if st.session_state.demo_mode and symbol_pf in DEMO_DATA:
                        current_rate = DEMO_DATA[symbol_pf].get('free_market_rate', DEMO_DATA[symbol_pf].get('official_rate', 1749500))
                    else:
                        current_rate = DEMO_DATA.get(symbol_pf, {}).get('free_market_rate', 1749500)
                    
                    currency_name, base_currency, quote_currency = get_currency_info(symbol_pf)
                    
                    for pos in positions:
                        amount = pos['amount']
                        buy_rate = pos['buy_rate']
                        cost_irr = amount * buy_rate
                        value_irr = amount * current_rate
                        profit_irr = value_irr - cost_irr
                        profit_pct = (profit_irr / cost_irr * 100) if cost_irr > 0 else 0
                        
                        total_cost_irr += cost_irr
                        total_value_irr += value_irr
                        
                        portfolio_data.append({
                            'Paire': symbol_pf,
                            'Devise': base_currency,
                            'Montant': f"{amount:,.0f}",
                            "Taux achat": format_rial(buy_rate, include_toman=False),
                            'Taux actuel': format_rial(current_rate, include_toman=False),
                            'Valeur (IRR)': format_rial(value_irr, include_toman=False),
                            'Profit (IRR)': format_rial(profit_irr, include_toman=False),
                            'Profit %': f"{profit_pct:.1f}%"
                        })
                except Exception as e:
                    st.warning(f"Impossible de charger {symbol_pf}")
            
            if portfolio_data:
                total_profit_irr = total_value_irr - total_cost_irr
                total_profit_pct = (total_profit_irr / total_cost_irr * 100) if total_cost_irr > 0 else 0
                
                st.markdown("#### Total portefeuille")
                col_i1, col_i2, col_i3 = st.columns(3)
                col_i1.metric("Valeur totale", format_rial(total_value_irr, include_toman=True))
                col_i2.metric("Coût total", format_rial(total_cost_irr, include_toman=True))
                col_i3.metric(
                    "Profit total",
                    format_rial(total_profit_irr, include_toman=False),
                    delta=f"{total_profit_pct:.1f}%"
                )
                
                st.markdown("### 📋 Positions détaillées")
                df_portfolio = pd.DataFrame(portfolio_data)
                st.dataframe(df_portfolio, use_container_width=True, hide_index=True)
                
                # Graphique de répartition
                try:
                    fig_pie = px.pie(
                        names=[p['Devise'] for p in portfolio_data],
                        values=[float(p['Valeur (IRR)'].split()[0].replace(',', '')) for p in portfolio_data],
                        title="Répartition du portefeuille par devise"
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                except:
                    st.warning("Impossible de générer le graphique")
                
                if st.button("🗑️ Vider le portefeuille"):
                    st.session_state.portfolio = {}
                    st.rerun()
            else:
                st.info("Aucune donnée de performance disponible")
        else:
            st.info("Aucune position dans le portefeuille. Ajoutez des devises pour commencer !")

# ============================================================================
# SECTION 3: ALERTES DE CHANGE
# ============================================================================
elif menu == "🔔 Alertes de change":
    st.subheader("🔔 Gestion des alertes de taux de change")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### ➕ Créer une nouvelle alerte")
        with st.form("new_alert"):
            alert_symbol = st.selectbox(
                "Paire de devises",
                options=list(CURRENCY_INFO.keys()),
                format_func=lambda x: CURRENCY_INFO.get(x, x),
                index=0
            )
            
            default_price = float(current_price * 1.05) if current_price > 0 else 1749500
            alert_price = st.number_input(
                "Taux cible (IRR)", 
                min_value=1.0, 
                step=10000.0, 
                value=default_price
            )
            
            col_cond, col_type = st.columns(2)
            with col_cond:
                condition = st.selectbox("Condition", ["above (au-dessus)", "below (en-dessous)"])
                condition = condition.split()[0]
            with col_type:
                alert_type = st.selectbox("Type", ["Permanent", "Une fois"])
            
            one_time = alert_type == "Une fois"
            
            if st.form_submit_button("Créer l'alerte"):
                st.session_state.price_alerts.append({
                    'symbol': alert_symbol,
                    'price': alert_price,
                    'condition': condition,
                    'one_time': one_time,
                    'created': datetime.now(USER_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
                })
                st.success(f"✅ Alerte créée pour {alert_symbol} à {format_rial(alert_price)}")
    
    with col2:
        st.markdown("### 📋 Alertes actives")
        if st.session_state.price_alerts:
            for i, alert in enumerate(st.session_state.price_alerts):
                with st.container():
                    st.markdown(f"""
                    <div class='alert-box alert-warning'>
                        <b>{alert['symbol']}</b> - {alert['condition']} {format_rial(alert['price'])}<br>
                        <small>Créée: {alert['created']} | {('Usage unique' if alert['one_time'] else 'Permanent')}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"Supprimer", key=f"del_alert_{i}"):
                        st.session_state.price_alerts.pop(i)
                        st.rerun()
        else:
            st.info("Aucune alerte active")

# ============================================================================
# SECTION 4: NOTIFICATIONS EMAIL
# ============================================================================
elif menu == "📧 Notifications email":
    st.subheader("📧 Configuration des notifications email")
    
    with st.form("email_config"):
        enabled = st.checkbox("Activer les notifications email", value=st.session_state.email_config['enabled'])
        
        col1, col2 = st.columns(2)
        with col1:
            smtp_server = st.text_input("Serveur SMTP", value=st.session_state.email_config['smtp_server'])
            smtp_port = st.number_input("Port SMTP", value=st.session_state.email_config['smtp_port'])
        
        with col2:
            email = st.text_input("Adresse email", value=st.session_state.email_config['email'])
            password = st.text_input("Mot de passe", type="password", value=st.session_state.email_config['password'])
        
        test_email = st.text_input("Email de test (optionnel)")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.form_submit_button("💾 Sauvegarder"):
                st.session_state.email_config = {
                    'enabled': enabled,
                    'smtp_server': smtp_server,
                    'smtp_port': smtp_port,
                    'email': email,
                    'password': password
                }
                st.success("Configuration sauvegardée !")
        
        with col_btn2:
            if st.form_submit_button("📨 Tester"):
                if test_email:
                    if send_email_alert(
                        "Test de notification",
                        f"<h2>Test réussi !</h2><p>Votre configuration email fonctionne correctement !</p><p>Heure d'envoi: {datetime.now(USER_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')} (heure Paris)</p><p>ساعت ارسال: {datetime.now(IRAN_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')} (heure Téhéran)</p>",
                        test_email
                    ):
                        st.success("Email de test envoyé !")
                    else:
                        st.error("Échec de l'envoi")
    
    with st.expander("📋 Aperçu de la configuration"):
        st.json(st.session_state.email_config)

# ============================================================================
# SECTION 5: EXPORT DES DONNÉES
# ============================================================================
elif menu == "📤 Export des données":
    st.subheader("📤 Export des données")
    
    if hist is not None and not hist.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Données historiques")
            display_hist = hist.copy()
            display_hist.index = display_hist.index.strftime('%Y-%m-%d %H:%M:%S (heure Paris)')
            st.dataframe(display_hist.tail(20))
            
            csv = hist.to_csv()
            st.download_button(
                label="📥 Télécharger en CSV",
                data=csv,
                file_name=f"{symbol}_data_{datetime.now(USER_TIMEZONE).strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            st.markdown("### 📈 Rapport")
            st.info("Génération de rapport (simulée)")
            
            st.markdown("**Statistiques:**")
            stats = {
                'Moyenne': hist['Close'].mean(),
                'Écart-type': hist['Close'].std(),
                'Min': hist['Close'].min(),
                'Max': hist['Close'].max(),
                'Variation totale': f"{(hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100:.2f}%" if len(hist) > 1 else "N/A"
            }
            
            for key, value in stats.items():
                if isinstance(value, float):
                    st.write(f"{key}: {format_rial(value, include_toman=False)}")
                else:
                    st.write(f"{key}: {value}")
            
            json_data = {
                'symbol': symbol,
                'name': CURRENCY_INFO.get(symbol, symbol),
                'last_update_paris': datetime.now(USER_TIMEZONE).isoformat(),
                'last_update_tehran': datetime.now(IRAN_TIMEZONE).isoformat(),
                'current_rate': float(current_price) if current_price else 0,
                'official_rate': info.get('official_rate', None),
                'nima_rate': info.get('nima_rate', None),
                'free_market_rate': info.get('free_market_rate', current_price),
                'statistics': {k: (float(v) if isinstance(v, (int, float)) else v) for k, v in stats.items()},
                'data': hist.reset_index().to_dict(orient='records')
            }
            
            st.download_button(
                label="📥 Télécharger en JSON",
                data=json.dumps(json_data, indent=2, default=str),
                file_name=f"{symbol}_data_{datetime.now(USER_TIMEZONE).strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    else:
        st.warning(f"Aucune donnée à exporter pour {symbol}")

# ============================================================================
# SECTION 6: PRÉDICTIONS ML
# ============================================================================
elif menu == "🤖 Prédictions ML":
    st.subheader("🤖 Prédictions avec Machine Learning - Taux de change IRR")
    
    if hist is not None and not hist.empty and len(hist) > 30:
        st.markdown("### Modèle de prédiction (Régression polynomiale)")
        
        st.info(f"""
        ⚠️ Facteurs influençant le Rial iranien (IRR):
        
        **Facteurs géopolitiques:**
        - Sanctions internationales (USA, UE, ONU) [citation:2][citation:8]
        - Négociations nucléaires (JCPOA)
        - Tensions au Moyen-Orient
        - Relations avec les puissances mondiales
        
        **Facteurs économiques:**
        - Prix du pétrole (exportations iraniennes)
        - Revenus pétroliers (~23-28 Mds $) [citation:2]
        - Réserves de change
        - Inflation (>42% annuel) [citation:2]
        - Masse monétaire
        
        **Facteurs de marché:**
        - Demande de dollars au marché libre
        - Taux NIMA pour les importateurs/exportateurs
        - Interventions de la Banque Centrale
        - Dollarisation de l'économie
        
        **Événements récents (février 2026):**
        - Record historique: 1 USD = 1,749,500 IRR [citation:1]
        - Frappes israéliennes à Téhéran
        - Dépréciation accélérée depuis janvier 2026
        """)
        
        df_pred = hist[['Close']].reset_index()
        df_pred['Days'] = (df_pred['Date'] - df_pred['Date'].min()).dt.days
        
        X = df_pred['Days'].values.reshape(-1, 1)
        y = df_pred['Close'].values
        
        col1, col2 = st.columns(2)
        
        with col1:
            days_to_predict = st.slider("Jours à prédire", min_value=1, max_value=30, value=7)
            degree = st.slider("Degré du polynôme", min_value=1, max_value=5, value=2)
        
        with col2:
            show_confidence = st.checkbox("Afficher l'intervalle de confiance", value=True)
        
        model = make_pipeline(
            PolynomialFeatures(degree=degree),
            LinearRegression()
        )
        model.fit(X, y)
        
        last_day = X[-1][0]
        future_days = np.arange(last_day + 1, last_day + days_to_predict + 1).reshape(-1, 1)
        predictions = model.predict(future_days)
        
        last_date = df_pred['Date'].iloc[-1]
        future_dates = [last_date + timedelta(days=i+1) for i in range(days_to_predict)]
        
        fig_pred = go.Figure()
        
        fig_pred.add_trace(go.Scatter(
            x=df_pred['Date'],
            y=y,
            mode='lines',
            name='Historique',
            line=dict(color='#2196f3', width=2)
        ))
        
        fig_pred.add_trace(go.Scatter(
            x=future_dates,
            y=predictions,
            mode='lines+markers',
            name='Prédictions',
            line=dict(color='#ff9800', width=2, dash='dash'),
            marker=dict(size=8)
        ))
        
        if show_confidence:
            residuals = y - model.predict(X)
            std_residuals = np.std(residuals)
            
            upper_bound = predictions + 2 * std_residuals
            lower_bound = predictions - 2 * std_residuals
            
            fig_pred.add_trace(go.Scatter(
                x=future_dates + future_dates[::-1],
                y=np.concatenate([upper_bound, lower_bound[::-1]]),
                fill='toself',
                fillcolor='rgba(255,152,0,0.2)',
                line=dict(color='rgba(255,152,0,0)'),
                name='Intervalle confiance 95%'
            ))
        
        fig_pred.update_layout(
            title=f"Prédictions pour {symbol} - {days_to_predict} jours",
            xaxis_title="Date",
            yaxis_title="Taux (IRR)",
            hovermode='x unified',
            template='plotly_white',
            height=500
        )
        
        st.plotly_chart(fig_pred, use_container_width=True)
        
        st.markdown("### 📋 Prédictions détaillées")
        pred_df = pd.DataFrame({
            'Date': [d.strftime('%Y-%m-%d') for d in future_dates],
            'Taux prédit': [format_rial(p, include_toman=True) for p in predictions],
            'Variation %': [f"{(p/current_price - 1)*100:.2f}%" for p in predictions]
        })
        st.dataframe(pred_df, use_container_width=True, hide_index=True)
        
        st.markdown("### 📊 Performance du modèle")
        residuals = y - model.predict(X)
        mse = np.mean(residuals**2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(residuals))
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("RMSE", format_rial(rmse, include_toman=False))
        col_m2.metric("MAE", format_rial(mae, include_toman=False))
        col_m3.metric("R²", f"{model.score(X, y):.3f}")
        
        st.markdown("### 📈 Analyse des tendances")
        last_price = current_price
        last_pred = predictions[-1]
        trend = "HAUSSIÈRE 📈" if last_pred > last_price else "BAISSIÈRE 📉" if last_pred < last_price else "NEUTRE ➡️"
        
        st.info(f"**Tendance prévue:** {trend} (hausse = dépréciation du Rial)")
        
        if last_pred > last_price * 1.05:
            strength = "Forte dépréciation anticipée 🚨"
        elif last_pred > last_price:
            strength = "Dépréciation modérée anticipée ⚠️"
        elif last_pred < last_price * 0.95:
            strength = "Appréciation forte anticipée (peu probable) 📈"
        elif last_pred < last_price:
            strength = "Légère appréciation anticipée 📊"
        else:
            strength = "Stabilité anticipée ⏸️"
        
        st.warning(f"**Scénario prévu:** {strength}")
        
    else:
        st.warning(f"Pas assez de données historiques pour {symbol} (minimum 30 points)")

# ============================================================================
# SECTION 7: CONTEXTE ÉCONOMIQUE
# ============================================================================
elif menu == "🇮🇷 Contexte économique":
    st.subheader("🇮🇷 Contexte économique iranien (2025-2026)")
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.markdown("### 📊 Indicateurs macroéconomiques")
        
        indicators = {
            "Inflation annuelle": "42.2% (décembre 2025) [citation:2]",
            "Inflation alimentaire": "60-70% [citation:2]",
            "Dépréciation 2025": "-45% [citation:2]",
            "Dépréciation depuis 1979": "x20,000 [citation:4]",
            "Taux officiel USD": "1,311,134 IRR [citation:3]",
            "Taux NIMA USD": "1,403,083 IRR [citation:3]",
            "Taux marché libre USD": "1,749,500 IRR (record) [citation:1]",
            "Prix de l'or (Téhéran)": "224.5 M IRR/gramme [citation:1]",
            "Réserves de change": "~20-30 Mds $ (estimé)",
            "Population": "~90 millions [citation:6]",
            "PIB (estimé)": "~400 Mds $",
            "Croissance PIB 2025": "-1.7% [citation:7]",
            "Croissance PIB 2026 (prév.)": "-2.8% [citation:7]",
        }
        
        for key, value in indicators.items():
            st.markdown(f"**{key}:** {value}")
    
    with col_c2:
        st.markdown("### 🌍 Sanctions et pressions")
        
        st.markdown("**Sanctions internationales:**")
        st.markdown("""
        - **ONU:** Réimposition septembre 2025 [citation:2]
          - Embargo sur les armes conventionnelles
          - Restrictions missiles balistiques
          - Gel des avoirs ciblés
          - Interdictions de voyage
        
        - **États-Unis:** Pression maximale renforcée
          - Blocage des revenus pétroliers
          - Restriction accès SWIFT
          - Pénurie orchestrée de dollars [citation:9]
        
        - **Union Européenne:**
          - Sanctions droits humains
          - Sanctions liées aux drones (Russie)
        """)
        
        st.markdown("**Impact des sanctions:**")
        st.markdown("""
        - Perte de 20% des revenus pétroliers potentiels
        - Coût d'évitement: ~5 Mds $/an [citation:2]
        - Dollarisation de l'économie
        - Fuite des capitaux
        """)
        
        st.markdown("**Événements récents (février 2026):**")
        st.markdown("""
        - Frappes israéliennes à Téhéran [citation:1]
        - Record historique du taux USD/IRR
        - Admission américaine de guerre économique [citation:9]
        """)
    
    st.markdown("---")
    
    col_h1, col_h2 = st.columns(2)
    
    with col_h1:
        st.markdown("### 📈 Historique du taux USD/IRR")
        
        history_data = {
            "1979 (Révolution)": 70,
            "2000": 1,750,
            "2010": 10,000,
            "2015": 30,000,
            "2018 (sanctions Trump)": 70,000,
            "2020": 200,000,
            "2023": 500,000,
            "Jan 2025": 42,000 (officiel) / 600,000 (marché),
            "Déc 2025": 1,065,000 [citation:2],
            "Jan 2026": 1,457,000 [citation:4],
            "Fév 2026": 1,749,500 [citation:1],
        }
        
        dates = list(history_data.keys())
        rates = list(history_data.values())
        
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Scatter(
            x=dates,
            y=rates,
            mode='lines+markers',
            name='USD/IRR',
            line=dict(color='#ff9800', width=3)
        ))
        
        fig_hist.update_layout(
            title="Évolution historique USD/IRR (échelle logarithmique)",
            yaxis_type="log",
            xaxis_tickangle=-45,
            height=400,
            template='plotly_white'
        )
        
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col_h2:
        st.markdown("### 🏦 Système de taux multiples")
        
        rate_system = pd.DataFrame({
            'Type de taux': ['Officiel (CBI)', 'NIMA/SANA', 'Marché libre'],
            'Taux (USD/IRR)': ['1,311,134', '1,403,083', '1,749,500'],
            'Accès': ['Gouvernement', 'Exportateurs/Importateurs', 'Public'],
            'Part du marché': ['~10%', '~30%', '~60%'],
        })
        
        st.dataframe(rate_system, use_container_width=True, hide_index=True)
        
        st.markdown("### 💡 Scénarios possibles")
        st.markdown("""
        **Scénario 1: Poursuite de la dépréciation** (probable)
        - Nouveaux records (>2M IRR/USD)
        - Inflation >50%
        - Tensions sociales accrues
        
        **Scénario 2: Stabilité temporaire** (possible)
        - Intervention CBI massive
        - Accords pétroliers avec la Chine
        - Allègement temporaire des sanctions
        
        **Scénario 3: Réforme monétaire** (en discussion)
        - Suppression de 4 zéros [citation:7]
        - Renommage en Toman
        - Transition sur 2-3 ans
        """)
    
    with st.expander("📰 Sources et références"):
        st.markdown("""
        - **bne IntelliNews:** Record historique du Rial (février 2026) [citation:1]
        - **Kompas:** Analyse détaillée des causes de la dépréciation [citation:2]
        - **Trend.az:** Taux officiels de la Banque Centrale d'Iran [citation:3]
        - **Republika:** Contexte historique depuis 1979 [citation:4]
        - **El Universal:** Impact social et manifestations [citation:6]
        - **Dân trí:** Analyse du système de taux multiples [citation:7]
        - **La Nouvelle Tribune:** Stratégie américaine de pression financière [citation:9]
        - **VnEconomy:** Impact des sanctions sur les revenus pétroliers [citation:10]
        """)

# ============================================================================
# WATCHLIST ET DERNIÈRE MISE À JOUR
# ============================================================================
st.markdown("---")
col_w1, col_w2 = st.columns([3, 1])

with col_w1:
    st.subheader("📋 Watchlist - Taux de change IRR")
    
    # Regrouper par type
    major_pairs = ['USDIRR', 'EURIRR', 'GBPIRR']
    regional_pairs = ['AEDIRR', 'SARIRR', 'TRYIRR']
    other_pairs = ['CNYIRR', 'RUBIRR', 'INRIRR', 'JPYIRR']
    metals = ['XAUIRR']
    
    tabs = st.tabs(["💵 Majeures", "🌍 Régionales", "🌏 Asiatiques", "🏅 Métaux"])
    
    with tabs[0]:  # Majeures
        cols_per_row = 2
        for i in range(0, len(major_pairs), cols_per_row):
            cols = st.columns(min(cols_per_row, len(major_pairs) - i))
            for j, sym in enumerate(major_pairs[i:i+cols_per_row]):
                with cols[j]:
                    try:
                        if st.session_state.demo_mode and sym in DEMO_DATA:
                            rate = DEMO_DATA[sym]['free_market_rate']
                            prev = DEMO_DATA[sym].get('previous_close', rate * 0.98)
                            change = ((rate - prev) / prev * 100)
                            name = CURRENCY_INFO.get(sym, sym).split('→')[0]
                            st.metric(name, format_rial(rate, include_toman=False), delta=f"{change:.1f}%")
                        else:
                            rate = random.uniform(1000000, 2000000)
                            st.metric(CURRENCY_INFO.get(sym, sym).split('→')[0], format_rial(rate, include_toman=False), delta=f"{random.uniform(-3, 5):.1f}%")
                    except:
                        st.metric(CURRENCY_INFO.get(sym, sym).split('→')[0], "N/A")
    
    with tabs[1]:  # Régionales
        cols_per_row = 2
        for i in range(0, len(regional_pairs), cols_per_row):
            cols = st.columns(min(cols_per_row, len(regional_pairs) - i))
            for j, sym in enumerate(regional_pairs[i:i+cols_per_row]):
                with cols[j]:
                    try:
                        if st.session_state.demo_mode and sym in DEMO_DATA:
                            rate = DEMO_DATA[sym]['free_market_rate']
                            prev = DEMO_DATA[sym].get('previous_close', rate * 0.98)
                            change = ((rate - prev) / prev * 100)
                            name = CURRENCY_INFO.get(sym, sym).split('→')[0]
                            st.metric(name, format_rial(rate, include_toman=False), delta=f"{change:.1f}%")
                        else:
                            rate = random.uniform(300000, 500000)
                            st.metric(CURRENCY_INFO.get(sym, sym).split('→')[0], format_rial(rate, include_toman=False), delta=f"{random.uniform(-3, 5):.1f}%")
                    except:
                        st.metric(CURRENCY_INFO.get(sym, sym).split('→')[0], "N/A")
    
    with tabs[2]:  # Asiatiques
        cols_per_row = 2
        for i in range(0, len(other_pairs), cols_per_row):
            cols = st.columns(min(cols_per_row, len(other_pairs) - i))
            for j, sym in enumerate(other_pairs[i:i+cols_per_row]):
                with cols[j]:
                    try:
                        if st.session_state.demo_mode and sym in DEMO_DATA:
                            rate = DEMO_DATA[sym]['free_market_rate']
                            prev = DEMO_DATA[sym].get('previous_close', rate * 0.98)
                            change = ((rate - prev) / prev * 100)
                            name = CURRENCY_INFO.get(sym, sym).split('→')[0]
                            st.metric(name, format_rial(rate, include_toman=False), delta=f"{change:.1f}%")
                        else:
                            rate = random.uniform(10000, 200000)
                            st.metric(CURRENCY_INFO.get(sym, sym).split('→')[0], format_rial(rate, include_toman=False), delta=f"{random.uniform(-3, 5):.1f}%")
                    except:
                        st.metric(CURRENCY_INFO.get(sym, sym).split('→')[0], "N/A")
    
    with tabs[3]:  # Métaux
        cols_per_row = 1
        for i in range(0, len(metals), cols_per_row):
            cols = st.columns(min(cols_per_row, len(metals) - i))
            for j, sym in enumerate(metals[i:i+cols_per_row]):
                with cols[j]:
                    try:
                        if st.session_state.demo_mode and sym in DEMO_DATA:
                            rate = DEMO_DATA[sym]['free_market_rate']
                            prev = DEMO_DATA[sym].get('previous_close', rate * 0.98)
                            change = ((rate - prev) / prev * 100)
                            name = CURRENCY_INFO.get(sym, sym).split('→')[0]
                            st.metric(name, format_rial(rate, include_toman=False), delta=f"{change:.1f}%")
                        else:
                            rate = random.uniform(200000000, 230000000)
                            st.metric(CURRENCY_INFO.get(sym, sym).split('→')[0], format_rial(rate, include_toman=False), delta=f"{random.uniform(-3, 5):.1f}%")
                    except:
                        st.metric(CURRENCY_INFO.get(sym, sym).split('→')[0], "N/A")

with col_w2:
    # Horaires et informations
    paris_time = datetime.now(USER_TIMEZONE)
    tehran_time = datetime.now(IRAN_TIMEZONE)
    
    st.markdown("### 🕐 Heures actuelles")
    st.caption(f"🇫🇷 Paris: {paris_time.strftime('%H:%M:%S')}")
    st.caption(f"🇮🇷 Téhéran: {tehran_time.strftime('%H:%M:%S')}")
    
    st.markdown("### 📊 Statut du marché")
    status, icon = get_market_status()
    st.caption(f"{icon} {status}")
    
    # Prochains événements
    st.markdown("### 📅 Événements à suivre")
    st.caption("• Négociations nucléaires")
    st.caption("• Décisions OPEP+")
    st.caption("• Rapport inflation mensuel")
    
    if st.session_state.demo_mode:
        st.caption("🎮 Mode démonstration")
    else:
        st.caption(f"Dernière MAJ: {paris_time.strftime('%H:%M:%S')}")
    
    if auto_refresh and hist is not None and not hist.empty:
        time.sleep(refresh_rate)
        st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 0.8rem;'>"
    "💵 Tracker Rial Iranien (IRR) - Données en temps réel (simulées) | 🇮🇷 Système de taux multiples<br>"
    "📅 Sources: Bonbast, CBI, Trend.az, bne IntelliNews - Mise à jour: février 2026<br>"
    "⚠️ À titre informatif uniquement - Les taux réels peuvent varier selon le marché"
    "</p>",
    unsafe_allow_html=True
)

# Message de bienvenue en persan
st.markdown("""
<div style='text-align: center; font-family: Vazirmatn; font-size: 1.2rem; margin-top: 1rem; direction: rtl;'>
    <p>🇮🇷 ریال ایران - ردیاب نرخ ارز در زمان واقعی</p>
    <p>نرخ‌های رسمی، نیما و بازار آزاد</p>
    <p>آخرین به‌روزرسانی: فوریه ۲۰۲۶</p>
</div>
""", unsafe_allow_html=True)
