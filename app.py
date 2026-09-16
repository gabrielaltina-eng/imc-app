import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA & TEMA
st.set_page_config(
    page_title="IMC+ | Analytics & Health Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ESTILO CSS AVANÇADO (DESIGN FUTURISTA / DASHBOARD SLICK)
st.markdown("""
<style>
    /* Fundo e Container Geral */
    .stApp {
        background-color: #0b0e14;
    }
    
    /* Cartões Métrica / KPI Cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(22, 27, 38, 0.9) 0%, rgba(15, 19, 28, 0.9) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 18px 22px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        border-color: #00f2fe;
    }
    
    /* Botões Customizados */
    .stButton>button {
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        color: #000000 !important;
        font-weight: 700;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 1.2rem;
        transition: all 0.3s ease-in-out;
        box-shadow: 0 4px 15px rgba(0, 242, 254, 0.2);
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(0, 242, 254, 0.4);
    }

    /* Modificação de Cabeçalhos e Containers */
    .dashboard-header {
        background: linear-gradient(90deg, rgba(79,172,254,0.1) 0%, rgba(0,242,254,0.05) 100%);
        padding: 20px;
        border-radius: 16px;
        border-left: 5px solid #00f2fe;
        margin-bottom: 25px;
    }
</style>
""", unsafe_allow_html=True)

# 2. BANCO DE DADOS (SQLITE COMPLETO)
def conectar():
    return sqlite3.connect("imc_plus_web.db", check_same_thread=False)

def inicializar_banco():
    conn = conectar()
    cursor = conn.cursor()
    
    # Tabela de Perfis
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
    
    # Tabela de Histórico do IMC
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_nome TEXT NOT NULL,
            data TEXT NOT NULL,
            peso REAL NOT NULL,
            imc REAL NOT NULL,
            classificacao TEXT NOT NULL
        )
    """)
    
    # Tabela de Registros Diários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registros_diarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_nome TEXT NOT NULL,
            data TEXT NOT NULL,
            agua INTEGER DEFAULT 0,
            passos INTEGER DEFAULT 0,
            UNIQUE(usuario_nome, data)
        )
    """)
    
    # Tabela de Hábitos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habitos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_nome TEXT NOT NULL,
            habito TEXT NOT NULL,
            status INTEGER DEFAULT 0,
            UNIQUE(usuario_nome, habito)
        )
    """)
    
    conn.commit()
    conn.close()

inicializar_banco()

# 3. LÓGICA DE CÁLCULO
def calcular_imc(peso, altura):
    return peso / (altura ** 2) if altura > 0 else 0

def classificar_imc(imc):
    if imc < 18.5: return "Abaixo do peso"
    elif 18.5 <= imc < 25.0: return "Peso Normal"
    elif 25.0 <= imc < 30.0: return "Sobrepeso"
    elif 30.0 <= imc < 35.0: return "Obesidade Grau I"
    elif 35.0 <= imc < 40.0: return "Obesidade Grau II"
    else: return "Obesidade Grau III"

# 4. PAINEL LATERAL (GERENCIAMENTO DE PERFIL & MENU)
st.sidebar.markdown("## 👤 Gerenciador de Perfil")

conn = conectar()
lista_usuarios = pd.read_sql_query("SELECT nome FROM usuarios", conn)['nome'].tolist()
conn.close()

# Seleção ou Criação de Perfil
opcoes_perfil = ["➕ Criar Novo Perfil"] + lista_usuarios
perfil_selecionado = st.sidebar.selectbox("Selecione o Usuário Ativo:", opcoes_perfil)

if perfil_selecionado == "➕ Criar Novo Perfil":
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ✨ Cadastrar Novo Perfil")
    novo_nome = st.sidebar.text_input("Nome da Pessoa:")
    nova_idade = st.sidebar.number_input("Idade:", min_value=1, max_value=120, value=25)
    nova_altura = st.sidebar.number_input("Altura (m):", min_value=0.5, max_value=2.5, value=1.70, step=0.01)
    
    if st.sidebar.button("Criar e Entrar"):
        if novo_nome.strip():
            try:
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO usuarios (nome, idade, altura) VALUES (?, ?, ?)", (novo_nome.strip(), nova_idade, nova_altura))
                conn.commit()
                conn.close()
                st.sidebar.success(f"Perfil '{novo_nome}' criado com sucesso!")
                st.rerun()
            except:
                st.sidebar.error("Já existe um perfil com esse nome.")
        else:
            st.sidebar.warning("Digite um nome válido.")
    
    usuario_ativo = None
else:
    usuario_ativo = perfil_selecionado
    st.sidebar.success(f"Conectado como: **{usuario_ativo}**")

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navegação do Dashboard",
    ["📊 Dashboard Geral", "💧 Água & Atividade", "✅ Hábitos & Metas", "🥗 Nutrição", "📈 Histórico Evolutivo"]
)

# VERIFICAÇÃO SE O PERFIL ESTÁ SELECIONADO
if not usuario_ativo:
    st.markdown("""
        <div class="dashboard-header">
            <h2>👋 Bem-vindo ao IMC+ Analytics!</h2>
            <p>Por favor, crie um perfil no menu à esquerda para salvar seus registros e visualizar suas estatísticas personalizadas.</p>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# 5. DADOS DO USUÁRIO ATIVO
