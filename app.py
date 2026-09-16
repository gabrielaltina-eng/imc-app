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

# 2. BANCO DE DADOS COMPLETO
def conectar():
    return sqlite3.connect("imc_plus_v4.db", check_same_thread=False)

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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS atividades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            data TEXT NOT NULL,
            atividade TEXT NOT NULL,
            categoria TEXT NOT NULL,
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

# 3. SIDEBAR / PERFIS
st.sidebar.title("👤 Perfis do Sistema")

conn = conectar()
try:
    lista_usuarios = pd.read_sql_query("SELECT nome FROM usuarios", conn)['nome'].tolist()
except Exception:
    lista_usuarios = []
conn.close()

aba_perfil = st.sidebar.radio("Opção:", ["Selecionar Perfil", "Criar Novo Perfil"])

usuario_ativo = None

if aba_perfil == "Criar Novo Perfil":
    st.sidebar.markdown("---")
    novo_nome = st.sidebar.text_input("Nome:")
    nova_idade = st.sidebar.number_input("Idade:", min_value=1, max_value=120, value=25)
    nova_altura = st.sidebar.number_input("Altura (m):", min_value=0.5, max_value=2.5, value=1.70, step=0.01)
    
    if st.sidebar.button("Salvar Perfil", type="primary"):
        nome_limpo = novo_nome.strip()
        if nome_limpo:
            try:
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO usuarios (nome, idade, altura) VALUES (?, ?, ?)", 
                               (nome_limpo, nova_idade, nova_altura))
                conn.commit()
                conn.close()
                st.sidebar.success(f"Perfil '{nome_limpo}' cadastrado!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.sidebar.error("Perfil já existente com este nome.")
            except Exception as e:
                st.sidebar.error(f"Erro no banco: {e}")
        else:
            st.sidebar.warning("Digite um nome válido.")
else:
    if lista_usuarios:
        usuario_ativo = st.sidebar.selectbox("Conectado como:", lista_usuarios)
    else:
        st.sidebar.info("Crie um perfil para iniciar.")

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navegação",
    ["📊 Dashboard Geral", "💧 Água & Atividade", "✅ Hábitos & Metas", "🥗 Nutrição", "📈 Histórico Evolutivo"]
)

