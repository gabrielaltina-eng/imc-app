import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. CONFIGURAÇÃO VISUAL & TEMA HIGH-TECH
st.set_page_config(
    page_title="IMC+ | Performance & Health",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0b0f19; }
    
    /* Cards estilo SaaS/Dashboard */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #161e2e 0%, #111827 100%);
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    
    /* Header Principal */
    .hero-card {
        background: linear-gradient(90deg, #1e1b4b 0%, #0f172a 100%);
        border: 1px solid #312e81;
        border-left: 6px solid #6366f1;
        padding: 24px;
        border-radius: 14px;
        margin-bottom: 25px;
    }
    
    .hero-title {
        color: #f8fafc;
        font-size: 26px;
        font-weight: 800;
        margin: 0;
    }
    
    .hero-sub {
        color: #94a3b8;
        font-size: 14px;
        margin-top: 5px;
    }

    /* Botões Stylized */
    div.stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
</style>
""", unsafe_allow_html=True)

# 2. BANCO DE DADOS ROBUSTO
DB_NAME = "imc_plus_v5.db"

def get_connection():
    return sqlite3.connect(DB_NAME, timeout=10, check_same_thread=False)

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                idade INTEGER,
                altura REAL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                data TEXT NOT NULL,
                peso REAL NOT NULL,
                imc REAL NOT NULL,
                classificacao TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registros_diarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                data TEXT NOT NULL,
                agua INTEGER DEFAULT 0,
                passos INTEGER DEFAULT 0,
                UNIQUE(nome, data)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS atividades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                data TEXT NOT NULL,
                atividade TEXT NOT NULL,
                categoria TEXT NOT NULL,
                intensidade TEXT NOT NULL,
                duracao INTEGER NOT NULL,
                calorias INTEGER NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habitos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                habito TEXT NOT NULL,
                status INTEGER DEFAULT 0,
                UNIQUE(nome, habito)
            )
        """)
        conn.commit()

init_db()

# CÁLCULOS
def calcular_imc(peso, altura):
    return peso / (altura ** 2) if altura > 0 else 0

def classificar_imc(imc):
    if imc < 18.5: return "Abaixo do peso"
    elif 18.5 <= imc < 25.0: return "Peso Normal"
    elif 25.0 <= imc < 30.0: return "Sobrepeso"
    elif 30.0 <= imc < 35.0: return "Obesidade I"
    elif 35.0 <= imc < 40.0: return "Obesidade II"
    else: return "Obesidade III"

# 3. BARRA LATERAL - GESTÃO DE USUÁRIO
st.sidebar.title("⚡ IMC+ Performance")

with get_connection() as conn:
    usuarios_df = pd.read_sql_query("SELECT nome FROM usuarios", conn)
    lista_usuarios = usuarios_df['nome'].tolist() if not usuarios_df.empty else []

st.sidebar.markdown("### 👤 Usuário")
if not lista_usuarios:
    st.sidebar.warning("Nenhum perfil cadastrado.")
    novo_u = st.sidebar.text_input("Seu Nome:")
    idade_u = st.sidebar.number_input("Idade:", 1, 120, 25)
    alt_u = st.sidebar.number_input("Altura (m):", 0.50, 2.50, 1.75, step=0.01)
    if st.sidebar.button("Criar Perfil", type="primary"):
        if novo_u.strip():
            with get_connection() as conn:
                conn.cursor().execute("INSERT INTO usuarios (nome, idade, altura) VALUES (?,?,?)", (novo_u.strip(), idade_u, alt_u))
                conn.commit()
            st.rerun()
    st.stop()

usuario_ativo = st.sidebar.selectbox("Conectado como:", lista_usuarios)

# Botão rápido para adicionar novo usuário
with st.sidebar.expander("➕ Cadastrar Outra Pessoa"):
    cad_nome = st.text_input("Nome:")
    cad_idade = st.number_input("Idade:", 1, 120, 20)
    cad_altura = st.number_input("Altura (m):", 0.50, 2.50, 1.70, step=0.01, key="alt_cad")
    if st.button("Salvar Novo Perfil"):
        if cad_nome.strip():
            try:
                with get_connection() as conn:
                    conn.cursor().execute("INSERT INTO usuarios (nome, idade, altura) VALUES (?,?,?)", (cad_nome.strip(), cad_idade, cad_altura))
                    conn.commit()
                st.success("Criado!")
                st.rerun()
            except:
                st.error("Nome já existe!")

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navegação",
    ["📊 Dashboard Geral", "🏋️ Treinos & Atividades", "💧 Água & Passos", "✅ Metas & Hábitos", "📈 Histórico Evolutivo"]
)