conn = conectar()
user_data = pd.read_sql_query("SELECT * FROM usuarios WHERE nome = ?", conn, params=(usuario_ativo,)).iloc[0]
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
    df_hist = pd.read_sql_query("SELECT * FROM historico WHERE usuario_nome = ? ORDER BY id DESC", conn, params=(usuario_ativo,))
    conn.close()

    peso_atual = df_hist['peso'].iloc[0] if not df_hist.empty else 70.0
    imc_atual = df_hist['imc'].iloc[0] if not df_hist.empty else calcular_imc(peso_atual, user_data['altura'])
    
    delta_peso = 0.0
    if len(df_hist) > 1:
        delta_peso = df_hist['peso'].iloc[0] - df_hist['peso'].iloc[1]

    # Cards Principais
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Peso Registrado", f"{peso_atual:.1f} kg", delta=f"{delta_peso:.1f} kg", delta_color="inverse")
    col2.metric("Altura", f"{user_data['altura']:.2f} m")
    col3.metric("IMC Atual", f"{imc_atual:.2f}")
    col4.metric("Status", classificar_imc(imc_atual))

    st.markdown("---")
    
    # Formulário de Nova Medição
    st.markdown("### 📝 Registrar Novo Peso")
    c1, c2 = st.columns(2)
    input_peso = c1.number_input("Digite o Peso Atual (kg):", min_value=1.0, max_value=300.0, value=float(peso_atual), step=0.1)
    input_altura = c2.number_input("Confirme sua Altura (m):", min_value=0.5, max_value=2.5, value=float(user_data['altura']), step=0.01)

    if st.button("🚀 Salvar Medição no Banco de Dados", use_container_width=True):
        novo_imc = calcular_imc(input_peso, input_altura)
        classif = classificar_imc(novo_imc)
        data_registro = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO historico (usuario_nome, data, peso, imc, classificacao)
            VALUES (?, ?, ?, ?, ?)
        """, (usuario_ativo, data_registro, input_peso, novo_imc, classif))
        
        # Atualiza altura se alterada
        cursor.execute("UPDATE usuarios SET altura = ? WHERE nome = ?", (input_altura, usuario_ativo))
        conn.commit()
        conn.close()
        
        st.success(f"Novo registro salvo! IMC: {novo_imc:.2f} ({classif})")
        st.rerun()

# --- 2. ÁGUA & ATIVIDADE ---
elif menu == "💧 Água & Atividade":
    st.markdown(f"## 💧 Rastreador Diário — {usuario_ativo}")
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    
    conn = conectar()
    reg_hoje = pd.read_sql_query("SELECT agua, passos FROM registros_diarios WHERE usuario_nome = ? AND data = ?", conn, params=(usuario_ativo, data_hoje))
    conn.close()

    agua_hoje = int(reg_hoje['agua'].iloc[0]) if not reg_hoje.empty else 0
    passos_hoje = int(reg_hoje['passos'].iloc[0]) if not reg_hoje.empty else 0

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚰 Consumo de Água")
        meta_agua = user_data['meta_agua']
        st.metric("Total Hoje", f"{agua_hoje} / {meta_agua} ml")
        st.progress(min(agua_hoje / meta_agua, 1.0))
        
        ca, cb = st.columns(2)
        if ca.button("+250ml Água", use_container_width=True):
            agua_hoje += 250
        if cb.button("+500ml Água", use_container_width=True):
            agua_hoje += 500

    with col2:
        st.markdown("### 🚶 Registro de Passos")
        meta_passos = user_data['meta_passos']
        st.metric("Total Hoje", f"{passos_hoje} / {meta_passos} passos")
        st.progress(min(passos_hoje / meta_passos, 1.0))
        
        add_p = st.number_input("Adicionar quantidade de passos:", min_value=0, step=500)
        if st.button("Registrar Passos", use_container_width=True):
            passos_hoje += add_p

    # Salvar automaticamente no banco
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO registros_diarios (usuario_nome, data, agua, passos)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(usuario_nome, data) DO UPDATE SET agua = ?, passos = ?
    """, (usuario_ativo, data_hoje, agua_hoje, passos_hoje, agua_hoje, passos_hoje))
    conn.commit()
    conn.close()

