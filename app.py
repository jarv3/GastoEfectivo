import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import Optional

# -----------------------------
# Config
# -----------------------------
import streamlit as st

st.set_page_config(
    page_title="Gasto Efectivo",
    page_icon="🔥",
    layout="wide",
    menu_items={'Get Help': None, 'Report a bug': None, 'About': None}
)

st.markdown("""
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Estilos Mobile First para el menú superior ---
st.markdown("""
<style>
/* Contenedor "sticky" para el menú (pegado arriba al hacer scroll) */
#app-top-nav {
  position: sticky;
  top: 0;                /* se pega al top del viewport */
  z-index: 999;          /* por encima del contenido */
  padding: 0.5rem 0 0.25rem 0;
  background: transparent; /* se funde con el tema */
  backdrop-filter: blur(2px);
}

/* Botones tipo "card" con área táctil cómoda */
#app-top-nav button[kind="secondary"],
#app-top-nav button[kind="primary"],
#app-top-nav button {
  padding: 12px 14px !important;         /* mayor área tocable */
  border-radius: 12px !important;        /* pill suave */
  border: 1px solid var(--secondary-background-color, #3a3a3a) !important;
  font-weight: 600;
}

/* Hover sutil */
#app-top-nav button:hover { filter: brightness(1.06); }

/* Ajustes para pantallas pequeñas */
@media (max-width: 420px) {
  #app-top-nav button[kind="secondary"],
  #app-top-nav button[kind="primary"],
  #app-top-nav button {
    padding: 10px 10px !important;
    font-size: 0.90rem;                   /* un poco más compacto */
  }
  /* Un pequeño espacio inferior del bloque del menú */
  #app-top-nav { padding-bottom: 0.35rem; }
}

/* Espaciado vertical mínimo entre filas de columnas */
#app-top-nav [data-testid="column"] {
  margin-bottom: 0.4rem;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Navegación (sin sidebar)
# -----------------------------
PAGES = ["Dashboard", "Gastos", "Categorías", "Presupuesto", "Reportes"]


# Íconos para cada sección (puedes cambiarlos por los que prefieras)
PAGE_ICONS = {
    "Dashboard": "📌",
    "Gastos": "🧾",
    "Categorías": "🏷️",
    "Presupuesto": "📅",
    "Reportes": "📊",
}

def goto(page_name: str):
    """Cambia de sección y hace rerun para aplicar el cambio."""
    st.session_state["page"] = page_name
    #st.rerun()

# -----------------------------
# Utilidades
# -----------------------------
def month_start(d: date) -> date:
    return date(d.year, d.month, 1)

def render_entries_grid(pages, cols_per_row: int = 5, center_last_row: bool = False):
    current = st.session_state.get("page", pages[0] if pages else "")
    n = len(pages)

    for i in range(0, n, cols_per_row):
        row_pages = pages[i : i + cols_per_row]

        if center_last_row and len(row_pages) < cols_per_row:
            pad_left = (cols_per_row - len(row_pages)) // 2
            pad_right = cols_per_row - len(row_pages) - pad_left
            cols = st.columns(pad_left + len(row_pages) + pad_right)
            slots = cols[pad_left : pad_left + len(row_pages)]
        else:
            slots = st.columns(len(row_pages))

        for c, name in zip(slots, row_pages):
            with c:
                icon = PAGE_ICONS.get(name, "•")
                label = f"{icon} {name}"
                # Si es la página actual, pinta como 'primary'
                btype = "primary" if name == current else "secondary"
                st.button(
                    label,
                    key=f"nav_{name}",
                    type=btype,
                    use_container_width=True,
                    on_click=goto,
                    args=(name,),
                )

# -----------------------------
# Supabase helpers
# -----------------------------
def get_supabase() -> Client:
    """
    Crea un cliente Supabase por sesión de usuario de Streamlit (no global cache),
    para evitar mezclar estados entre usuarios.
    """
    if "supabase" not in st.session_state:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_ANON_KEY"]
        st.session_state.supabase = create_client(url, key)  # create_client() recomendado por Supabase
    return st.session_state.supabase

def is_logged_in() -> bool:
    return st.session_state.get("auth", {}).get("user") is not None

def set_auth(auth_response):
    """
    Guarda user/session para la sesión actual.
    Supabase-py por defecto mantiene la sesión en memoria (persist_session),
    pero igual guardamos datos útiles para UI.
    """
    st.session_state.auth = {
        "user": getattr(auth_response, "user", None) or (auth_response.get("user") if isinstance(auth_response, dict) else None),
        "session": getattr(auth_response, "session", None) or (auth_response.get("session") if isinstance(auth_response, dict) else None),
    }

