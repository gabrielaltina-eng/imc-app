import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuração da página do Streamlit
st.set_page_config(
    page_title="IMC+ | Saúde, Hábitos e Nutrição",
    page_icon="🩺",
    layout="wide"
)

# --- BANCO DE DADOS ---
def conectar():
    conn = sqlite3.connect("imc_plus_web.db")
    return conn

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

# --- FUNÇÕES DE LÓGICA DO IMC ---
def calcular_imc(peso, altura):
    if altura <= 0:
        return 0
    return peso / (altura ** 2)

def classificar_imc(imc):
    if imc < 18.5:
        return "Abaixo do peso"
    elif 18.5 <= imc < 25.0:
        return "Peso normal"
    elif 25.0 <= imc < 30.0:
        return "Sobrepeso"
    elif 30.0 <= imc < 35.0:
        return "Obesidade Grau 1"
    elif 35.0 <= imc < 40.0:
        return "Obesidade Grau 2"
    else:
        return "Obesidade Grau 3 (Mórbida)"

# --- TELA LATERAL (SIDEBAR / NAVEGAÇÃO) ---
st.sidebar.title("🩺 IMC+ Web")

# Gerenciamento do Perfil de Usuário
conn = conectar()
usuarios_db = pd.read_sql_query("SELECT nome FROM usuarios", conn)['nome'].tolist()
conn.close()

if not usuarios_db:
    usuario_atual = "Convidado"
    st.sidebar.info("Crie um perfil na aba 'Meu Perfil' para salvar seus dados.")
else:
    usuario_atual = st.sidebar.selectbox("Selecione seu Perfil:", usuarios_db)

menu = st.sidebar.radio(
    "Navegação",
    [
        "📊 Meu IMC",
        "💧 Água e Passos",
        "✅ Metas e Hábitos",
        "🥗 Tabela Nutricional",
        "💡 Dicas de Saúde",
        "🏋️ Treinos Semanais",
        "👤 Meu Perfil",
        "📈 Histórico Geral"
    ]
)

# --- 1. MEU IMC ---
if menu == "📊 Meu IMC":
    st.title("📊 Calculadora de IMC")
    
    conn = conectar()
    user_info = pd.read_sql_query("SELECT * FROM usuarios WHERE nome = ?", conn, params=(usuario_atual,))
    conn.close()
    
    altura_padrao = float(user_info['altura'].iloc[0]) if not user_info.empty else 1.70
    
    col1, col2 = st.columns(2)
    with col1:
        peso = st.number_input("Digite seu peso (kg):", min_value=1.0, max_value=300.0, value=70.0, step=0.1)
    with col2:
        altura = st.number_input("Digite sua altura (m):", min_value=0.5, max_value=2.5, value=altura_padrao, step=0.01)
        
    if st.button("Calcular e Salvar Registro", type="primary"):
        imc = calcular_imc(peso, altura)
        classificacao = classificar_imc(imc)
        data_hoje = datetime.today().strftime('%Y-%m-%d %H:%M')
        
        st.subheader(f"Seu IMC é **{imc:.2f}**")
        st.info(f"Classificação: **{classificacao}**")
        
        if usuario_atual != "Convidado":
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO historico (nome, data, peso, imc, classificacao)
                VALUES (?, ?, ?, ?, ?)
            """, (usuario_atual, data_hoje, peso, imc, classificacao))
            conn.commit()
            conn.close()
            st.success("Registro salvo no seu histórico!")

# --- 2. ÁGUA E PASSOS ---
elif menu == "💧 Água e Passos":
    st.title("💧 Rastreador Diário de Água e Atividades")
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
        st.write(f"**Progresso Atual:** {agua_atual} / {meta_agua} ml")
        st.progress(min(agua_atual / meta_agua, 1.0))
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("+ 250ml Água"):
                agua_atual += 250
        with col_b:
            if st.button("+ 500ml Água"):
                agua_atual += 500
                
    with col2:
        st.subheader("🚶 Passos Diários")
        st.write(f"**Progresso Atual:** {passos_atuais} / {meta_passos} passos")
        st.progress(min(passos_atuais / meta_passos, 1.0))
        
        novos_passos = st.number_input("Adicionar passos:", min_value=0, step=500)
        if st.button("Registrar Passos"):
            passos_atuais += novos_passos
            
    # Atualizar no banco de dados
    if usuario_atual != "Convidado":
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO registros_diarios (nome, data, agua, passos)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(nome, data) DO UPDATE SET agua=?, passos=?
        """, (usuario_atual, data_hoje, agua_atual, passos_atuais, agua_atual, passos_atuais))
        conn.commit()
        conn.close()

