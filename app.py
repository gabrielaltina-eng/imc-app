import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="IMC+ | Health & Fitness Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Personalizada
st.markdown("""
    <style>
    .main { padding: 1.5rem; }
    .stMetric {
        background-color: #1e222d;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .css-card {
        background-color: #1a1c23;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# BANCO DE DADOS
def conectar():
    return sqlite3.connect("imc_plus_web.db")

def criar_tabelas():
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

criar_tabelas()

# LÓGICA
def calcular_imc(peso, altura):
    return peso / (altura ** 2) if altura > 0 else 0

def classificar_imc(imc):
    if imc < 18.5: return "Abaixo do peso", "warning"
    elif 18.5 <= imc < 25.0: return "Peso Normal", "success"
    elif 25.0 <= imc < 30.0: return "Sobrepeso", "warning"
    elif 30.0 <= imc < 35.0: return "Obesidade Grau I", "error"
    elif 35.0 <= imc < 40.0: return "Obesidade Grau II", "error"
    else: return "Obesidade Grau III", "error"

# SIDEBAR
st.sidebar.title("⚡ IMC+ Analytics")

conn = conectar()
usuarios_db = pd.read_sql_query("SELECT nome FROM usuarios", conn)['nome'].tolist()
conn.close()

if not usuarios_db:
    usuario_atual = "Convidado"
    st.sidebar.warning("⚠️ Crie seu perfil na aba 'Meu Perfil'")
else:
    usuario_atual = st.sidebar.selectbox("👤 Perfil Ativo:", usuarios_db)

menu = st.sidebar.radio(
    "Navegação",
    ["📊 Dashboard IMC", "💧 Água & Passos", "✅ Hábitos", "🥗 Nutrição", "💡 Dicas", "🏋️ Treinos", "👤 Perfil", "📈 Histórico"]
)

# 1. DASHBOARD IMC
if menu == "📊 Dashboard IMC":
    st.title("📊 Dashboard de Saúde & IMC")
    
    conn = conectar()
    user_info = pd.read_sql_query("SELECT * FROM usuarios WHERE nome = ?", conn, params=(usuario_atual,))
    hist_info = pd.read_sql_query("SELECT * FROM historico WHERE LOWER(nome) = LOWER(?) ORDER BY id DESC LIMIT 2", conn, params=(usuario_atual,))
    conn.close()
    
    altura_padrao = float(user_info['altura'].iloc[0]) if not user_info.empty else 1.70
    
    # KPIs Inteligentes
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    
    peso_atual = hist_info['peso'].iloc[0] if not hist_info.empty else 70.0
    imc_atual = hist_info['imc'].iloc[0] if not hist_info.empty else 24.2
    
    delta_peso = 0.0
    if len(hist_info) > 1:
        delta_peso = hist_info['peso'].iloc[0] - hist_info['peso'].iloc[1]
        
    col_kpi1.metric("Peso Atual", f"{peso_atual:.1f} kg", delta=f"{delta_peso:.1f} kg", delta_color="inverse")
    col_kpi2.metric("IMC Atual", f"{imc_atual:.2f}")
    
    class_nome, class_tipo = classificar_imc(imc_atual)
    col_kpi3.metric("Status Corporal", class_nome)

    st.divider()

    # Form de Cálculo
    c1, c2 = st.columns(2)
    with c1:
        novo_peso = st.number_input("Digite seu peso atual (kg):", min_value=1.0, max_value=300.0, value=float(peso_atual), step=0.1)
    with c2:
        nova_altura = st.number_input("Sua altura (m):", min_value=0.5, max_value=2.5, value=float(altura_padrao), step=0.01)

    if st.button("🚀 Registrar Nova Medição", type="primary", use_container_width=True):
        imc = calcular_imc(novo_peso, nova_altura)
        class_texto, status_cor = classificar_imc(imc)
        data_hoje = datetime.today().strftime('%Y-%m-%d %H:%M')
        
        if usuario_atual != "Convidado":
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO historico (nome, data, peso, imc, classificacao) VALUES (?, ?, ?, ?, ?)",
                           (usuario_atual, data_hoje, novo_peso, imc, class_texto))
            conn.commit()
            conn.close()
            st.success(f"Excelente! IMC de {imc:.2f} ({class_texto}) registrado com sucesso!")
            st.rerun()

# 2. ÁGUA E PASSOS
elif menu == "💧 Água & Passos":
    st.title("💧 Meta Diária de Hidratação & Atividades")
    data_hoje = datetime.today().strftime('%Y-%m-%d')
    
    conn = conectar()
    user_info = pd.read_sql_query("SELECT meta_agua, meta_passos FROM usuarios WHERE nome = ?", conn, params=(usuario_atual,))
    reg_info = pd.read_sql_query("SELECT agua, passos FROM registros_diarios WHERE nome = ? AND data = ?", conn, params=(usuario_atual, data_hoje))
    conn.close()
    
    meta_agua = int(user_info['meta_agua'].iloc[0]) if not user_info.empty else 2000
    meta_passos = int(user_info['meta_passos'].iloc[0]) if not user_info.empty else 8000
    
    agua_atual = int(reg_info['agua'].iloc[0]) if not reg_info.empty else 0
    passos_atuais = int(reg_info['passos'].iloc[0]) if not reg_info.empty else 0
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💧 Consumo de Água")
        st.metric("Total Hoje", f"{agua_atual} / {meta_agua} ml")
        st.progress(min(agua_atual / meta_agua, 1.0))
        
        ca, cb = st.columns(2)
        if ca.button("+250 ml", use_container_width=True): agua_atual += 250
        if cb.button("+500 ml", use_container_width=True): agua_atual += 500
                
    with col2:
        st.subheader("🚶 Passos")
        st.metric("Total Hoje", f"{passos_atuais} / {meta_passos} passos")
        st.progress(min(passos_atuais / meta_passos, 1.0))
        
        n_passos = st.number_input("Adicionar passos:", min_value=0, step=500)
        if st.button("Registrar Passos", use_container_width=True):
            passos_atuais += n_passos

    if usuario_atual != "Convidado":
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO registros_diarios (nome, data, agua, passos) VALUES (?, ?, ?, ?)
            ON CONFLICT(nome, data) DO UPDATE SET agua=?, passos=?
        """, (usuario_atual, data_hoje, agua_atual, passos_atuais, agua_atual, passos_atuais))
        conn.commit()
        conn.close()