def current_user_email() -> str:
    user = st.session_state.get("auth", {}).get("user")
    if not user:
        return ""
    # user puede ser objeto o dict
    return getattr(user, "email", None) or user.get("email", "")

# -----------------------------
# Auth UI
# -----------------------------
def auth_block():
    st.title("💳 Gasto Efectivo")

    # Enlaces
    VIDEO_URL = "https://www.youtube.com/watch?v=cdtMJSxGNZo"
    PAGO_URL = "https://ppls.me/8sI5sriWVSFgKZkOkQIDFA"

    # ---- Layout en dos columnas
    col_left, col_right = st.columns([3, 2])  # 60% | 40%

    with col_left:
        # Texto persuasivo + duración de prueba + precio
        st.markdown(
            """
            **No necesitas ganar más dinero para mejorar tu vida financiera; necesitas conocer tus gastos.**
            **Mira primero el video** y aprende a usar **Gasto Efectivo** paso a paso.
            Ponla a prueba durante **15 días** y evalúa cómo mejora tu claridad sobre los gastos.
            Si después de ese tiempo te resulta útil, adquiere la versión completa por **$20 (pago único)**.
            """
        )
        # --- Botones de acción
        try:
            c1, c2 = st.columns(2)
            with c1:
                st.link_button("🎥 Ver el video", VIDEO_URL, type="secondary")
            with c2:
                st.link_button("💳 Lo quiero", PAGO_URL, type="primary")
        except Exception:
            st.markdown(
                f"""
                - 🎥 **Ver el video de uso:** {VIDEO_URL}
                - 💳 **Lo quiero:** {PAGO_URL}
                """
            )

    with col_right:
        # ---- Tabs de autenticación
        supabase = get_supabase()
        tab_login, tab_signup = st.tabs(["🔐 Iniciar sesión", "🆕 Crear cuenta"])

        with tab_login:
            email = st.text_input("Correo", key="login_email")
            password = st.text_input("Contraseña", type="password", key="login_pass")
            if st.button("Entrar", type="primary"):
                try:
                    resp = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    set_auth(resp)
                    st.success("✅ Sesión iniciada.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ No se pudo iniciar sesión: {e}")

        with tab_signup:
            email2 = st.text_input("Correo", key="signup_email")
            password2 = st.text_input("Contraseña", type="password", key="signup_pass")
            if st.button("Crear cuenta", type="primary"):
                try:
                    resp = supabase.auth.sign_up({"email": email2, "password": password2})
                    set_auth(resp)
                    st.success("✅ Registro creado. Revisa tu correo si necesitas confirmar la cuenta.")
                except Exception as e:
                    st.error(f"❌ No se pudo crear la cuenta: {e}")

# -----------------------------
# Data access helpers (CRUD)
# -----------------------------
def fetch_categories():
    supabase = get_supabase()
    res = supabase.table("categories").select("id,name,created_at").order("name").execute()
    return res.data or []

def add_category(name: str):
    supabase = get_supabase()
    name = name.strip()
    if not name:
        return
    supabase.table("categories").insert({"name": name}).execute()

def delete_category(category_id: str):
    supabase = get_supabase()
    supabase.table("categories").delete().eq("id", category_id).execute()

def upsert_budget(budget_month: date, amount: float):
    supabase = get_supabase()
    # upsert por unique(user_id, budget_month)
    supabase.table("budgets").upsert(
        {"budget_month": str(budget_month), "amount": float(amount)},
        on_conflict="user_id,budget_month"
    ).execute()

def fetch_budget_month(budget_month: date):
    supabase = get_supabase()
    try:
        res = (
            supabase.table("budgets")
            .select("id,budget_month,amount")
            .eq("budget_month", str(budget_month))
            .execute()
        )
        data = res.data or []
        return data[0] if len(data) > 0 else None
    except Exception as e:
        st.error(f"Error consultando presupuesto: {e}")
        return None

def delete_budget(budget_id: str):
    supabase = get_supabase()
    supabase.table("budgets").delete().eq("id", budget_id).execute()

def add_expense(expense_date: date, amount: float, category_id: Optional[str], description: str):
    supabase = get_supabase()
    payload = {
        "expense_date": str(expense_date),
        "amount": float(amount),
        "category_id": category_id,
        "description": description.strip() if description else None,
    }
    supabase.table("expenses").insert(payload).execute()

