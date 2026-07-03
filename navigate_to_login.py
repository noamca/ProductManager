from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

try:
    driver = webdriver.Chrome(options=chrome_options)
    print("Navigating to login page...")
    driver.get("https://www.king-games.co.il/apanel/")
    print("Done navigating. Keeping Chrome open.")
except Exception as e:
    print(f"Error: {e}")
