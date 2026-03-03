import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from fpdf import FPDF

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Gestor de Préstamos", layout="wide")

# --- FUNCIONES DE BASE DE DATOS ---
def conectar_db():
    return sqlite3.connect('prestamos_master.db')

def crear_tablas():
    conn = conectar_db()
    cursor = conn.cursor()
    # Tabla de Préstamos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prestamos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            monto REAL,
            tasa REAL,
            periodo TEXT,
            fecha_inicio TEXT,
            fecha_vencimiento TEXT
        )
    ''')
    # Tabla de Pagos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_prestamo INTEGER,
            monto_pago REAL,
            fecha_pago TEXT,
            FOREIGN KEY(id_prestamo) REFERENCES prestamos(id)
        )
    ''')
    conn.commit()
    conn.close()

crear_tablas()

# --- LÓGICA DE CÁLCULO DE INTERÉS ---
def calcular_interes(monto, tasa, fecha_inicio, periodo):
    inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    hoy = date.today()
    dias = (hoy - inicio).days
    if dias <= 0: return 0.0
    
    divisores = {"Semanal": 7, "Quincenal": 15, "Mensual": 30}
    divisor = divisores.get(periodo, 30)
    return round(monto * (tasa / 100) * (dias / divisor), 2)

# --- FUNCIÓN GENERAR PDF ---
def generar_pdf_recibo(cliente, monto, fecha, saldo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "RECIBO DE PAGO", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Cliente: {cliente}", ln=True)
    pdf.cell(200, 10, f"Fecha: {fecha}", ln=True)
    pdf.cell(200, 10, f