# BLOQUEIO DE TELA SEM USUÁRIO
if not usuario_ativo:
    st.markdown("""
        <div class="dashboard-header">
            <h2>👋 Bem-vindo ao IMC+ Web!</h2>
            <p>Selecione <b>'Criar Novo Perfil'</b> na barra lateral para começar.</p>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# DADOS DO USUÁRIO CONECTADO
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
    st.markdown("### 📝 Adicionar Medição")
    
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
    st.title(f"💧 Registros e Atividades — {usuario_ativo}")
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    
    conn = conectar()
    reg = pd.read_sql_query("SELECT agua, passos FROM registros_diarios WHERE nome = ? AND data = ?", conn, params=(usuario_ativo, data_hoje))
    conn.close()

    agua_hoje = int(reg['agua'].iloc[0]) if not reg.empty else 0
    passos_hoje = int(reg['passos'].iloc[0]) if not reg.empty else 0

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚰 Consumo de Água")
        meta_a = user_info['meta_agua']
        st.metric("Total Hoje", f"{agua_hoje} / {meta_a} ml")
        st.progress(min(agua_hoje / meta_a, 1.0))
        
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
        st.subheader("🚶 Passos Diários")
        meta_p = user_info['meta_passos']
        st.metric("Total Hoje", f"{passos_hoje} / {meta_p} passos")
        st.progress(min(passos_hoje / meta_p, 1.0))
        
        add_p = st.number_input("Adicionar passos:", min_value=0, step=500)
        if st.button("Registrar Passos", use_container_width=True):
            passos_hoje += add_p
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO registros_diarios (nome, data, agua, passos) VALUES (?, ?, ?, ?) ON CONFLICT(nome, data) DO UPDATE SET passos = ?", (usuario_ativo, data_hoje, agua_hoje, passos_hoje, passos_hoje))
            conn.commit()
            conn.close()
            st.rerun()

    st.markdown("---")
    st.subheader("🏋️ Registrar Atividade Física")

    nome_atv = st.text_input("Nome da Atividade (ex: Corrida, Musculação):")
    cat_atv = st.selectbox("Categoria", ["Cardio", "Musculação", "Esportes", "Funcional", "Outro"])
    dur_atv = st.number_input("Duração (Minutos)", min_value=1, max_value=300, value=30)
    cal_atv = st.number_input("Calorias Gastas Aprox. (kcal)", min_value=0, max_value=3000, value=150)

    if st.button("Salvar Atividade", type="primary"):
        if nome_atv.strip():
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO atividades (nome, data, atividade, categoria, duracao, calorias) VALUES (?, ?, ?, ?, ?, ?)",
                           (usuario_ativo, data_hoje, nome_atv.strip(), cat_atv, dur_atv, cal_atv))
            conn.commit()
            conn.close()
            st.success(f"Atividade '{nome_atv}' salva!")
            st.rerun()
        else:
            st.warning("Informe o nome da atividade.")

    # HISTÓRICO DE ATIVIDADES
    conn = conectar()
    df_atv = pd.read_sql_query("SELECT data as Data, atividade as Atividade, categoria as Categoria, duracao as 'Duração (min)', calorias as 'Calorias (kcal)' FROM atividades WHERE nome = ? ORDER BY id DESC", conn, params=(usuario_ativo,))
    conn.close()

    if not df_atv.empty:
        st.markdown("### 📋 Treinos Registrados")
        st.dataframe(df_atv, use_container_width=True)

# --- 3. HÁBITOS & METAS ---
elif menu == "✅ Hábitos & Metas":
    st.title(f"✅ Gerenciador de Hábitos — {usuario_ativo}")
    
    c1, c2 = st.columns([3, 1])
    novo_h = c1.text_input("Criar novo hábito:")
    if c2.button("Adicionar Hábito", use_container_width=True) and novo_h.strip():
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO habitos (nome, habito, status) VALUES (?, ?, 0)", (usuario_ativo, novo_h.strip()))
            conn.commit()
            conn.close()
            st.rerun()
        except Exception:
            st.warning("Hábito já cadastrado.")

    st.markdown("---")
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
    st.title("🥗 Tabela de Alimentos & Calorias")
    
    dados = {
        "Alimento": ["Peito de Frango Grelhado (100g)", "Arroz Branco Cozido (100g)", "Ovo Cozido (1 un)", "Banana Prata (1 un)", "Feijão Preto (100g)"],
        "Calorias (kcal)": [165, 130, 78, 98, 77],
        "Proteínas (g)": [31.0, 2.5, 6.3, 1.3, 4.5],
        "Carboidratos (g)": [0.0, 28.0, 0.6, 23.0, 14.0],
        "Gorduras (g)": [3.6, 0.2, 5.3, 0.1, 0.5]
    }
    df_nutri = pd.DataFrame(dados)
    busca = st.text_input("🔍 Pesquisar alimento:")
    if busca:
        df_nutri = df_nutri[df_nutri['Alimento'].str.contains(busca, case=False)]
    st.dataframe(df_nutri, use_container_width=True)

# --- 5. HISTÓRICO EVOLUTIVO ---
elif menu == "📈 Histórico Evolutivo":
    st.title(f"📈 Histórico de IMC — {usuario_ativo}")
    
    conn = conectar()
    df_hist = pd.read_sql_query("SELECT data as Data, peso as 'Peso (kg)', imc as IMC, classificacao as Classificação FROM historico WHERE nome = ? ORDER BY id ASC", conn, params=(usuario_ativo,))
    conn.close()

    if not df_hist.empty:
        st.dataframe(df_hist, use_container_width=True)
        
        fig = px.area(df_hist, x='Data', y='IMC', title=f"Evolução Temporal do IMC — {usuario_ativo}", markers=True)
        fig.add_hline(y=24.9, line_dash="dash", line_color="green", annotation_text="Meta Peso Ideal (24.9)")
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum histórico registrado para este perfil ainda.")
