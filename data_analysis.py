import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF

# 🔹 Load Data dari SQLite
def load_data():
    conn = sqlite3.connect("uniswap.db")
    query = "SELECT timestamp, sender, token0_symbol, token1_symbol, amount0, amount1, price FROM swaps"
    df = pd.read_sql(query, conn)
    conn.close()

    # Konversi timestamp ke format datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s").astype(str)  

    # Konversi kolom numerik
    df["amount0"] = pd.to_numeric(df["amount0"], errors="coerce")
    df["amount1"] = pd.to_numeric(df["amount1"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    return df

# 🔹 Analisis Data
def analyze_data(df):
    print("\n📊 Statistik Data:")
    print(df.describe(include="all"))

    # 🔹 Korelasi antara amount0, amount1, dan price
    plt.figure(figsize=(8, 6))
    sns.heatmap(df[["amount0", "amount1", "price"]].corr(), annot=True, cmap="coolwarm", fmt=".2f")
    plt.title("Korelasi Amount dan Harga Swap")
    plt.savefig("correlation_plot.png")  
    plt.close()  

    # 🔹 Distribusi harga swap
    plt.figure(figsize=(10, 5))
    sns.histplot(df["price"], bins=50, kde=True, color="blue")
    plt.title("Distribusi Harga Swap")
    plt.xlabel("Price (USD)")
    plt.ylabel("Frequency")
    plt.savefig("price_distribution.png")  
    plt.close()  

# 🔹 Kelas PDF dengan Tabel
class PDF(FPDF):
    def __init__(self, orientation="L"):
        super().__init__(orientation, unit="mm", format="A4")

    def add_table(self, df):
        self.set_font("Arial", style="B", size=10)
        col_width = [40, 50, 30, 30, 40, 40, 30]  # Lebar kolom diperbesar untuk lanskap
        headers = ["Timestamp", "Sender", "Token0", "Token1", "Amount0", "Amount1", "Price"]

        # Header tabel
        for i, header in enumerate(headers):
            self.cell(col_width[i], 8, header, border=1, align="C")
        self.ln()

        # Isi tabel (maksimum 10 data agar tidak penuh)
        self.set_font("Arial", size=9)
        for i, row in df.head(10).iterrows():
            self.cell(col_width[0], 8, row["timestamp"], border=1, align="C")
            self.cell(col_width[1], 8, row["sender"], border=1, align="C")
            self.cell(col_width[2], 8, row["token0_symbol"], border=1, align="C")
            self.cell(col_width[3], 8, row["token1_symbol"], border=1, align="C")
            self.cell(col_width[4], 8, f"{row['amount0']:.2f}" if pd.notna(row['amount0']) else "N/A", border=1, align="C")
            self.cell(col_width[5], 8, f"{row['amount1']:.2f}" if pd.notna(row['amount1']) else "N/A", border=1, align="C")
            self.cell(col_width[6], 8, f"${row['price']:.2f}" if pd.notna(row['price']) else "N/A", border=1, align="C")
            self.ln()

# 🔹 Buat Laporan PDF dalam Mode Lanskap
def generate_pdf_report(df):
    pdf = PDF(orientation="L")  # 🔹 Set lanskap
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Judul
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(280, 10, "Uniswap Swap Data Analysis", ln=True, align="C")

    # Tambahkan statistik dasar
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(280, 10, f"Total Swaps: {len(df)}", ln=True)

    # Tambahkan tabel
    pdf.ln(5)
    pdf.cell(280, 10, "Top 10 Transactions:", ln=True)
    pdf.ln(5)
    pdf.add_table(df)

    # Tambahkan gambar ke dalam PDF
    pdf.add_page()
    pdf.cell(280, 10, "Correlation Plot:", ln=True)
    pdf.image("correlation_plot.png", x=10, y=30, w=260)

    pdf.add_page()
    pdf.cell(280, 10, "Price Distribution:", ln=True)
    pdf.image("price_distribution.png", x=10, y=30, w=260)

    pdf.output("Uniswap_Report_Landscape.pdf")
    print("✅ Laporan PDF (Lanskap) berhasil dibuat: Uniswap_Report_Landscape.pdf")

# 🔹 Main Execution
df = load_data()
if not df.empty:
    analyze_data(df)
    generate_pdf_report(df)
else:
    print("⚠️ Data kosong, pastikan `fetch_data.py` sudah dijalankan.")
