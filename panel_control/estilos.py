"""CSS del panel, tomando paleta/efectos de referencia de un mockup HTML
(index-design.html) que compartió el usuario: fondo casi negro, verde neón
como acento, tarjetas con borde sutil + glow, tipografía DM Sans/JetBrains
Mono. Se inyecta una sola vez al principio de dashboard.py.

Streamlit no permite tocar su HTML/estructura interna, así que esto solo
puede re-vestir lo que ya renderiza (vía sus atributos data-testid, que son
más estables entre versiones que sus clases con hash)."""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  --bg: #0C0F10;
  --surface: #141A1B;
  --surface-alt: #1A2322;
  --fg: #E0ECE9;
  --muted: #728A86;
  --border: #1E2A28;
  --accent: #71EF8A;
  --accent-light: #A2FFB5;
  --accent-faint: rgba(113, 239, 138, 0.1);
  --warn: #E6AD30;
  --warn-faint: rgba(230, 173, 48, 0.12);
  --danger: #FF6B6B;
  --danger-faint: rgba(255, 107, 107, 0.1);
  --font-display: 'DM Sans', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, Menlo, monospace;
  --r-sm: 6px;
  --r-md: 10px;
  --r-lg: 14px;
  --glow-accent: 0 0 12px rgba(113, 239, 138, 0.25);
  --glow-accent-strong: 0 0 20px rgba(113, 239, 138, 0.35);
  --ease: cubic-bezier(0.22, 1, 0.36, 1);
}

[data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stMain"] {
  background: var(--bg);
  color: var(--fg);
}

[data-testid="stHeader"] {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}

h1, h2, h3, [data-testid="stHeading"], [data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 {
  font-family: var(--font-display) !important;
  letter-spacing: -0.02em;
  font-weight: 700 !important;
}

[data-testid="stCaptionContainer"] { color: var(--muted) !important; }

/* ===== METRIC CARDS ===== */
[data-testid="stMetric"] {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 1rem 1.1rem;
  position: relative;
  overflow: hidden;
  transition: border-color 200ms var(--ease), box-shadow 200ms var(--ease);
}

[data-testid="stMetric"]::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: var(--accent);
  box-shadow: 0 0 8px var(--accent);
}

[data-testid="stMetric"]:hover {
  border-color: var(--accent);
  box-shadow: var(--glow-accent);
}

[data-testid="stMetricLabel"] {
  font-size: 0.72rem !important;
  font-weight: 500 !important;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--muted) !important;
}

[data-testid="stMetricValue"] {
  font-family: var(--font-mono) !important;
  font-weight: 600 !important;
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
}

/* ===== BUTTONS ===== */
button[data-testid^="stBaseButton"] {
  border-radius: var(--r-sm) !important;
  font-weight: 500 !important;
  transition: all 150ms var(--ease) !important;
  letter-spacing: 0.01em;
}

button[data-testid="stBaseButton-primary"] {
  background: var(--accent) !important;
  border-color: var(--accent) !important;
  color: #0C0F10 !important;
  font-weight: 600 !important;
  box-shadow: var(--glow-accent);
}

button[data-testid="stBaseButton-primary"]:hover {
  background: var(--accent-light) !important;
  border-color: var(--accent-light) !important;
  box-shadow: var(--glow-accent-strong);
}

button[data-testid="stBaseButton-secondary"] {
  background: var(--surface) !important;
  border-color: var(--border) !important;
  color: var(--fg) !important;
}

button[data-testid="stBaseButton-secondary"]:hover {
  border-color: var(--muted) !important;
  background: var(--surface-alt) !important;
}

/* ===== TABS ===== */
[data-testid="stTabs"] [role="tablist"] {
  border-bottom: 1px solid var(--border);
  gap: 0.25rem;
}

[data-testid="stTabs"] button[role="tab"] {
  color: var(--muted);
  font-weight: 500;
  transition: color 150ms var(--ease);
}

[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
  color: var(--accent);
  text-shadow: 0 0 8px rgba(113, 239, 138, 0.3);
}

[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
  background-color: var(--accent) !important;
  box-shadow: 0 0 8px rgba(113, 239, 138, 0.5);
}

/* ===== CONTAINERS / "CARDS" ===== */
[data-testid="stVerticalBlockBorderWrapper"] > div {
  border-color: var(--border) !important;
  border-radius: var(--r-lg) !important;
  background: var(--surface);
}

/* ===== DATAFRAME / TABLE ===== */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  overflow: hidden;
}

/* ===== ALERTS ===== */
[data-testid="stAlertContainer"] {
  border-radius: var(--r-md) !important;
  border: 1px solid var(--border) !important;
}

[data-testid="stAlertContentSuccess"] { color: var(--accent) !important; }
[data-testid="stAlertContentInfo"] { color: var(--fg) !important; }
[data-testid="stAlertContentError"] { color: var(--danger) !important; }

/* ===== INPUTS ===== */
[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
  background: var(--bg) !important;
  border-color: var(--border) !important;
  color: var(--fg) !important;
  transition: border-color 150ms var(--ease), box-shadow 150ms var(--ease) !important;
}

[data-testid="stTextArea"] textarea:focus,
[data-testid="stTextInput"] input:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px var(--accent-faint) !important;
}

/* ===== SIDEBAR / MENÚ DE NAVEGACIÓN ===== */
[data-testid="stSidebar"] {
  background: var(--surface);
  border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
  color: var(--muted) !important;
}

[data-testid="stSidebar"] button[data-testid^="stBaseButton"] {
  width: 100%;
  justify-content: flex-start !important;
  text-align: left !important;
  border-radius: var(--r-sm) !important;
  margin-bottom: 2px;
}

[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] {
  background: transparent !important;
  border-color: transparent !important;
  color: var(--fg) !important;
}

[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover {
  background: var(--surface-alt) !important;
  border-color: var(--border) !important;
}

[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {
  background: var(--accent-faint) !important;
  color: var(--accent-light) !important;
  border: none !important;
  border-left: 3px solid var(--accent) !important;
  box-shadow: none;
  font-weight: 600 !important;
}

/* ===== SCROLLBAR (webkit) ===== */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }
</style>
"""
