import os
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parents[1]
load_dotenv(APP_DIR / ".env")
DATA_DIR = Path(os.getenv("ATOMO_DATA_DIR", str(APP_DIR / "datos")))
BACKUP_DIR = DATA_DIR / "backups"
DATA_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

LIVE_DB = DATA_DIR / "finanzas.db"
DEMO_DB = DATA_DIR / "demo_finanzas.db"
ATOMO_LOGO = APP_DIR / "assets" / "atomo_logo.png"
ATOMO_FAVICON = APP_DIR / "assets" / "atomo_favicon.png"
ATOMO_AVATAR = APP_DIR / "assets" / "atomo_avatar.png"
_PAGE_ICON = Image.open(ATOMO_FAVICON) if ATOMO_FAVICON.exists() else "⚛️"

PAGES = [
    "Pagos", "Ingresos", "Pendientes",
    "Inicio",
    "Electro",
    "Cuentas",
    "Tarjetas y cuotas",
    "Movimientos",
    "Deudas",
    "Inversiones",
    "Comparar rendimientos",
    "Proyección",
    "Preguntale a Átomo",
    "Instituciones",
    "Configuración",
]

PAGE_ICONS = {
    "Pagos": "💸", "Ingresos": "💰", "Pendientes": "📅",
    "Inicio": "🏠",
    "Electro": "⚡",
    "Cuentas": "🏦",
    "Tarjetas y cuotas": "💳",
    "Movimientos": "💸",
    "Deudas": "🧾",
    "Inversiones": "📈",
    "Comparar rendimientos": "⚖️",
    "Proyección": "🗓️",
    "Preguntale a Átomo": "🤖",
    "Instituciones": "🏛️",
    "Configuración": "⚙️",
}

TIPOS_INSTITUCION = [
    "Banco / Financiera",
    "Billetera / Fintech",
    "Broker / ALyC",
    "Exchange / Crypto",
    "Otro",
]

TIPOS_CUENTA = [
    "Caja de ahorro ARS",
    "Caja de ahorro USD",
    "Cuenta corriente",
    "Cuenta remunerada",
    "Billetera",
    "Cuenta comitente",
    "Cuenta de inversión",
    "Cuenta crypto",
    "Efectivo",
    "Otra",
]

MONEDAS = ["ARS", "USD", "USDT", "EUR", "Otra"]

CATEGORIAS = [
    "Sueldo / ingreso",
    "Vivienda / alquiler",
    "Supermercado / compra del mes",
    "Comida afuera",
    "Gasto hormiga",
    "Combustible / transporte",
    "Servicios",
    "Suscripciones",
    "Tarjetas",
    "Préstamos / deudas",
    "Salud",
    "Ropa",
    "Ocio",
    "Ahorro",
    "Inversión",
    "Impuestos",
    "Transferencia",
    "Otros",
]

DISCRETIONARY = {"Comida afuera", "Gasto hormiga", "Ropa", "Ocio"}

INGRESO_CATEGORIAS = ["Sueldo / ingreso", "Ahorro", "Inversión", "Otros"]
GASTO_CATEGORIAS = [c for c in CATEGORIAS if c not in {"Sueldo / ingreso", "Transferencia"}]


def categories_for_type(tipo):
    if tipo == "Ingreso":
        return INGRESO_CATEGORIAS
    if tipo == "Gasto":
        return GASTO_CATEGORIAS
    if tipo == "Compromiso":
        return [c for c in GASTO_CATEGORIAS if c != "Ahorro"]
    return ["Transferencia"]

TIPOS_ACTIVO = [
    "Acción argentina",
    "CEDEAR",
    "Bono soberano",
    "Bono provincial",
    "ON",
    "FCI",
    "ETF",
    "Acción exterior",
    "Cripto",
    "Dólar / stablecoin",
    "Caución",
    "Otro",
]

