from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from pathlib import Path
import time
import os
import csv

# Stocks to track
symbols = ['HWM', 'BAC', 'COKE', 'F']

# Map symbols to correct exchanges for Google Finance
symbol_exchange_map = {
    'HWM': 'NYSE',
    'BAC': 'NYSE',
    'COKE': 'NASDAQ',
    'F': 'NYSE'
    
}

# Setup headless Chrome browser
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 1)

# Log file setup
log_file = Path("stock_accuracy_log.csv")
if not log_file.exists():
    with open(log_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Symbol", "Google Price", "Yahoo Price", "Delta", "Accuracy %"])

def get_yahoo_price(symbol):
    try:
        url = f"https://finance.yahoo.com/quote/{symbol}"
        driver.get(url)
        el = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, f'fin-streamer[data-symbol="{symbol}"][data-field="regularMarketPrice"]')
        ))
        wait.until(lambda d: el.text.strip() != "")
        return float(el.text.replace(",", ""))
    except Exception as e:
        print(f"{symbol} (Yahoo): [Caution] Error - {e}")
        return None

def get_google_price(symbol):
    try:
        exchange = symbol_exchange_map.get(symbol, 'NASDAQ')  # Default to NASDAQ
        url = f"https://www.google.com/finance/quote/{symbol}:{exchange}"
        driver.get(url)

        price_els = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, 'div.YMlKec.fxKbKc')
        ))
        full_text = price_els[0].text.strip()
        price_line = full_text.split('\n')[0].replace('$', '')
        return float(price_line)
    except Exception as e:
        print(f"{symbol} (Google): [Caution] Error - {e}")
        return None

try:
    while True:
        os.system('clear' if os.name != 'nt' else 'cls')  # Works on Mac/Linux/Windows
        print("📊 Live Stock Accuracy Checker")
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for symbol in symbols:
            yahoo_price = get_yahoo_price(symbol)
            google_price = get_google_price(symbol)

            if yahoo_price is None or google_price is None:
                print(f"{symbol}: [Caution] Could not retrieve both prices\n")
                continue

            delta = google_price - yahoo_price
            accuracy_pct = 100 - abs(delta / yahoo_price) * 100

            # Match status logic
            if accuracy_pct == 100:
                match_status = "✅ Exact Match"
            elif accuracy_pct >= 99.9:
                match_status = "⚠️ Near Match"
            else:
                match_status = "❌ Mismatch"

            # Print to terminal
            print(f"{symbol}: ${google_price:.2f} (Google)")
            print(f"  ↳ Accuracy vs Yahoo: {accuracy_pct:.4f}% → {match_status}")
            print(f"  Δ = {delta:.4f} | Yahoo @ ${yahoo_price:.2f}\n")

            # Write to CSV
            with open(log_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    timestamp,
                    symbol,
                    f"{google_price:.2f}",
                    f"{yahoo_price:.2f}",
                    f"{delta:.4f}",
                    f"{accuracy_pct:.4f}"
                ])

        print("🔄 Refreshing in 2 seconds... (Ctrl+C to stop)")
        time.sleep(2)

except KeyboardInterrupt:
    print("\n🛑 Monitoring stopped by user.")

finally:
    driver.quit()