def fetch_expenses(date_from: date, date_to: date):
    supabase = get_supabase()
    res = (
        supabase.table("expenses")
        .select("id,expense_date,amount,description,category_id,created_at")
        .gte("expense_date", str(date_from))
        .lte("expense_date", str(date_to))
        .order("expense_date", desc=True)
        .execute()
    )
    return res.data or []

def delete_expense(expense_id: str):
    supabase = get_supabase()
    supabase.table("expenses").delete().eq("id", expense_id).execute()

# -----------------------------
# Main app (logged)
# -----------------------------
def app_main():
    st.title("💳 Gasto Efectivo")

    # Cabecera con usuario y cerrar sesión
    colA, colB = st.columns([3, 1])
    with colA:
        st.caption(f"Sesión: **{current_user_email()}**")
    with colB:
        if st.button("Cerrar sesión"):
            try:
                get_supabase().auth.sign_out()
            except Exception:
                pass
            st.session_state.auth = {"user": None, "session": None}
            st.rerun()
     
    # Estado inicial de la página
    if "page" not in st.session_state:
        st.session_state["page"] = "Dashboard"
    page = st.session_state["page"]

    # -----------------------------
    # Menú principal en el cuerpo
    # -----------------------------
    #st.markdown("#### Menú")
    render_entries_grid(PAGES, cols_per_row=5, center_last_row=False)
    st.markdown("")

    # -----------------------------
    # Renderizado de secciones
    # -----------------------------

    # -------- Dashboard
    if page == "Dashboard":
        st.subheader("📌 Dashboard")
        today = date.today()
        bmonth = month_start(today)

        # Presupuesto del mes actual
        b = fetch_budget_month(bmonth)
        budget_amount = float(b["amount"]) if b else 0.0

        # Gastos del mes actual
        start = bmonth
        end = (bmonth + relativedelta(months=1)) - relativedelta(days=1)
        expenses = fetch_expenses(start, end)
        total_spent = sum(float(x["amount"]) for x in expenses) if expenses else 0.0
        remaining = max(budget_amount - total_spent, 0.0)

        # Gastos del mes anterior
        prev_month_start = bmonth - relativedelta(months=1)
        prev_month_end = bmonth - relativedelta(days=1)
        prev_expenses = fetch_expenses(prev_month_start, prev_month_end)
        prev_total_spent = sum(float(x["amount"]) for x in prev_expenses) if prev_expenses else 0.0

        # Métricas
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Presupuesto del mes", f"${budget_amount:,.2f}")
        c2.metric("Gastado", f"${total_spent:,.2f}")
        c3.metric("Disponible", f"${remaining:,.2f}")
        c4.metric("Gastado mes anterior", f"${prev_total_spent:,.2f}")

        st.caption("Tip: configura el presupuesto en la sección 'Presupuesto (mensual)'.")

    # -------- Gastos
    elif page == "Gastos":
        st.subheader("🧾 Gastos")

        cats = fetch_categories()
        cat_map = {"(Sin categoría)": None}
        for c in cats:
            cat_map[c["name"]] = c["id"]

        c1, c2, c3 = st.columns([1.2, 1, 2])

        with c1:
            exp_date = st.date_input("Fecha del gasto", value=date.today(), key="exp_date")
        with c2:
            amount = st.number_input("Monto (USD)", min_value=0.0, step=1.0, key="exp_amount")
        with c3:
            cat_name = st.selectbox("Categoría", list(cat_map.keys()), key="exp_cat")

        desc = st.text_input("Descripción (opcional)", placeholder="Ej: Supermercado, taxi...", key="exp_desc")

        if st.button("Agregar gasto", type="primary"):
            try:
                add_expense(exp_date, amount, cat_map[cat_name], desc)
                st.success("Gasto agregado.")
                st.rerun()
            except Exception as e:
                st.error(f"No se pudo agregar: {e}")

        st.markdown("---")
        st.markdown("### Historial y eliminación por fechas")

        default_from = date.today().replace(day=1)
        default_to = date.today()

        dcol1, dcol2 = st.columns(2)
        with dcol1:
            dfrom = st.date_input("Desde", value=default_from, key="filter_from")
        with dcol2:
            dto = st.date_input("Hasta", value=default_to, key="filter_to")

        rows = fetch_expenses(dfrom, dto)

        if not rows:
            st.info("No hay gastos en el rango seleccionado.")
            return

        # Enriquecer con nombre de categoría
        cat_lookup = {c["id"]: c["name"] for c in cats}
        for r in rows:
            r["category"] = cat_lookup.get(r["category_id"], "Sin categoría")

        df = pd.DataFrame(rows)
        df["expense_date"] = pd.to_datetime(df["expense_date"])
        df = df.sort_values("expense_date", ascending=False)

        st.dataframe(df[["expense_date", "amount", "category", "description"]], width='stretch')

        # Eliminar uno
        labels = {
            f"{r['expense_date']} | {r['amount']} | {r['category']} | { (r.get('description') or '')[:20] }...": r["id"]
            for r in rows
        }
        pick = st.selectbox("Selecciona un gasto para eliminar", ["(ninguno)"] + list(labels.keys()))
        if pick != "(ninguno)" and st.button("Eliminar gasto", type="secondary"):
            try:
                delete_expense(labels[pick])
                st.success("Gasto eliminado.")
                st.rerun()
            except Exception as e:
                st.error(f"No se pudo eliminar: {e}")

    # -------- Categoría
    elif page == "Categorías":
        st.subheader("🏷️ Categorías")
        c1, c2 = st.columns([2, 3])
        with c1:
            st.markdown("### Crear categoría")
            new_name = st.text_input("Nombre", placeholder="Ej: Alimentación")
            if st.button("Agregar categoría", type="primary"):
                try:
                    add_category(new_name)
                    st.success("Categoría agregada.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo agregar: {e}")
        with c2:
            st.markdown("### Mis categorías")
            cats = fetch_categories()
            if not cats:
                st.info("Aún no tienes categorías.")
            else:
                df = pd.DataFrame(cats)
                st.dataframe(df[["name", "created_at"]], width='stretch')
                options = {f"{row['name']} ({row['id'][:8]})": row["id"] for row in cats}
                to_delete = st.selectbox("Eliminar categoría", ["(ninguna)"] + list(options.keys()))
                if to_delete != "(ninguna)" and st.button("Eliminar definitivamente", type="secondary"):
                    try:
                        delete_category(options[to_delete])
                        st.success("Categoría eliminada. (Los gastos quedan sin categoría si estaban asociados)")
                        st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo eliminar: {e}")

    # -------- Presupuesto
    elif page == "Presupuesto":
        st.subheader("📅 Presupuesto mensual")
        today = date.today()
        selected = st.date_input("Selecciona un día del mes (se guardará como mes)", value=today)
        bmonth = month_start(selected)

        current = fetch_budget_month(bmonth)
        current_amount = float(current["amount"]) if current else 0.0

        st.write(f"Mes: **{bmonth.strftime('%Y-%m')}**")
        amount = st.number_input("Presupuesto (USD)", min_value=0.0, value=current_amount, step=10.0)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Guardar/Actualizar", type="primary"):
                try:
                    upsert_budget(bmonth, amount)
                    st.success("Presupuesto guardado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo guardar: {e}")

        with c2:
            if current and st.button("Eliminar presupuesto del mes", type="secondary"):
                try:
                    delete_budget(current["id"])
                    st.success("Presupuesto eliminado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo eliminar: {e}")

    # -------- Reportes
    elif page == "Reportes":
        st.subheader("📊 Reportes")
        dcol1, dcol2 = st.columns(2)
        with dcol1:
            dfrom = st.date_input("Desde", value=date.today().replace(day=1), key="rep_from")
        with dcol2:
            dto = st.date_input("Hasta", value=date.today(), key="rep_to")

        rows = fetch_expenses(dfrom, dto)
        if not rows:
            st.info("No hay datos para reportar en ese rango.")
            return

        cats = fetch_categories()
        cat_lookup = {c["id"]: c["name"] for c in cats}

        df = pd.DataFrame(rows)
        df["category"] = df["category_id"].map(cat_lookup).fillna("Sin categoría")
        df["expense_date"] = pd.to_datetime(df["expense_date"])
        df["amount"] = df["amount"].astype(float)

        st.markdown("### Gastos por categoría")
        grp = df.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
        fig = px.pie(grp, names="category", values="amount", hole=0.4)
        st.plotly_chart(fig, width='stretch')

        st.markdown("### Evolución (diario)")
        daily = (
            df.assign(date=df["expense_date"].dt.date)
                .groupby("date", as_index=False)["amount"]
                .sum()
                )
        fig2 = px.line(daily, x="date", y="amount", markers=True)
        st.plotly_chart(fig2, width='stretch')

        st.markdown("### Detalle")
        st.dataframe(df[["expense_date", "amount", "category", "description"]].sort_values("expense_date", ascending=False),
                     width='stretch')

# -----------------------------
# Router
# -----------------------------
if not is_logged_in():
    auth_block()
else:
    app_main()