# --- 3. METAS E HÁBITOS ---
elif menu == "✅ Metas e Hábitos":
    st.title("✅ Meus Hábitos Saudáveis")
    
    novo_habito = st.text_input("Adicionar novo hábito:")
    if st.button("Adicionar Hábito"):
        if novo_habito and usuario_atual != "Convidado":
            conn = conectar()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO habitos (nome, habito, status) VALUES (?, ?, 0)", (usuario_atual, novo_habito))
                conn.commit()
                st.success(f"Hábito '{novo_habito}' adicionado!")
            except:
                st.warning("Este hábito já existe.")
            conn.close()
            
    st.divider()
    
    if usuario_atual != "Convidado":
        conn = conectar()
        df_habitos = pd.read_sql_query("SELECT habito, status FROM habitos WHERE nome = ?", conn, params=(usuario_atual,))
        conn.close()
        
        if not df_habitos.empty:
            for idx, row in df_habitos.iterrows():
                checked = st.checkbox(row['habito'], value=bool(row['status']), key=f"hab_{idx}")
                if checked != bool(row['status']):
                    conn = conectar()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE habitos SET status = ? WHERE nome = ? AND habito = ?", (int(checked), usuario_atual, row['habito']))
                    conn.commit()
                    conn.close()

# --- 4. TABELA NUTRICIONAL ---
elif menu == "🥗 Tabela Nutricional":
    st.title("🥗 Tabela de Alimentos")
    
    dados_alimentos = {
        "Alimento": ["Arroz Branco Cozido (100g)", "Feijão Preto Cozido (100g)", "Peito de Frango Grelhado (100g)", "Ovo Cozido (1 unidade)", "Banana Prata (1 unidade)", "Maçã (1 unidade)", "Aveia em Flocos (30g)"],
        "Calorias (kcal)": [130, 77, 165, 78, 98, 72, 117],
        "Carboidratos (g)": [28.0, 14.0, 0.0, 0.6, 23.0, 19.0, 17.0],
        "Proteínas (g)": [2.5, 4.5, 31.0, 6.3, 1.3, 0.3, 4.3],
        "Gorduras (g)": [0.2, 0.5, 3.6, 5.3, 0.1, 0.2, 2.3]
    }
    
    df_alimentos = pd.DataFrame(dados_alimentos)
    
    busca = st.text_input("🔍 Buscar alimento:")
    if busca:
        df_alimentos = df_alimentos[df_alimentos['Alimento'].str.contains(busca, case=False)]
        
    st.dataframe(df_alimentos, use_container_width=True)

# --- 5. DICAS DE SAÚDE ---
elif menu == "💡 Dicas de Saúde":
    st.title("💡 Dicas Diárias de Saúde e Bem-Estar")
    
    st.markdown("""
    * **Hidratação:** Beba água regularmente mesmo sem sentir sede extrema.
    * **Sono:** Priorize entre 7 e 8 horas de sono de qualidade por noite para regulação hormonal.
    * **Alimentação:** Prefira alimentos in natura e reduza o consumo de ultraprocessados.
    * **Movimento:** Evite ficar sentado por mais de 2 horas seguidas ao longo do dia.
    """)

# --- 6. TREINOS SEMANAIS ---
elif menu == "🏋️ Treinos Semanais":
    st.title("🏋️ Sugestão de Treino Semanal")
    
    st.markdown("### 🟢 Treino Aeróbico e Mobilidade")
    st.write("- Caminhada/Corrida Leve: 30 minutos")
    st.write("- Alongamento Geral de Quadril e Ombros")
    st.write("- Exercícios de Equilíbrio")

# --- 7. MEU PERFIL ---
elif menu == "👤 Meu Perfil":
    st.title("👤 Gerenciar Perfil")
    
    nome_perfil = st.text_input("Seu Nome:")
    idade_perfil = st.number_input("Sua Idade:", min_value=1, max_value=120, value=25)
    altura_perfil = st.number_input("Sua Altura (m):", min_value=0.5, max_value=2.5, value=1.70, step=0.01)
    meta_agua_p = st.number_input("Meta de Água (ml):", min_value=500, max_value=10000, value=2000, step=250)
    meta_passos_p = st.number_input("Meta de Passos Diários:", min_value=1000, max_value=50000, value=8000, step=500)
    
    if st.button("Salvar / Criar Perfil", type="primary"):
        if nome_perfil:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO usuarios (nome, idade, altura, meta_agua, meta_passos)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(nome) DO UPDATE SET idade=?, altura=?, meta_agua=?, meta_passos=?
            """, (nome_perfil, idade_perfil, altura_perfil, meta_agua_p, meta_passos_p, idade_perfil, altura_perfil, meta_agua_p, meta_passos_p))
            conn.commit()
            conn.close()
            st.success("Perfil salvo com sucesso! Atualize a página para usá-lo.")

# --- 8. HISTÓRICO GERAL ---
elif menu == "📈 Histórico Geral":
    st.title("📈 Seu Histórico Geral")
    
    conn = conectar()
    df_hist = pd.read_sql_query("SELECT data as Data, peso as 'Peso (kg)', imc as IMC, classificacao as Classificação FROM historico WHERE LOWER(nome) = LOWER(?) ORDER BY id", conn, params=(usuario_atual,))
    conn.close()
    
    if not df_hist.empty:
        st.dataframe(df_hist, use_container_width=True)
        
        # Gráfico evolutivo do IMC
        fig = px.line(df_hist, x='Data', y='IMC', title='Evolução do seu IMC ao longo do tempo', markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Ainda não existem registros de IMC no histórico. Vá até a aba 'Meu IMC' e salve seu primeiro registro!")
