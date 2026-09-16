import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import hashlib

# 1. CONFIGURAÇÃO VISUAL & TEMA HIGH-TECH
st.set_page_config(
    page_title="IMC+ | Performance & Health",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ESTILO CSS AVANÇADO (DESIGN DASHBOARD PREMIUM)
st.markdown("""
<style>
    /* Fundo da Aplicação */
    .stApp {
        background-color: #0b0f19;
    }
    
    /* Cartões Métrica / KPI Cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(22, 30, 46, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        border-color: #6366f1;
        box-shadow: 0 12px 30px rgba(99, 102, 241, 0.25);
    }
    
    /* Hero Header */
    .hero-card {
        background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-left: 6px solid #6366f1;
        padding: 28px;
        border-radius: 18px;
        margin-bottom: 25px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
    }
    .hero-title {
        color: #f8fafc;
        font-size: 28px;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .hero-sub {
        color: #94a3b8;
        font-size: 15px;
        margin-top: 6px;
    }

    /* Botões Estilizados */
    div.stButton > button {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%);
        color: #ffffff !important;
        font-weight: 700;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.2rem;
        transition: all 0.3s ease-in-out;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
    }
    div.stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
    }

    /* Abas de Formulário */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        background-color: #1e293b;
        color: #94a3b8;
    }
    .stTabs [aria-selected="true"] {
        background-color: #6366f1 !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# 2. BANCO DE DADOS
DB_NAME = "imc_plus_v9.db"

def get_connection():
    return sqlite3.connect(DB_NAME, timeout=10, check_same_thread=False)

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                idade INTEGER,
                altura REAL,
                peso_inicial REAL
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

# CÁLCULOS BIOMÉTRICOS
def calcular_imc(peso, altura):
    return peso / (altura ** 2) if altura > 0 else 0

def classificar_imc(imc):
    if imc < 18.5: return "Abaixo do peso"
    elif 18.5 <= imc < 25.0: return "Peso Normal"
    elif 25.0 <= imc < 30.0: return "Sobrepeso"
    elif 30.0 <= imc < 35.0: return "Obesidade I"
    elif 35.0 <= imc < 40.0: return "Obesidade II"
    else: return "Obesidade III"

# 3. CONTROLE DE SESSÃO / TELA DE LOGIN & CADASTRO
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

if not st.session_state.usuario_logado:
    st.markdown("""
        <div style="text-align: center; padding: 40px 0;">
            <h1 style="color: #6366f1; font-size: 42px; font-weight: 900; margin-bottom: 0;">⚡ IMC+ Analytics</h1>
            <p style="color: #94a3b8; font-size: 18px;">Seu painel de inteligência em saúde e treino</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_centered = st.columns([1, 2, 1])[1]
    
    with col_centered:
        tab_login, tab_cadastro = st.tabs(["🔑 Entrar na Conta", "📝 Criar Nova Conta"])
        
        with tab_login:
            with st.form("form_login"):
                usuario_input = st.text_input("Usuário / Nome:")
                senha_input = st.text_input("Senha:", type="password")
                btn_entrar = st.form_submit_button("Entrar no Dashboard", type="primary", use_container_width=True)
                
                if btn_entrar:
                    nome_limpo = usuario_input.strip()
                    if nome_limpo and senha_input:
                        senha_hash = hash_senha(senha_input)
                        with get_connection() as conn:
                            res = pd.read_sql_query("SELECT * FROM usuarios WHERE LOWER(nome) = LOWER(?) AND senha = ?", 
                                                    conn, params=(nome_limpo, senha_hash))
                        if not res.empty:
                            user_real = res['nome'].iloc[0]
                            st.session_state.usuario_logado = user_real
                            st.success("Login efetuado com sucesso!")
                            st.rerun()
                        else:
                            st.error("Usuário ou senha incorretos!")
                    else:
                        st.warning("Preencha todos os campos para entrar.")
                        
        with tab_cadastro:
            with st.form("form_cadastro"):
                novo_u = st.text_input("Nome de Usuário:")
                nova_s = st.text_input("Defina uma Senha:", type="password")
                
                c_cad1, c_cad2, c_cad3 = st.columns(3)
                peso_u = c_cad1.number_input("Peso (kg):", 1.0, 300.0, 70.0, step=0.1)
                alt_u = c_cad2.number_input("Altura (m):", 0.50, 2.50, 1.70, step=0.01)
                idade_u = c_cad3.number_input("Idade:", 1, 120, 25)
                
                btn_cadastrar = st.form_submit_button("Criar Conta e Entrar", type="primary", use_container_width=True)
                
                if btn_cadastrar:
                    nome_cad = novo_u.strip()
                    if nome_cad and nova_s:
                        with get_connection() as conn:
                            ja_existe = pd.read_sql_query("SELECT id FROM usuarios WHERE LOWER(nome) = LOWER(?)", conn, params=(nome_cad,))
                        
                        if not ja_existe.empty:
                            st.error("⚠️ Este nome de usuário já está em uso! Escolha outro nome.")
                        else:
                            senha_hash = hash_senha(nova_s)
                            imc_inicial = calcular_imc(peso_u, alt_u)
                            diag_inicial = classificar_imc(imc_inicial)
                            data_agora = datetime.now().strftime('%d/%m/%Y %H:%M')
                            
                            with get_connection() as conn:
                                cur = conn.cursor()
                                # Salva usuário
                                cur.execute("INSERT INTO usuarios (nome, senha, idade, altura, peso_inicial) VALUES (?,?,?,?,?)", 
                                            (nome_cad, senha_hash, idade_u, alt_u, peso_u))
                                # Registra primeiro histórico de peso/IMC
                                cur.execute("INSERT INTO historico (nome, data, peso, imc, classificacao) VALUES (?,?,?,?,?)",
                                            (nome_cad, data_agora, peso_u, imc_inicial, diag_inicial))
                                conn.commit()
                                
                            st.success("Conta criada com sucesso! Vá até a aba 'Entrar na Conta'.")
                    else:
                        st.warning("Preencha o nome de usuário e a senha.")
    st.stop()

# --- USUÁRIO AUTENTICADO ---
usuario_ativo = st.session_state.usuario_logado

st.sidebar.title("⚡ IMC+ Performance")
st.sidebar.success(f"Conectado como: **{usuario_ativo}**")

if st.sidebar.button("🚪 Sair (Logout)", use_container_width=True):
    st.session_state.usuario_logado = None
    st.rerun()

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
            <div class="hero-sub">Visão geral do seu estado físico e evolução biométrica em tempo real</div>
        </div>
    """, unsafe_allow_html=True)

    with get_connection() as conn:
        df_h = pd.read_sql_query("SELECT * FROM historico WHERE nome = ? ORDER BY id DESC", conn, params=(usuario_ativo,))

    peso_atual = df_h['peso'].iloc[0] if not df_h.empty else user_data['peso_inicial']
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
        st.success("Medição registrada no banco de dados!")
        st.rerun()

# --- 2. TREINOS & ATIVIDADES ---
elif menu == "🏋️ Treinos & Atividades":
    st.markdown(f"""
        <div class="hero-card">
            <div class="hero-title">Central de Treinos — {usuario_ativo}</div>
            <div class="hero-sub">Registre suas atividades diárias e monitore seu gasto calórico</div>
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
            st.success("Atividade salva no histórico!")
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
        fig = px.area(df_hist, x='Data', y='IMC', title=f"Evolução Temporal do IMC — {usuario_ativo}", markers=True)
        fig.add_hline(y=24.9, line_dash="dash", line_color="#10b981", annotation_text="Meta Peso Ideal (24.9)")
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum histórico disponível.")
