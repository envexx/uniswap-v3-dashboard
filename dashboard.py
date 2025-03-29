import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
import io  # Untuk membuat file PDF langsung di Streamlit

# 🔹 Load Data dari SQLite
def load_data():
    conn = sqlite3.connect("uniswap.db")
    query = """
    SELECT timestamp, sender, token0_symbol, token1_symbol, amount0, amount1, price 
    FROM swaps WHERE price IS NOT NULL AND amount0 IS NOT NULL AND amount1 IS NOT NULL"""
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Konversi timestamp ke format datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s").dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Konversi kolom numerik
    df[["amount0", "amount1", "price"]] = df[["amount0", "amount1", "price"]].apply(pd.to_numeric, errors='coerce')
    
    return df

# 🔹 Fungsi untuk membuat PDF sebagai file buffer
def generate_pdf_report(df):
    pdf = FPDF(orientation="L")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(280, 10, "Uniswap Swap Data Analysis", ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(280, 10, f"Total Swaps: {len(df)}", ln=True)

    pdf.ln(5)
    pdf.cell(280, 10, "Top 10 Transactions:", ln=True)
    pdf.ln(5)
    
    col_width = [40, 50, 30, 30, 40, 40, 30]
    headers = ["Timestamp", "Sender", "Token0", "Token1", "Amount0", "Amount1", "Price"]
    pdf.set_font("Arial", style="B", size=10)
    
    for header, width in zip(headers, col_width):
        pdf.cell(width, 8, header, border=1, align="C")
    pdf.ln()
    
    pdf.set_font("Arial", size=9)
    for _, row in df.head(10).iterrows():
        pdf.cell(col_width[0], 8, row["timestamp"], border=1, align="C")
        pdf.cell(col_width[1], 8, row["sender"], border=1, align="C")
        pdf.cell(col_width[2], 8, row["token0_symbol"], border=1, align="C")
        pdf.cell(col_width[3], 8, row["token1_symbol"], border=1, align="C")
        pdf.cell(col_width[4], 8, f"{row['amount0']:.2f}" if pd.notna(row['amount0']) else "N/A", border=1, align="C")
        pdf.cell(col_width[5], 8, f"{row['amount1']:.2f}" if pd.notna(row['amount1']) else "N/A", border=1, align="C")
        pdf.cell(col_width[6], 8, f"${row['price']:.2f}" if pd.notna(row['price']) else "N/A", border=1, align="C")
        pdf.ln()

    # ✅ Simpan PDF sebagai string bytes
    pdf_buffer = io.BytesIO()
    pdf_bytes = pdf.output(dest="S").encode("latin1")  # Gunakan 'S' untuk output ke string
    pdf_buffer.write(pdf_bytes)
    pdf_buffer.seek(0)

    return pdf_buffer

# 🔹 Fungsi utama untuk Streamlit Dashboard
def main():
    st.title("📊 Uniswap Swap Data Dashboard")
    
    df = load_data()
    
    if df.empty:
        st.warning("⚠️ Data kosong, pastikan database sudah diisi.")
        return
    
    # **Tampilkan data di dashboard**
    st.write("### 🔍 Data Swap Transaksi")
    st.dataframe(df.head(10))  # Tampilkan hanya 10 transaksi pertama

    # **Analisis Data**
    st.write("### 📈 Korelasi Amount dan Harga Swap")
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(df[["amount0", "amount1", "price"]].corr(), annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
    st.pyplot(fig)

    st.write("### 📊 Distribusi Harga Swap")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(df["price"], bins=50, kde=True, color="blue", ax=ax)
    ax.set_xlabel("Price (USD)")
    ax.set_ylabel("Frequency")
    st.pyplot(fig)

    # **Tombol untuk Download PDF**
    st.write("### 📄 Download Laporan PDF")
    pdf_buffer = generate_pdf_report(df)
    st.download_button(label="📥 Download PDF Report",
                   data=pdf_buffer,
                   file_name="Uniswap_Report.pdf",
                   mime="application/pdf")

if __name__ == "__main__":
    main()
