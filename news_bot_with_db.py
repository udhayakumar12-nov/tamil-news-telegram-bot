from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

def get_dailythanthi_news():
    news_list = []
    driver = None
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument('--disable-software-rasterizer')
        
        # Important: Let ChromeDriverManager find Chrome binary automatically
        # Do NOT set binary_location unless absolutely necessary
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.get("https://www.dailythanthi.com/")
        driver.implicitly_wait(5)
        
        elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/news/')]")
        
        for element in elements[:10]:
            title = element.text.strip()
            link = element.get_attribute('href')
            if title and len(title) > 20:
                news_list.append(f"📌 *{title}*\n🔗 [Read more]({link})\n🏷️ *Source:* தினத்தந்தி")
        print(f"✅ தினத்தந்தி - {len(news_list)} செய்திகள்")
        
    except Exception as e:
        print(f"❌ தினத்தந்தி பிழை: {e}")
    finally:
        if driver:
            driver.quit()
    return news_list