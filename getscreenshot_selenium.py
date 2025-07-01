import os
import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

os.environ["WDM_SSL_VERIFY"] = "0"

def take_full_page_screenshot(driver, save_path):
    total_height = driver.execute_script("return document.body.scrollHeight")
    driver.set_window_size(1920, total_height)
    time.sleep(2)
    driver.save_screenshot(save_path)

def check_for_ip_restriction(driver):
    try:
        restricted_element = driver.find_element(By.XPATH, "//*[contains(text(), 'Доступ ограничен: проблема с IP')]")
        return restricted_element is not None
    except:
        return False

def check_for_title_wrapper(driver):
    try:
        driver.find_element(By.CLASS_NAME, 'style-titleWrapper-Hmr_5')
        return True
    except:
        return False

def interact_for_missing_element(driver, href):
    driver.get(href)
    time.sleep(5)  # Wait for the page to load
    if not check_for_title_wrapper(driver):
        driver.refresh()
        time.sleep(5)  # Wait for the page to load
        if not check_for_title_wrapper(driver):
            print("Element missing. Please interact with the page in the browser window.")
            while not check_for_title_wrapper(driver):
                time.sleep(5)  # Wait for the user to interact

def enable_normal_mode():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def enable_headless_mode():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")  # Suppress logs
    options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid detection
    options.add_experimental_option("excludeSwitches", ["enable-logging"])  # Suppress logs
    options.add_argument("--stderr=/dev/null")    
    service = Service(ChromeDriverManager().install(), log_path=os.devnull)
    return webdriver.Chrome(service=service, options=options)

def take_screenshots(driver, screenshot_dir='./screens'):
    if not os.path.exists(screenshot_dir):
        os.makedirs(screenshot_dir)
    
    items = driver.find_elements(By.CLASS_NAME, 'iva-item-title-py3i_')
    
    for index, item in enumerate(items):
        link = item.find_element(By.TAG_NAME, 'a')
        href = link.get_attribute('href')
        
        #driver.execute_script(f"window.open('{href}');")
        driver.execute_script(f"window.open('data:');")
        driver.switch_to.window(driver.window_handles[1])
        time.sleep(random.uniform(5, 10))  # Random delay
        driver = get_page(href, driver)
        
        if not check_for_title_wrapper(driver):
            driver.quit()
            driver = enable_normal_mode()
            interact_for_missing_element(driver, href)
            driver.quit()
            driver = enable_headless_mode()
            driver.get(href)
            time.sleep(random.uniform(5, 10))  # Random delay
        
        screenshot_path = os.path.join(screenshot_dir, f"post_screenshot_{index + 1}.png")
        take_full_page_screenshot(driver, screenshot_path)
        
        print(f"Screenshot for item {index + 1} saved as {screenshot_path}")
        
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(random.uniform(2, 5))  # Random delay
    
def get_total_pages(driver):
	try:
		paginator = driver.find_element(By.CSS_SELECTOR, "nav[aria-label='Пагинация'] ul")
		pages = paginator.find_elements(By.TAG_NAME, "li")
		last_page = pages[-2].find_element(By.TAG_NAME, "span").text  # Get the second last item which is the last page number
		return int(last_page)
	except:
        #No paginator found
		return 1

def load_page_from_source(driver, page_source, cookies):
    driver.execute_script("document.open();document.write(arguments[0]);document.close();", page_source)
    #for cookie in cookies:
    #    driver.add_cookie(cookie)
    driver.refresh()

def get_page(page_url, driver):
    #driver = enable_headless_mode()
    while True:
        driver.get(page_url)
        time.sleep(random.uniform(5, 10))  # Random delay
        attempts = 0
        page_source = driver.page_source
        while attempts < 10 and check_for_ip_restriction(driver):
            print("IP restriction detected. Please solve the CAPTCHA in the browser window.")
            driver.quit()
            driver = enable_normal_mode()
            driver.get(page_url)
            time.sleep(15)  # Random delay
            page_source = driver.page_source
            cookies = driver.get_cookies()
            driver.quit()
            driver = enable_headless_mode()
            load_page_from_source(driver, page_source, cookies)
            #driver.get(page_url)
            attempts = attempts+1
        if attempts >= 10:
            print("CAPTCHA not solved within 10 attempts. Exiting.")
            driver.quit()
            exit()
        return driver
    

def main(base_url, screenshot_dir='./screens'):
    driver = enable_headless_mode()
    #driver = enable_normal_mode()
    driver = get_page(base_url, driver)
    time.sleep(random.uniform(5, 10))  # Random delay
    

    total_pages = get_total_pages(driver)
    
    for page in range(1, total_pages + 1):
        url = f"https://www.avito.ru/all?cd=1&p={page}&q=%D0%B8%D0%BD%D1%82%D0%B5%D1%80%D0%BB%D0%B8%D0%B7%D0%B8%D0%BD%D0%B3"
        print(f"Getting {url}")
        driver = get_page(url, driver)
        time.sleep(random.uniform(5, 10))  # Random delay
        print(f"...saving {url}")
        take_screenshots(driver, screenshot_dir)
        print(f"Saved {url}")
    
    driver.quit()

# Example usage
base_url = "https://www.avito.ru/all?cd=1&p=1&q=%D0%B8%D0%BD%D1%82%D0%B5%D1%80%D0%BB%D0%B8%D0%B7%D0%B8%D0%BD%D0%B3"
main(base_url)