BASE_INSTITUTIONS = [
    # Bancos / financieras frecuentes y entidades argentinas conocidas.
    ("Banco / Financiera", "Banco de la Nación Argentina", "Institución sugerida"),
    ("Banco / Financiera", "Banco Provincia del Neuquén", "Institución sugerida"),
    ("Banco / Financiera", "Banco de Galicia y Buenos Aires", "Institución sugerida"),
    ("Banco / Financiera", "Banco Santander Argentina", "Institución sugerida"),
    ("Banco / Financiera", "BBVA Argentina", "Institución sugerida"),
    ("Banco / Financiera", "Banco Macro", "Institución sugerida"),
    ("Banco / Financiera", "Banco Patagonia", "Institución sugerida"),
    ("Banco / Financiera", "Banco Supervielle", "Institución sugerida"),
    ("Banco / Financiera", "Banco Credicoop", "Institución sugerida"),
    ("Banco / Financiera", "Banco Ciudad", "Institución sugerida"),
    ("Banco / Financiera", "Banco Hipotecario", "Institución sugerida"),
    ("Banco / Financiera", "Banco de La Pampa", "Institución sugerida"),
    ("Banco / Financiera", "Brubank", "Institución sugerida"),
    ("Banco / Financiera", "Ualá Bank", "Institución sugerida"),
    ("Banco / Financiera", "Banco del Sol", "Institución sugerida"),
    ("Banco / Financiera", "ICBC Argentina", "Institución sugerida"),
    ("Banco / Financiera", "Banco Comafi", "Institución sugerida"),
    ("Banco / Financiera", "Banco de Valores", "Institución sugerida"),
    ("Banco / Financiera", "Banco Industrial", "Institución sugerida"),
    ("Banco / Financiera", "Banco BICA", "Institución sugerida"),
    ("Banco / Financiera", "Banco Coinag", "Institución sugerida"),
    ("Banco / Financiera", "Banco Columbia", "Institución sugerida"),
    ("Banco / Financiera", "Banco Sáenz", "Institución sugerida"),
    ("Banco / Financiera", "Banco CMF", "Institución sugerida"),
    ("Banco / Financiera", "Banco Mariva", "Institución sugerida"),
    ("Banco / Financiera", "Banco Piano", "Institución sugerida"),
    ("Banco / Financiera", "Banco Rioja", "Institución sugerida"),
    ("Banco / Financiera", "Banco de Córdoba", "Institución sugerida"),
    ("Banco / Financiera", "Banco de Corrientes", "Institución sugerida"),
    ("Banco / Financiera", "Banco de Formosa", "Institución sugerida"),
    ("Banco / Financiera", "Banco de San Juan", "Institución sugerida"),
    ("Banco / Financiera", "Banco de Santa Cruz", "Institución sugerida"),
    ("Banco / Financiera", "Banco de Santiago del Estero", "Institución sugerida"),
    ("Banco / Financiera", "Banco del Chubut", "Institución sugerida"),
    ("Banco / Financiera", "Banco de Tierra del Fuego", "Institución sugerida"),
    ("Banco / Financiera", "Nuevo Banco del Chaco", "Institución sugerida"),
    ("Banco / Financiera", "Nuevo Banco de Entre Ríos", "Institución sugerida"),
    ("Banco / Financiera", "Nuevo Banco de Santa Fe", "Institución sugerida"),
    ("Banco / Financiera", "BICE", "Institución sugerida"),

    # Billeteras / fintech
    ("Billetera / Fintech", "Mercado Pago", "Institución sugerida"),
    ("Billetera / Fintech", "Ualá", "Institución sugerida"),
    ("Billetera / Fintech", "Naranja X", "Institución sugerida"),
    ("Billetera / Fintech", "Personal Pay", "Institución sugerida"),
    ("Billetera / Fintech", "Prex Argentina", "Institución sugerida"),
    ("Billetera / Fintech", "AstroPay", "Institución sugerida"),
    ("Billetera / Fintech", "Lemon", "Institución sugerida"),
    ("Billetera / Fintech", "Belo", "Institución sugerida"),
    ("Billetera / Fintech", "Buenbit", "Institución sugerida"),
    ("Billetera / Fintech", "MODO", "Institución sugerida"),

    # Brokers / ALyC. El usuario puede sumar cualquiera que falte.
    ("Broker / ALyC", "InvertirOnline (IOL)", "Institución sugerida"),
    ("Broker / ALyC", "Cocos Capital", "Institución sugerida"),
    ("Broker / ALyC", "Balanz", "Institución sugerida"),
    ("Broker / ALyC", "Portfolio Personal Inversiones (PPI)", "Institución sugerida"),
    ("Broker / ALyC", "Bull Market Brokers", "Institución sugerida"),
    ("Broker / ALyC", "Allaria", "Institución sugerida"),
    ("Broker / ALyC", "Adcap", "Institución sugerida"),
    ("Broker / ALyC", "Puente", "Institución sugerida"),
    ("Broker / ALyC", "SBS", "Institución sugerida"),
    ("Broker / ALyC", "Cohen", "Institución sugerida"),
    ("Broker / ALyC", "Max Capital", "Institución sugerida"),
    ("Broker / ALyC", "Eco Valores", "Institución sugerida"),
    ("Broker / ALyC", "Rava Bursátil", "Institución sugerida"),
    ("Broker / ALyC", "Criteria", "Institución sugerida"),
    ("Broker / ALyC", "Sailing", "Institución sugerida"),
    ("Broker / ALyC", "Mariva Bursátil", "Institución sugerida"),

    # Crypto
    ("Exchange / Crypto", "Binance", "Institución sugerida"),
    ("Exchange / Crypto", "Bitget", "Institución sugerida"),
    ("Exchange / Crypto", "Bybit", "Institución sugerida"),
    ("Exchange / Crypto", "Ripio", "Institución sugerida"),
    ("Exchange / Crypto", "SatoshiTango", "Institución sugerida"),
    ("Otro", "Efectivo", "Institución sugerida"),
]

