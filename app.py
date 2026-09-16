import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import plotly.express as px

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(
    page_title="IMC+ • Saúde, Exercícios e Hábitos",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB = "imc_plus_web.db"

# Estilização CSS customizada para o Tema Escuro
st.markdown("""
    <style>
        .stApp {
            background-color: #07111F;
            color: #F4F7FB;
        }
        [data-testid="stSidebar"] {
            background-color: #0A1729;
        }
        div[data-testid="metric-container"] {
            background-color: #10233A;
            border: 1px solid #20304A;
            padding: 15px;
            border-radius: 15px;
        }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# BANCO DE DADOS
# =========================================================
def conectar():
    return sqlite3.connect(DB)

def auto_migrar_tabela(cursor, tabela, colunas_desejadas):
    cursor.execute(f"PRAGMA table_info({tabela})")
    colunas_existentes = [col[1] for col in cursor.fetchall()]
    if not colunas_existentes:
        defs = [f"{nome} {tipo}" for nome, tipo in colunas_desejadas]
        cursor.execute(f"CREATE TABLE {tabela} ({', '.join(defs)})")
    else:
        for nome, tipo in colunas_desejadas:
            if nome not in colunas_existentes and "PRIMARY KEY" not in tipo.upper():
                cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {nome} {tipo}")

def criar_banco():
    conn = conectar()
    cursor = conn.cursor()
    
    tabelas = {
        "historico": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("nome", "TEXT NOT NULL"),
            ("idade", "INTEGER"),
            ("peso", "REAL NOT NULL"),
            ("altura", "REAL NOT NULL"),
            ("imc", "REAL NOT NULL"),
            ("classificacao", "TEXT"),
            ("data", "TEXT NOT NULL")
        ],
        "agua": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("nome", "TEXT NOT NULL"),
            ("quantidade", "REAL NOT NULL"),
            ("data", "TEXT NOT NULL")
        ],
        "atividades": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("nome", "TEXT NOT NULL"),
            ("atividade", "TEXT NOT NULL"),
            ("categoria", "TEXT"),
            ("intensidade", "TEXT"),
            ("minutos", "INTEGER NOT NULL"),
            ("kcal_gasta", "REAL"),
            ("data", "TEXT NOT NULL")
        ],
        "metas": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("nome", "TEXT NOT NULL"),
            ("meta", "TEXT NOT NULL"),
            ("status", "TEXT DEFAULT 'Pendente'")
        ],
        "alimentos": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("nome", "TEXT UNIQUE"),
            ("categoria", "TEXT"),
            ("kcal", "REAL"),
            ("proteina", "REAL"),
            ("carboidrato", "REAL"),
            ("gordura", "REAL"),
            ("fibra", "REAL")
        ]
    }
    
    for tabela, colunas in tabelas.items():
        auto_migrar_tabela(cursor, tabela, colunas)
        
    alimentos = [
        ("Arroz branco cozido", "Cereais", 128, 2.5, 28.1, 0.2, 1.6),
        ("Arroz integral cozido", "Cereais", 124, 2.6, 25.8, 1.0, 2.7),
        ("Feijão carioca cozido", "Leguminosas", 76, 4.8, 13.6, 0.5, 8.5),
        ("Feijão preto cozido", "Leguminosas", 77, 4.5, 14.0, 0.5, 8.4),
        ("Tapioca", "Cereais", 230, 0.2, 57.0, 0.0, 0.0),
        ("Aveia", "Cereais", 394, 13.9, 66.6, 8.5, 9.1),
        ("Pão francês", "Cereais", 300, 8.0, 58.6, 3.1, 2.3),
        ("Pão integral", "Cereais", 250, 9.0, 41.0, 4.0, 6.0),
        ("Batata cozida", "Tubérculos", 52, 1.2, 11.9, 0.0, 1.3),
        ("Banana prata", "Frutas", 98, 1.3, 26.0, 0.1, 2.0),
        ("Maçã", "Frutas", 56, 0.3, 15.2, 0.0, 1.3),
        ("Ovo cozido", "Ovos", 146, 13.3, 0.6, 9.5, 0.0),
        ("Frango grelhado", "Carnes", 159, 32.0, 0.0, 2.5, 0.0),
        ("Peixe grelhado", "Pescados", 130, 26.0, 0.0, 3.0, 0.0),
        ("Leite integral", "Laticínios", 61, 3.2, 4.8, 3.3, 0.0),
        ("Iogurte natural", "Laticínios", 61, 3.5, 4.7, 3.3, 0.0),
        ("Queijo minas", "Laticínios", 264, 17.4, 3.2, 20.0, 0.0),
        ("Tomate", "Vegetais", 18, 0.9, 3.9, 0.2, 1.2),
        ("Alface", "Vegetais", 15, 1.4, 2.9, 0.2, 1.8),
        ("Laranja", "Frutas", 47, 0.9, 11.8, 0.1, 2.4),
        ("Abacate", "Frutas", 96, 1.2, 6.0, 8.4, 6.3),
        ("Batata doce cozida", "Tubérculos", 77, 0.6, 18.4, 0.1, 2.2),
        ("Carne bovina grelhada", "Carnes", 250, 26.0, 0.0, 16.0, 0.0),
        ("Brócolis cozido", "Vegetais", 25, 2.1, 4.4, 0.5, 3.4),
        ("Cenoura cozida", "Vegetais", 30, 0.8, 6.7, 0.2, 2.6),
        ("Morango", "Frutas", 30, 0.9, 6.8, 0.3, 1.7),
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO alimentos 
        (nome, categoria, kcal, proteina, carboidrato, gordura, fibra) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, alimentos)
    conn.commit()
    conn.close()

criar_banco()

# =========================================================
# LÓGICA DE IMC
# =========================================================
def calcular_imc(peso, altura):
    if peso <= 0 or altura <= 0:
        return 0
    if altura > 3:
        altura /= 100
    return peso / (altura * altura)

def classificacao_imc(imc, idade):
    if imc <= 0:
        return "Dados inválidos", "info", "Digite peso e altura válidos."
    if idade < 18:
        return "Avaliação por idade", "info", "Para menores de 18 anos, o IMC deve ser interpretado por curvas específicas de idade e sexo por um profissional."
    if imc < 18.5:
        return "Abaixo do peso", "warning", "Vale conversar com um profissional se isso for uma preocupação."
    elif imc < 25:
        return "Peso normal", "success", "Mantenha hábitos equilibrados e uma rotina ativa."
    elif imc < 30:
        return "Sobrepeso", "warning", "Priorize hábitos saudáveis e constância."
    else:
        return "Obesidade", "error", "Busque acompanhamento de um profissional de saúde."

# =========================================================
# INTERFACE DO USUÁRIO & PERFIL
# =========================================================
st.sidebar.title("IMC+ | Saúde e Hábitos")

if 'usuario' not in st.session_state:
    st.session_state.usuario = {
        'nome': 'Usuário',
        'idade': 25,
        'altura': 1.75,
        'peso': 70.0,
        'objetivo': 'Melhorar hábitos'
    }

with st.sidebar.expander("👤 Meu Perfil / Dados", expanded=False):
    nome = st.text_input("Nome", value=st.session_state.usuario['nome'])
    idade = st.number_input("Idade", min_value=1, max_value=120, value=int(st.session_state.usuario['idade']))
    altura = st.number_input("Altura (m)", min_value=0.5, max_value=2.5, value=float(st.session_state.usuario['altura']), step=0.01)
    peso = st.number_input("Peso (kg)", min_value=1.0, max_value=300.0, value=float(st.session_state.usuario['peso']), step=0.5)
    objetivo = st.selectbox("Objetivo Principal", ["Melhorar hábitos", "Manter saúde", "Praticar atividade física", "Conhecer alimentação"], index=0)

    if st.button("Atualizar Perfil", type="primary"):
        st.session_state.usuario = {
            'nome': nome,
            'idade': idade,
            'altura': altura,
            'peso': peso,
            'objetivo': objetivo
        }
        st.success("Perfil atualizado com sucesso!")

# Navegação Principal
menu = st.sidebar.radio(
    "Navegação",
    [
        "🏠 Dashboard", 
        "⚖️ Meu IMC", 
        "💧 Hidratação / Água", 
        "🏃 Registro de Atividades", 
        "🎯 Metas de Hábitos", 
        "🍎 Tabela Nutricional", 
        "💡 Dicas & Treinos", 
        "📈 Histórico Geral"
    ]
)

user = st.session_state.usuario
imc_atual = calcular_imc(user['peso'], user['altura'])
status, tipo_alerta, explicacao = classificacao_imc(imc_atual, user['idade'])

# =========================================================
# PÁGINAS DO SITE
# =========================================================

# 1. DASHBOARD
if menu == "🏠 Dashboard":
    st.title(f"Olá, {user['nome']} 👋")
    st.caption("Aqui está o resumo da sua saúde e dos seus hábitos.")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("IMC Atual", f"{imc_atual:.1f}")
    col2.metric("Peso", f"{user['peso']:.1f} kg")
    col3.metric("Altura", f"{user['altura']:.2f} m")
    col4.metric("Objetivo", user['objetivo'])

    st.markdown("---")
    
    # Status e Orientações
    if tipo_alerta == "success":
        st.success(f"**Status:** {status} - {explicacao}")
    elif tipo_alerta == "warning":
        st.warning(f"**Status:** {status} - {explicacao}")
    elif tipo_alerta == "error":
        st.error(f"**Status:** {status} - {explicacao}")
    else:
        st.info(f"**Status:** {status} - {explicacao}")

    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("💧 Hidratação do Dia")
        conn = conectar()
        hoje = datetime.now().strftime("%d/%m/%Y")
        df_agua = pd.read_sql_query("SELECT SUM(quantidade) as total FROM agua WHERE LOWER(nome) = LOWER(?) AND data LIKE ?", conn, params=(user['nome'], f"{hoje}%"))
        conn.close()
        
        agua_hoje = df_agua['total'].iloc[0] if not df_agua.empty and df_agua['total'].iloc[0] is not None else 0
        meta_agua = user['peso'] * 35
        progresso = min(agua_hoje / meta_agua, 1.0) if meta_agua > 0 else 0
        
        st.progress(progresso)
        st.write(f"**{agua_hoje:.0f} ml** ingeridos de uma meta recomendada de **{meta_agua:.0f} ml**.")

    with c2:
        st.subheader("🎯 Metas Pendentes")
        conn = conectar()
        df_metas = pd.read_sql_query("SELECT meta, status FROM metas WHERE LOWER(nome) = LOWER(?) ORDER BY id DESC LIMIT 3", conn, params=(user['nome'],))
        conn.close()
        if not df_metas.empty:
            for _, row in df_metas.iterrows():
                st.markdown(f"- **{row['meta']}** `({row['status']})`")
        else:
            st.info("Nenhuma meta salva no momento.")

# 2. MEU IMC
elif menu == "⚖️ Meu IMC":
    st.title("⚖️ Avaliação de IMC")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Resultado do IMC", f"{imc_atual:.2f}")
        st.write(f"**Classificação:** {status}")
        
        if st.button("💾 Salvar IMC no Histórico"):
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO historico (nome, idade, peso, altura, imc, classificacao, data) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user['nome'], user['idade'], user['peso'], user['altura'], imc_atual, status, datetime.now().strftime("%d/%m/%Y %H:%M"))
            )
            conn.commit()
            conn.close()
            st.success("Cálculo de IMC registrado com sucesso!")
            
    with col2:
        st.subheader("💡 Recomendações de Saúde")
        st.write("- 🥗 **Alimentação:** Priorize pratos coloridos, vegetais, leguminosas e boas fontes de proteína.")
        st.write("- 💧 **Água:** Beba água regularly ao longo do dia.")
        st.write("- 🏃 **Movimento:** Faça caminhadas ou exercícios regulares adequados ao seu ritmo.")
        st.write("- 😴 **Sono:** Mantenha uma rotina regular de descanso para auxílio metabólico.")

# 3. HIDRATAÇÃO
elif menu == "💧 Hidratação / Água":
    st.title("💧 Registro de Hidratação")
    
    meta_agua = user['peso'] * 35
    st.info(f"Sua meta diária estimada de água é **{meta_agua:.0f} ml** (35ml por kg).")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        qtd = st.number_input("Quantidade (ml)", min_value=50, max_value=2000, value=250, step=50)
        if st.button("➕ Adicionar Água"):
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO agua (nome, quantidade, data) VALUES (?, ?, ?)", (user['nome'], qtd, datetime.now().strftime("%d/%m/%Y %H:%M")))
            conn.commit()
            conn.close()
            st.success(f"{qtd}ml adicionados com sucesso!")
            
    with col2:
        st.subheader("Registros Recentes")
        conn = conectar()
        df_agua_rec = pd.read_sql_query("SELECT quantidade as 'Quantidade (ml)', data as 'Data/Hora' FROM agua WHERE LOWER(nome) = LOWER(?) ORDER BY id DESC LIMIT 5", conn, params=(user['nome'],))
        conn.close()
        st.dataframe(df_agua_rec, use_container_width=True)

# 4. REGISTRO DE ATIVIDADES
elif menu == "🏃 Registro de Atividades":
    st.title("🏃 Registro de Atividades Físicas")
    
    with st.form("form_atividade"):
        atividade = st.text_input("Exercício / Atividade", placeholder="Ex: Caminhada, Corrida, Musculação")
        categoria = st.selectbox("Categoria", ["Cardio", "Musculação", "Esporte", "Mobilidade/Flexibilidade"])
        intensidade = st.select_slider("Intensidade", options=["Leve", "Moderada", "Intensa"])
        minutos = st.number_input("Duração (Minutos)", min_value=5, max_value=300, value=30)
        kcal = st.number_input("Calorias Gastas Aprox. (kcal)", min_value=0, max_value=2000, value=150)
        
        submitted = st.form_submit_button("Salvar Atividade")
        if submitted and atividade:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO atividades (nome, atividade, categoria, intensidade, minutos, kcal_gasta, data) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user['nome'], atividade, categoria, intensidade, minutos, kcal, datetime.now().strftime("%d/%m/%Y %H:%M"))
            )
            conn.commit()
            conn.close()
            st.success(f"Atividade '{atividade}' salva com sucesso!")

# 5. METAS DE HÁBITOS
elif menu == "🎯 Metas de Hábitos":
    st.title("🎯 Minhas Metas")
    
    nova_meta = st.text_input("Cadastrar Nova Meta", placeholder="Ex: Dormir 8 horas por noite")
    if st.button("Adicionar Meta"):
        if nova_meta.strip():
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO metas (nome, meta) VALUES (?, ?)", (user['nome'], nova_meta))
            conn.commit()
            conn.close()
            st.success("Meta cadastrada!")
            st.rerun()

    st.markdown("---")
    st.subheader("Suas Metas Atuais")
    
    conn = conectar()
    df_metas = pd.read_sql_query("SELECT id, meta, status FROM metas WHERE LOWER(nome) = LOWER(?) ORDER BY id DESC", conn, params=(user['nome'],))
    conn.close()
    
    if not df_metas.empty:
        for index, row in df_metas.iterrows():
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"🎯 **{row['meta']}**")
            c2.write(f"Status: `{row['status']}`")
            if c3.button("Concluir", key=f"m_{row['id']}"):
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("UPDATE metas SET status = 'Concluída' WHERE id = ?", (row['id'],))
                conn.commit()
                conn.close()
                st.rerun()
    else:
        st.write("Nenhuma meta cadastrada ainda.")

# 6. TABELA NUTRICIONAL
elif menu == "🍎 Tabela Nutricional":
    st.title("🍎 Tabela de Alimentos")
    st.caption("Consulte a tabela de composição nutricional dos alimentos (por porção de 100g).")
    
    conn = conectar()
    df_alimentos = pd.read_sql_query("SELECT nome as Alimento, categoria as Categoria, kcal as 'Calorias (kcal)', proteina as 'Proteína (g)', carboidrato as 'Carboidratos (g)', gordura as 'Gorduras (g)', fibra as 'Fibras (g)' FROM alimentos", conn)
    conn.close()
    
    busca = st.text_input("🔍 Buscar Alimento por nome")
    if busca:
        df_alimentos = df_alimentos[df_alimentos['Alimento'].str.contains(busca, case=False, na=False)]
        
    st.dataframe(df_alimentos, use_container_width=True)

# 7. DICAS & TREINOS
elif menu == "💡 Dicas & Treinos":
    st.title("💡 Central de Dicas & Sugestões de Treinos")
    
    tab1, tab2 = st.tabs(["💡 Dicas de Saúde", "🏋️ Sugestões de Treinos"])
    
    with tab1:
        st.subheader("Hábitos Importantes")
        st.write("1. **Hidratação:** Consuma líquidos continuamente ao longo do dia.")
        st.write("2. **Refeições Equilibradas:** Combine vegetais, cereais integrais e proteínas em suas refeições.")
        st.write("3. **Sono Regulado:** Mantenha horários constantes para dormir e acordar.")
        st.write("4. **Consistência:** Estabeleça metas realistas e graduais para manter os resultados.")
        
    with tab2:
        st.subheader("Sugestões de Treino")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🔵 Treino Full Body (Corpo Inteiro)")
            st.write("- Agachamento Livre: 3 x 12")
            st.write("- Flexões de Braço (ou adaptadas): 3 x 10")
            st.write("- Remada Curvada: 3 x 12")
            st.write("- Prancha Abdominal: 3x 30 seg")
        with col2:
            st.markdown("### 🟢 Treino Aeróbico e Mobilidade")
            st.write("- Caminhada/Corrida Leve: 30 minutos")
            st.write("- Alongamento Geral de Quadril e Ombros")
            st.write("- Exercícios de Equilíbrio")

# 8. HISTÓRICO GERAL
elif menu == "📈 Histórico Geral":
    st.title("📈 Seu Histórico Geral")
    
    conn = conectar()
    df_hist = pd.read_sql_query("SELECT data as Data, peso as 'Peso (kg)', imc as IMC, classificacao as Classificação FROM historico WHERE LOWER(nome) = LOWER(?) ORDER BY id ASC", conn, params=(user['nome'],))
    conn.close()
    
    if not df_hist.empty:
        st.dataframe(df_hist, use_container_width=True)
        
        # Gráfico evolutivo do IMC
        fig = px.line(df_hist, x='Data', y='IMC', title='Evolução do seu IMC ao longo do tempo', markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Ainda não existem registros de IMC no histórico. Vá até a aba 'Meu IMC' e salve seu primeiro registro!")streamlit
pandas
plotly
