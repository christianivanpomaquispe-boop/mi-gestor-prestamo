import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from fpdf import FPDF

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestor Préstamos", layout="wide")

def conectar_db():
    return sqlite3.connect('prestamos_master.db')

def crear_tablas():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS prestamos 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, monto REAL, tasa REAL, periodo TEXT, fecha_inicio TEXT, fecha_vencimiento TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS pagos 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, id_prestamo INTEGER, monto_pago REAL, fecha_pago TEXT)''')
    conn.commit()
    conn.close()

crear_tablas()

# --- CÁLCULOS ---
def calcular_interes(monto, tasa, fecha_inicio, periodo):
    try:
        inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        dias = (date.today() - inicio).days
        if dias <= 0: return 0.0
        div = {"Semanal": 7, "Quincenal": 15, "Mensual": 30}
        return round(monto * (tasa / 100) * (dias / div.get(periodo, 30)), 2)
    except:
        return 0.0

# --- FUNCIÓN PDF (CORREGIDA SIN F-STRINGS COMPLEJAS) ---
def generar_pdf_recibo(cliente, monto, fecha, saldo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "RECIBO DE PAGO", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, "Cliente: " + str(cliente), ln=True)
    pdf.cell(200, 10, "Fecha: " + str(fecha), ln=True)
    pdf.cell(200, 10, "Monto Pagado: $" + str(monto), ln=True)
    pdf.cell(200, 10, "Saldo Restante: $" + str(saldo), ln=True)
    pdf.ln(20)
    pdf.cell(200, 10, "Firma: ________________________", ln=True, align='C')
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ ---
st.title("🏦 Mi Gestor de Préstamos")
menu = ["Cartera", "Nuevo Préstamo", "Pagos", "Recibos"]
choice = st.sidebar.radio("Menú", menu)

if choice == "Nuevo Préstamo":
    with st.form("f1"):
        c = st.text_input("Nombre")
        m = st.number_input("Monto ($)", min_value=1.0)
        t = st.number_input("Interés (%)", min_value=0.1)
        p = st.selectbox("Frecuencia", ["Semanal", "Quincenal", "Mensual"])
        fi = st.date_input("Inicio", date.today())
        fv = st.date_input("Vencimiento", date.today())
        if st.form_submit_button("Guardar"):
            conn = conectar_db()
            conn.execute("INSERT INTO prestamos (cliente, monto, tasa, periodo, fecha_inicio, fecha_vencimiento) VALUES (?,?,?,?,?,?)", (c, m, t, p, str(fi), str(fv)))
            conn.commit()
            conn.close()
            st.success("¡Guardado!")

elif choice == "Cartera":
    conn = conectar_db()
    df = pd.read_sql_query("SELECT * FROM prestamos", conn)
    if not df.empty:
        df['Int_Hoy'] = df.apply(lambda x: calcular_interes(x['monto'], x['tasa'], x['fecha_inicio'], x['periodo']), axis=1)
        st.dataframe(df, use_container_width=True)
    conn.close()

elif choice == "Pagos":
    conn = conectar_db()
    cli = pd.read_sql_query("SELECT id, cliente FROM prestamos", conn)
    if not cli.empty:
        op = {f"{r['cliente']} ({r['id']})": r['id'] for _, r in cli.iterrows()}
        s = st.selectbox("Cliente", list(op.keys()))
        m_p = st.number_input("Monto Pago", min_value=0.1)
        if st.button("Registrar"):
            conn.execute("INSERT INTO pagos (id_prestamo, monto_pago, fecha_pago) VALUES (?,?,?)", (op[s], m_p, str(date.today())))
            conn.commit()
            st.success("Pago registrado")
    conn.close()

elif choice == "Recibos":
    conn = conectar_db()
    res = pd.read_sql_query("SELECT p.id, pr.cliente, p.monto_pago, p.fecha_pago FROM pagos p JOIN prestamos pr ON p.id_prestamo = pr.id ORDER BY p.id DESC", conn)
    if not res.empty:
        sel = st.selectbox("Seleccione pago", res.apply(lambda x: f"{x['cliente']} - {x['monto_pago']}", axis=1))
        if st.button("Generar PDF"):
            row = res.iloc[0] # Simplificado para prueba
            pdf = generar_pdf_recibo(row['cliente'], row['monto_pago'], row['fecha_pago'], 0.0)
            st.download_button("Descargar", pdf, "recibo.pdf", "application/pdf")
    conn.close()