with get_connection() as conn:
    user_data = pd.read_sql_query("SELECT * FROM usuarios WHERE nome = ?", conn, params=(usuario_ativo,)).iloc[0]

# --- 1. DASHBOARD GERAL ---
if menu == "📊 Dashboard Geral":
    st.markdown(f"""
        <div class="hero-card">
            <div class="hero-title">Painel de Performance: {usuario_ativo}</div>
            <div class="hero-sub">Visão geral do seu estado físico e evolução biométrica</div>
        </div>
    """, unsafe_allow_html=True)

    with get_connection() as conn:
        df_h = pd.read_sql_query("SELECT * FROM historico WHERE nome = ? ORDER BY id DESC", conn, params=(usuario_ativo,))

    peso_atual = df_h['peso'].iloc[0] if not df_h.empty else 70.0
    imc_atual = df_h['imc'].iloc[0] if not df_h.empty else calcular_imc(peso_atual, user_data['altura'])
    
    delta = 0.0
    if len(df_h) > 1:
        delta = df_h['peso'].iloc[0] - df_h['peso'].iloc[1]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Peso Atual", f"{peso_atual:.1f} kg", delta=f"{delta:.1f} kg", delta_color="inverse")
    c2.metric("Altura", f"{user_data['altura']:.2f} m")
    c3.metric("IMC", f"{imc_atual:.1f}")
    c4.metric("Classificação", classificar_imc(imc_atual))

    st.markdown("---")
    st.markdown("### 📝 Atualizar Peso / Altura")
    
    col_p, col_a = st.columns(2)
    p_in = col_p.number_input("Peso (kg):", 1.0, 300.0, float(peso_atual), step=0.1)
    a_in = col_a.number_input("Altura (m):", 0.50, 2.50, float(user_data['altura']), step=0.01)

    if st.button("Salvar Nova Medição", type="primary", use_container_width=True):
        imc_calc = calcular_imc(p_in, a_in)
        diag = classificar_imc(imc_calc)
        data_agora = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO historico (nome, data, peso, imc, classificacao) VALUES (?,?,?,?,?)",
                        (usuario_ativo, data_agora, p_in, imc_calc, diag))
            cur.execute("UPDATE usuarios SET altura = ? WHERE nome = ?", (a_in, usuario_ativo))
            conn.commit()
        st.success("Medição registrada com sucesso!")
        st.rerun()

