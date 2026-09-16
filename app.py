import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="IMC+ | Health Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS
st.markdown("""
<style>
    .stApp { background-color: #0b0e14; }
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 15px;
    }
    .dashboard-header {
        background: linear-gradient(90deg, rgba(79,172,254,0.1) 0%, rgba(0,242,254,0.05) 100%);
        padding: 20px;
        border-radius: 16px;
        border-left: 5px solid #00f2fe;
        margin-bottom: 25px;
    }
</style>
""", unsafe_allow_html=True)

# 2. BANCO DE DADOS
def conectar():
    return sqlite3.connect("imc_plus_final.db", check_same_thread=False)

def inicializar_banco():
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            idade INTEGER,
            altura REAL,
            meta_agua INTEGER DEFAULT 2000,
            meta_passos INTEGER DEFAULT 8000
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

    # TABELA QUE FALTAVA PARA SALVAR AS ATIVIDADES
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
    conn.close()

inicializar_banco()

# CÁLCULOS
def calcular_imc(peso, altura):
    return peso / (altura ** 2) if altura > 0 else 0

def classificar_imc(imc):
    if imc < 18.5: return "Abaixo do peso"
    elif 18.5 <= imc < 25.0: return "Peso Normal"
    elif 25.0 <= imc < 30.0: return "Sobrepeso"
    elif 30.0 <= imc < 35.0: return "Obesidade Grau I"
    elif 35.0 <= imc < 40.0: return "Obesidade Grau II"
    else: return "Obesidade Grau III"

# 3. GERENCIADOR DE PERFIL
st.sidebar.title("👤 Gerenciador de Perfil")

conn = conectar()
try:
    lista_usuarios = pd.read_sql_query("SELECT nome FROM usuarios", conn)['nome'].tolist()
except Exception:
    lista_usuarios = []
conn.close()

if not lista_usuarios:
    st.sidebar.warning("Nenhum perfil cadastrado.")
    novo_nome = st.sidebar.text_input("Criar Primeiro Usuário:")
    nova_idade = st.sidebar.number_input("Idade:", min_value=1, max_value=120, value=25)
    nova_altura = st.sidebar.number_input("Altura (m):", min_value=0.5, max_value=2.5, value=1.70, step=0.01)
    
    if st.sidebar.button("Criar Usuário", type="primary"):
        if novo_nome.strip():
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO usuarios (nome, idade, altura) VALUES (?, ?, ?)", 
                           (novo_nome.strip(), nova_idade, nova_altura))
            conn.commit()
            conn.close()
            st.rerun()
    st.stop()

usuario_ativo = st.sidebar.selectbox("Selecione o Usuário Ativo:", lista_usuarios)

st.sidebar.success(f"Conectado como: **{usuario_ativo}**")

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navegação do Dashboard",
    ["📊 Dashboard Geral", "💧 Água & Atividade", "✅ Hábitos & Metas", "🥗 Nutrição", "📈 Histórico Evolutivo"]
)

conn = conectar()
user_info = pd.read_sql_query("SELECT * FROM usuarios WHERE nome = ?", conn, params=(usuario_ativo,)).iloc[0]
conn.close()

# --- 1. DASHBOARD GERAL ---
if menu == "📊 Dashboard Geral":
    st.markdown(f"""
        <div class="dashboard-header">
            <h2>⚡ Analytics Corporal: {usuario_ativo}</h2>
            <p>Acompanhe suas métricas de saúde em tempo real.</p>
        </div>
    """, unsafe_allow_html=True)

    conn = conectar()
    df_hist = pd.read_sql_query("SELECT * FROM historico WHERE nome = ? ORDER BY id DESC", conn, params=(usuario_ativo,))
    conn.close()

    peso_atual = df_hist['peso'].iloc[0] if not df_hist.empty else 70.0
    imc_atual = df_hist['imc'].iloc[0] if not df_hist.empty else calcular_imc(peso_atual, user_info['altura'])
    
    delta_peso = 0.0
    if len(df_hist) > 1:
        delta_peso = df_hist['peso'].iloc[0] - df_hist['peso'].iloc[1]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Peso Atual", f"{peso_atual:.1f} kg", delta=f"{delta_peso:.1f} kg", delta_color="inverse")
    col2.metric("Altura", f"{user_info['altura']:.2f} m")
    col3.metric("IMC Atual", f"{imc_atual:.2f}")
    col4.metric("Status", classificar_imc(imc_atual))

    st.markdown("---")
    st.markdown("### 📝 Registrar Peso")
    
    c1, c2 = st.columns(2)
    in_peso = c1.number_input("Peso Atual (kg):", min_value=1.0, max_value=300.0, value=float(peso_atual), step=0.1)
    in_altura = c2.number_input("Altura (m):", min_value=0.5, max_value=2.5, value=float(user_info['altura']), step=0.01)

    if st.button("Salvar Medição", type="primary", use_container_width=True):
        novo_imc = calcular_imc(in_peso, in_altura)
        classif = classificar_imc(novo_imc)
        data_hoje = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO historico (nome, data, peso, imc, classificacao) VALUES (?, ?, ?, ?, ?)",
                       (usuario_ativo, data_hoje, in_peso, novo_imc, classif))
        cursor.execute("UPDATE usuarios SET altura = ? WHERE nome = ?", (in_altura, usuario_ativo))
        conn.commit()
        conn.close()
        st.success("Medição registrada!")
        st.rerun()

