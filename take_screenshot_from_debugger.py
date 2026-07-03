from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

try:
    driver = webdriver.Chrome(options=chrome_options)
    driver.save_screenshot(r"C:\Users\USER\AppData\Local\Temp\active_chrome.png")
    print("Screenshot saved successfully to active_chrome.png")
except Exception as e:
    print(f"Error: {e}")