# --- 3. HÁBITOS & METAS ---
elif menu == "✅ Hábitos & Metas":
    st.markdown(f"## ✅ Gestão de Hábitos — {usuario_ativo}")
    
    c1, c2 = st.columns([3, 1])
    novo_h = c1.text_input("Criar novo hábito pessoal:")
    if c2.button("Adicionar Hábito", use_container_width=True) and novo_h.strip():
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO habitos (usuario_nome, habito, status) VALUES (?, ?, 0)", (usuario_ativo, novo_h.strip()))
            conn.commit()
            conn.close()
            st.rerun()
        except:
            st.warning("Este hábito já está na sua lista.")

    st.markdown("---")
    conn = conectar()
    df_habitos = pd.read_sql_query("SELECT habito, status FROM habitos WHERE usuario_nome = ?", conn, params=(usuario_ativo,))
    conn.close()

    if not df_habitos.empty:
        for idx, row in df_habitos.iterrows():
            chk = st.checkbox(row['habito'], value=bool(row['status']), key=f"hab_{usuario_ativo}_{idx}")
            if chk != bool(row['status']):
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("UPDATE habitos SET status = ? WHERE usuario_nome = ? AND habito = ?", (int(chk), usuario_ativo, row['habito']))
                conn.commit()
                conn.close()
                st.rerun()
    else:
        st.info("Nenhum hábito cadastrado para este perfil.")

# --- 4. NUTRIÇÃO ---
elif menu == "🥗 Nutrição":
    st.markdown("## 🥗 Consulta de Alimentos & Calorias")
    
    alimentos_data = {
        "Alimento": ["Peito de Frango Grelhado (100g)", "Arroz Integral (100g)", "Ovo Cozido (1 un)", "Banana Prata (1 un)", "Feijão Preto (100g)", "Aveia (30g)"],
        "Calorias (kcal)": [165, 124, 78, 98, 77, 117],
        "Proteínas (g)": [31.0, 2.6, 6.3, 1.3, 4.5, 4.3],
        "Carboidratos (g)": [0.0, 25.8, 0.6, 23.0, 14.0, 17.0],
        "Gorduras (g)": [3.6, 1.0, 5.3, 0.1, 0.5, 2.3]
    }
    df_nutri = pd.DataFrame(alimentos_data)
    busca = st.text_input("🔍 Pesquisar alimento:")
    if busca:
        df_nutri = df_nutri[df_nutri['Alimento'].str.contains(busca, case=False)]
    st.dataframe(df_nutri, use_container_width=True)

# --- 5. HISTÓRICO EVOLUTIVO ---
elif menu == "📈 Histórico Evolutivo":
    st.markdown(f"## 📈 Histórico & Gráficos — {usuario_ativo}")
    
    conn = conectar()
    df_h = pd.read_sql_query("SELECT data as Data, peso as 'Peso (kg)', imc as IMC, classificacao as Classificação FROM historico WHERE usuario_nome = ? ORDER BY id ASC", conn, params=(usuario_ativo,))
    conn.close()

    if not df_h.empty:
        st.dataframe(df_h, use_container_width=True)
        
        # Gráfico Animado Interativo Plotly
        fig = px.area(
            df_h, x='Data', y='IMC', 
            title=f"Evolução Corporal de {usuario_ativo}",
            markers=True,
            color_discrete_sequence=['#00f2fe']
        )
        fig.add_hline(y=24.9, line_dash="dash", line_color="#00ff88", annotation_text="Limite Peso Ideal (24.9)")
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#ffffff")
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Ainda não há histórico registrado para este perfil. Faça medições no Dashboard Geral!")