# --- 2. ÁGUA & ATIVIDADE ---
elif menu == "💧 Água & Atividade":
    st.title(f"💧 Água & Atividades — {usuario_ativo}")
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    
    conn = conectar()
    reg = pd.read_sql_query("SELECT agua, passos FROM registros_diarios WHERE nome = ? AND data = ?", conn, params=(usuario_ativo, data_hoje))
    conn.close()

    agua_hoje = int(reg['agua'].iloc[0]) if not reg.empty else 0
    passos_hoje = int(reg['passos'].iloc[0]) if not reg.empty else 0

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🚰 Água")
        st.metric("Hoje", f"{agua_hoje} ml")
        ca, cb = st.columns(2)
        if ca.button("+250 ml", use_container_width=True):
            agua_hoje += 250
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO registros_diarios (nome, data, agua, passos) VALUES (?, ?, ?, ?) ON CONFLICT(nome, data) DO UPDATE SET agua = ?", (usuario_ativo, data_hoje, agua_hoje, passos_hoje, agua_hoje))
            conn.commit()
            conn.close()
            st.rerun()
            
        if cb.button("+500 ml", use_container_width=True):
            agua_hoje += 500
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO registros_diarios (nome, data, agua, passos) VALUES (?, ?, ?, ?) ON CONFLICT(nome, data) DO UPDATE SET agua = ?", (usuario_ativo, data_hoje, agua_hoje, passos_hoje, agua_hoje))
            conn.commit()
            conn.close()
            st.rerun()

    with col2:
        st.subheader("🚶 Passos")
        st.metric("Hoje", f"{passos_hoje} passos")
        add_p = st.number_input("Adicionar passos:", min_value=0, step=500)
        if st.button("Salvar Passos", use_container_width=True):
            passos_hoje += add_p
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO registros_diarios (nome, data, agua, passos) VALUES (?, ?, ?, ?) ON CONFLICT(nome, data) DO UPDATE SET passos = ?", (usuario_ativo, data_hoje, agua_hoje, passos_hoje, passos_hoje))
            conn.commit()
            conn.close()
            st.rerun()

    st.markdown("---")
    
    # FORMULÁRIO EXATO DA SUA IMAGEM
    nome_atv = st.text_input("Nome da Atividade:", placeholder="Ex: Caminhada, Corrida, Musculação")
    cat_atv = st.selectbox("Categoria", ["Cardio", "Musculação", "Esportes", "Funcional"])
    int_atv = st.select_slider("Intensidade", options=["Leve", "Moderada", "Intensa"], value="Intensa")
    dur_atv = st.number_input("Duração (Minutos)", min_value=1, max_value=300, value=30)
    cal_atv = st.number_input("Calorias Gastas Aprox. (kcal)", min_value=0, max_value=3000, value=150)

    # BOTÃO SALVAR ATIVIDADE CORRIGIDO
    if st.button("Salvar Atividade"):
        nome_final = nome_atv.strip() if nome_atv.strip() else cat_atv
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO atividades (nome, data, atividade, categoria, intensidade, duracao, calorias)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (usuario_ativo, data_hoje, nome_final, cat_atv, int_atv, dur_atv, cal_atv))
        conn.commit()
        conn.close()
        st.success("Atividade salva no banco de dados!")
        st.rerun()

# --- 3. HÁBITOS & METAS ---
elif menu == "✅ Hábitos & Metas":
    st.title(f"✅ Hábitos — {usuario_ativo}")
    c1, c2 = st.columns([3, 1])
    novo_h = c1.text_input("Criar novo hábito:")
    if c2.button("Adicionar", use_container_width=True) and novo_h.strip():
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO habitos (nome, habito, status) VALUES (?, ?, 0)", (usuario_ativo, novo_h.strip()))
            conn.commit()
            conn.close()
            st.rerun()
        except Exception:
            pass

    conn = conectar()
    df_h = pd.read_sql_query("SELECT habito, status FROM habitos WHERE nome = ?", conn, params=(usuario_ativo,))
    conn.close()

    if not df_h.empty:
        for idx, row in df_h.iterrows():
            chk = st.checkbox(row['habito'], value=bool(row['status']), key=f"hb_{idx}")
            if chk != bool(row['status']):
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("UPDATE habitos SET status = ? WHERE nome = ? AND habito = ?", (int(chk), usuario_ativo, row['habito']))
                conn.commit()
                conn.close()
                st.rerun()

# --- 4. NUTRIÇÃO ---
elif menu == "🥗 Nutrição":
    st.title("🥗 Nutrição")
    dados = {
        "Alimento": ["Peito de Frango (100g)", "Arroz Cozido (100g)", "Ovo Cozido (1 un)"],
        "Calorias (kcal)": [165, 130, 78],
        "Proteínas (g)": [31.0, 2.5, 6.3]
    }
    st.dataframe(pd.DataFrame(dados), use_container_width=True)

# --- 5. HISTÓRICO EVOLUTIVO ---
elif menu == "📈 Histórico Evolutivo":
    st.title(f"📈 Histórico — {usuario_ativo}")
    conn = conectar()
    df_hist = pd.read_sql_query("SELECT data as Data, peso as 'Peso (kg)', imc as IMC FROM historico WHERE nome = ?", conn, params=(usuario_ativo,))
    conn.close()

    if not df_hist.empty:
        st.dataframe(df_hist, use_container_width=True)