# --- 2. TREINOS & ATIVIDADES ---
elif menu == "🏋️ Treinos & Atividades":
    st.markdown(f"""
        <div class="hero-card">
            <div class="hero-title">Central de Treinos — {usuario_ativo}</div>
            <div class="hero-sub">Registre suas atividades diárias e monitore o gasto calórico</div>
        </div>
    """, unsafe_allow_html=True)

    data_hoje = datetime.now().strftime('%Y-%m-%d')

    with st.form("form_treino", clear_on_submit=True):
        st.markdown("#### ⚡ Registrar Novo Treino")
        c_nome, c_cat = st.columns(2)
        atv_nome = c_nome.text_input("Nome da Atividade:", placeholder="Ex: Corrida, Musculação Leg Day")
        atv_cat = c_cat.selectbox("Categoria:", ["Cardio", "Musculação", "Esportes", "Crossfit", "Outro"])

        c_int, c_dur, c_cal = st.columns(3)
        atv_int = c_int.select_slider("Intensidade:", ["Leve", "Moderada", "Intensa"], value="Intensa")
        atv_dur = c_dur.number_input("Duração (Minutos):", 1, 300, 45)
        atv_cal = c_cal.number_input("Calorias Queimadas (kcal):", 0, 3000, 250)

        submit = st.form_submit_button("🔥 Salvar Atividade", type="primary", use_container_width=True)

        if submit:
            nome_final = atv_nome.strip() if atv_nome.strip() else atv_cat
            with get_connection() as conn:
                conn.cursor().execute("""
                    INSERT INTO atividades (nome, data, atividade, categoria, intensidade, duracao, calorias)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (usuario_ativo, data_hoje, nome_final, atv_cat, atv_int, atv_dur, atv_cal))
                conn.commit()
            st.success("Atividade salva no banco de dados!")
            st.rerun()

    st.markdown("---")
    st.markdown("### 📋 Histórico de Treinos")
    
    with get_connection() as conn:
        df_atv = pd.read_sql_query("""
            SELECT data as Data, atividade as Atividade, categoria as Categoria, 
                   intensidade as Intensidade, duracao as 'Duração (min)', calorias as 'Calorias (kcal)' 
            FROM atividades WHERE nome = ? ORDER BY id DESC
        """, conn, params=(usuario_ativo,))

    if not df_atv.empty:
        st.dataframe(df_atv, use_container_width=True)
    else:
        st.info("Nenhum treino registrado ainda.")

# --- 3. ÁGUA & PASSOS ---
elif menu == "💧 Água & Passos":
    st.title(f"💧 Consumo & Passos — {usuario_ativo}")
    data_hoje = datetime.now().strftime('%Y-%m-%d')

    with get_connection() as conn:
        reg = pd.read_sql_query("SELECT agua, passos FROM registros_diarios WHERE nome = ? AND data = ?", conn, params=(usuario_ativo, data_hoje))

    agua_atual = int(reg['agua'].iloc[0]) if not reg.empty else 0
    passos_atual = int(reg['passos'].iloc[0]) if not reg.empty else 0

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🚰 Hidratação")
        st.metric("Total Hoje", f"{agua_atual} / 2500 ml")
        st.progress(min(agua_atual / 2500, 1.0))
        
        ca, cb = st.columns(2)
        if ca.button("+250 ml", use_container_width=True):
            agua_atual += 250
            with get_connection() as conn:
                conn.cursor().execute("INSERT INTO registros_diarios (nome, data, agua, passos) VALUES (?, ?, ?, ?) ON CONFLICT(nome, data) DO UPDATE SET agua = ?", (usuario_ativo, data_hoje, agua_atual, passos_atual, agua_atual))
                conn.commit()
            st.rerun()

        if cb.button("+500 ml", use_container_width=True):
            agua_atual += 500
            with get_connection() as conn:
                conn.cursor().execute("INSERT INTO registros_diarios (nome, data, agua, passos) VALUES (?, ?, ?, ?) ON CONFLICT(nome, data) DO UPDATE SET agua = ?", (usuario_ativo, data_hoje, agua_atual, passos_atual, agua_atual))
                conn.commit()
            st.rerun()

    with col2:
        st.subheader("🚶 Passos Diários")
        st.metric("Total Hoje", f"{passos_atual} / 10000 passos")
        st.progress(min(passos_atual / 10000, 1.0))
        
        add_p = st.number_input("Adicionar passos:", min_value=0, step=500)
        if st.button("Registrar Passos", use_container_width=True):
            passos_atual += add_p
            with get_connection() as conn:
                conn.cursor().execute("INSERT INTO registros_diarios (nome, data, agua, passos) VALUES (?, ?, ?, ?) ON CONFLICT(nome, data) DO UPDATE SET passos = ?", (usuario_ativo, data_hoje, agua_atual, passos_atual, passos_atual))
                conn.commit()
            st.rerun()

# --- 4. METAS & HÁBITOS ---
elif menu == "✅ Metas & Hábitos":
    st.title(f"✅ Hábitos Diários — {usuario_ativo}")
    
    c1, c2 = st.columns([3, 1])
    novo_h = c1.text_input("Criar Hábito:")
    if c2.button("Adicionar", use_container_width=True) and novo_h.strip():
        try:
            with get_connection() as conn:
                conn.cursor().execute("INSERT INTO habitos (nome, habito, status) VALUES (?, ?, 0)", (usuario_ativo, novo_h.strip()))
                conn.commit()
            st.rerun()
        except:
            st.warning("Hábito já existe.")

    st.markdown("---")
    with get_connection() as conn:
        df_h = pd.read_sql_query("SELECT habito, status FROM habitos WHERE nome = ?", conn, params=(usuario_ativo,))

    if not df_h.empty:
        for idx, row in df_h.iterrows():
            chk = st.checkbox(row['habito'], value=bool(row['status']), key=f"hb_{idx}")
            if chk != bool(row['status']):
                with get_connection() as conn:
                    conn.cursor().execute("UPDATE habitos SET status = ? WHERE nome = ? AND habito = ?", (int(chk), usuario_ativo, row['habito']))
                    conn.commit()
                st.rerun()

# --- 5. HISTÓRICO EVOLUTIVO ---
elif menu == "📈 Histórico Evolutivo":
    st.title(f"📈 Gráficos de Evolução — {usuario_ativo}")
    
    with get_connection() as conn:
        df_hist = pd.read_sql_query("SELECT data as Data, peso as Peso, imc as IMC FROM historico WHERE nome = ? ORDER BY id ASC", conn, params=(usuario_ativo,))

    if not df_hist.empty:
        st.dataframe(df_hist, use_container_width=True)
        fig = px.line(df_hist, x='Data', y='IMC', title="Evolução do IMC", markers=True)
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum histórico disponível.")
