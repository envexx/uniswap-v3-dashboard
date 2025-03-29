import requests
import pandas as pd
import sqlite3
import time

# API Key & Endpoint
API_KEY = "e3a6c8feea34efa4e236af2bd18a0df6"  # Ganti dengan API Key Anda
GRAPHQL_ENDPOINT = f"https://gateway.thegraph.com/api/{API_KEY}/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"

# Ambil data dengan pagination
BATCH_SIZE = 100  # Jumlah data per batch
MAX_RECORDS = 1000  # Maksimal data yang ingin diambil
session = requests.Session()

def fetch_data():
    all_swaps = []
    last_timestamp = None  # Untuk pagination
    total_fetched = 0

    while total_fetched < MAX_RECORDS:
        # Query GraphQL dengan price & nama token
        query = f"""
        {{
          swaps(first: {BATCH_SIZE}, orderBy: timestamp, orderDirection: desc, where: {{ timestamp_lt: {last_timestamp if last_timestamp else "9999999999"} }}) {{
            amount0
            amount1
            sender
            timestamp
            token0 {{
              symbol
              name
            }}
            token1 {{
              symbol
              name
            }}
            amountUSD
          }}
        }}
        """

        headers = {"Content-Type": "application/json"}
        response = session.post(GRAPHQL_ENDPOINT, json={"query": query}, headers=headers)

        if response.status_code != 200:
            print(f"⚠️ ERROR: API Gagal dengan status {response.status_code}")
            print("Response JSON:", response.text)
            break

        data = response.json()
        if "data" not in data or "swaps" not in data["data"]:
            print("⚠️ ERROR: Data tidak ditemukan dalam respons API.")
            break

        swaps = data["data"]["swaps"]
        if not swaps:
            print("✅ Data selesai diambil, tidak ada data baru.")
            break  # Stop jika tidak ada data baru

        # Konversi data agar lebih mudah dibaca
        for swap in swaps:
            swap["token0_name"] = swap["token0"]["name"]
            swap["token0_symbol"] = swap["token0"]["symbol"]
            swap["token1_name"] = swap["token1"]["name"]
            swap["token1_symbol"] = swap["token1"]["symbol"]
            swap["price"] = swap["amountUSD"]  # Harga dalam USD

            # Hapus kolom JSON yang tidak dibutuhkan
            del swap["token0"]
            del swap["token1"]

        all_swaps.extend(swaps)
        last_timestamp = swaps[-1]["timestamp"]  # Ambil timestamp terakhir
        total_fetched += len(swaps)
        print(f"📊 Data diambil: {total_fetched} records...")

        time.sleep(1)  # Hindari rate limit API

    return pd.DataFrame(all_swaps)

# Ambil Data
df = fetch_data()

if not df.empty:
    # Simpan ke CSV
    df.to_csv("uniswap_data.csv", index=False)
    print("✅ Data berhasil disimpan di uniswap_data.csv")

    # Simpan ke SQLite
    conn = sqlite3.connect("uniswap.db")
    df.to_sql("swaps", conn, if_exists="replace", index=False)
    print("✅ Data berhasil disimpan di database uniswap.db")
    conn.close()
else:
    print("⚠️ Tidak ada data yang disimpan karena kosong.")