# 3. HÁBITOS
elif menu == "✅ Hábitos":
    st.title("✅ Metas & Hábitos Diários")
    
    c1, c2 = st.columns([3, 1])
    novo_h = c1.text_input("Definir novo hábito:")
    if c2.button("Adicionar", use_container_width=True) and novo_h and usuario_atual != "Convidado":
        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO habitos (nome, habito, status) VALUES (?, ?, 0)", (usuario_atual, novo_h))
            conn.commit()
        except: st.warning("Já existe este hábito.")
        conn.close()
        st.rerun()

    st.divider()
    if usuario_atual != "Convidado":
        conn = conectar()
        df_h = pd.read_sql_query("SELECT habito, status FROM habitos WHERE nome = ?", conn, params=(usuario_atual,))
        conn.close()
        
        for idx, row in df_h.iterrows():
            chk = st.checkbox(row['habito'], value=bool(row['status']), key=f"h_{idx}")
            if chk != bool(row['status']):
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("UPDATE habitos SET status = ? WHERE nome = ? AND habito = ?", (int(chk), usuario_atual, row['habito']))
                conn.commit()
                conn.close()

# 4. NUTRIÇÃO
elif menu == "🥗 Nutrição":
    st.title("🥗 Tabela Nutricional")
    dados = {
        "Alimento": ["Arroz Branco Cozido (100g)", "Feijão Preto (100g)", "Peito de Frango Grelhado (100g)", "Ovo Cozido (1 un)", "Banana Prata (1 un)"],
        "Calorias (kcal)": [130, 77, 165, 78, 98],
        "Carboidratos (g)": [28.0, 14.0, 0.0, 0.6, 23.0],
        "Proteínas (g)": [2.5, 4.5, 31.0, 6.3, 1.3],
        "Gorduras (g)": [0.2, 0.5, 3.6, 5.3, 0.1]
    }
    df = pd.DataFrame(dados)
    busca = st.text_input("🔍 Buscar alimento...")
    if busca:
        df = df[df['Alimento'].str.contains(busca, case=False)]
    st.dataframe(df, use_container_width=True)

# 5. DICAS
elif menu == "💡 Dicas":
    st.title("💡 Guias Rápidos de Saúde")
    st.info("💧 **Água:** Calcule de 35ml a 40ml de água por quilo corporal por dia.")
    st.success("🥗 **Nutrição:** Mantenha pelo menos metade do seu prato coberto por vegetais e legumes.")
    st.warning("😴 **Sono:** Sono desregulado aumenta a produção do hormônio do estresse (Cortisol).")

# 6. TREINOS
elif menu == "🏋️ Treinos":
    st.title("🏋️ Sugestão de Treino Semanal")
    st.markdown("""
    * **Segunda/Quinta:** Treino de Força (Membros Superiores) + 20min Cardio.
    * **Terça/Sexta:** Treino de Força (Membros Inferiores) + Mobilidade.
    * **Quarta/Sábado:** Caminhada moderada / Corrida de rua (45min).
    """)

# 7. PERFIL
elif menu == "👤 Perfil":
    st.title("👤 Configuração do Perfil")
    nome = st.text_input("Nome completo:")
    idade = st.number_input("Idade:", min_value=1, max_value=120, value=25)
    altura = st.number_input("Altura (m):", min_value=0.5, max_value=2.5, value=1.70, step=0.01)
    
    if st.button("Salvar Perfil", type="primary"):
        if nome:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO usuarios (nome, idade, altura) VALUES (?, ?, ?)
                ON CONFLICT(nome) DO UPDATE SET idade=?, altura=?
            """, (nome, idade, altura, idade, altura))
            conn.commit()
            conn.close()
            st.success("Perfil atualizado! Selecione-o na barra lateral.")
            st.rerun()

# 8. HISTÓRICO
elif menu == "📈 Histórico":
    st.title("📈 Evolução e Histórico")
    conn = conectar()
    df_h = pd.read_sql_query("SELECT data as Data, peso as 'Peso (kg)', imc as IMC, classificacao as Classificação FROM historico WHERE LOWER(nome) = LOWER(?) ORDER BY id", conn, params=(usuario_atual,))
    conn.close()
    
    if not df_h.empty:
        st.dataframe(df_h, use_container_width=True)
        
        # Gráfico Plotly com linha de meta
        fig = px.line(df_h, x='Data', y='IMC', title='Evolução Numérica do IMC', markers=True)
        fig.add_hline(y=24.9, line_dash="dot", line_color="green", annotation_text="Meta Peso Normal (24.9)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Ainda não existem dados registrados para este perfil.")
