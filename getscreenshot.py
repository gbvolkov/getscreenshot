import os
import random
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pyautogui
import re

os.environ["WDM_SSL_VERIFY"] = "0"

def take_full_screen_screenshot(save_path):
    screenshot = pyautogui.screenshot()
    screenshot.save(save_path)
    #add_timestamp_to_screenshot(save_path)

WAITING_PERIOD = (1, 3)

def fit_page_to_screen(driver):
    screen_w, screen_h = driver.execute_script(
        "return [window.screen.availWidth, window.screen.availHeight];")
    driver.set_window_size(screen_w, screen_h)
    view_w, view_h = driver.execute_script(
        "return [ window.innerWidth, window.innerHeight ];")
    
    page_w, page_h = driver.execute_script(
        "return [ Math.max(document.body.scrollWidth,"
        "                document.documentElement.scrollWidth),"
        "         Math.max(document.body.scrollHeight,"
        "                document.documentElement.scrollHeight) ];")
    zoom = min(view_w / page_w, view_h / page_h, 1)

    driver.execute_script(f"document.body.style.zoom='{int(zoom*100)}%'")
   
    driver.execute_cdp_cmd("Emulation.setScrollbarsHidden",
                           {"hidden": True}) 

def take_full_page_screenshot(driver, save_path):
    # Inject timestamp into the page
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    driver.execute_script(f"document.body.insertAdjacentHTML('beforeend', '<div style=\"position:fixed; bottom:10px; right:10px; background:rgba(0, 0, 0, 0.5); color:white; padding:5px; font-size:12px;\">{timestamp}</div>');")
    time.sleep(1)
    fit_page_to_screen(driver)
    time.sleep(random.uniform(*WAITING_PERIOD))  # Random delay
    driver.save_screenshot(save_path)

def check_for_title_wrapper(driver):
    try:
        driver.find_element(By.CLASS_NAME, 'style-titleWrapper-Hmr_5')
        return True
    except:
        return False

def interact_for_missing_element(driver, href):
    driver.get(href)
    time.sleep(random.uniform(5, 10))  # Random delay
    if not check_for_title_wrapper(driver):
        driver.refresh()
        time.sleep(5)  # Wait for the page to load
        if not check_for_title_wrapper(driver):
            print("Element missing. Please interact with the page in the browser window.")
            while not check_for_title_wrapper(driver):
                time.sleep(random.uniform(*WAITING_PERIOD))  # Random delay

def enable_normal_mode():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd('Emulation.setPageScaleFactor', {'pageScaleFactor': 0.5})
    return driver

def enable_headless_mode():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")  # Suppress logs
    service = Service(ChromeDriverManager().install(), log_path=os.devnull)
    return webdriver.Chrome(service=service, options=options)

def take_screenshots(soup, driver, screenshot_dir='./screens'):
    if not os.path.exists(screenshot_dir):
        os.makedirs(screenshot_dir)
    class_pattern = re.compile(r"^iva-item-title-\S+$")
    items = soup.find_all('div', class_=class_pattern)
    print(f"Found {len(items)} elements on the page {driver.current_url}")

    for index, item in enumerate(items):
        link = item.find('a')['href']
        href = "https://www.avito.ru" + link
        
        soup  = get_page(href, driver)
       
        screenshot_path = os.path.join(screenshot_dir, f"post_screenshot_{index + 1}.png")
        take_full_page_screenshot(driver, screenshot_path)
        print(f"Screenshot for item {index + 1} saved as {screenshot_path}")
        time.sleep(random.uniform(*WAITING_PERIOD))  # Random delay
    
def get_total_pages(soup):
    try:
        paginator = soup.find("nav", {"aria-label": "Пагинация"}).find("ul")
        pages = paginator.find_all("li")
        last_page = int(pages[-2].find("span").text)
        return last_page
    except:
        # No paginator found
        return 1

def check_for_ip_restriction(soup):
    restricted_element = soup.find(string="Доступ ограничен: проблема с IP")
    return restricted_element is not None


def get_page(page_url, driver):
    while True:
        driver.get(page_url)

        time.sleep(random.uniform(*WAITING_PERIOD))  # Random delay
        attempts = 0
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        while attempts < 10 and check_for_ip_restriction(soup):
            print("IP restriction detected. Please solve the CAPTCHA in the browser window.")
            time.sleep(random.uniform(*WAITING_PERIOD))  # Random delay
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            attempts = attempts+1
        if attempts >= 10:
            print("CAPTCHA not solved within 10 attempts. Exiting.")
            driver.quit()
            exit()
        #driver.quit()
        #driver.execute_script("document.body.style.zoom='50%'")
        return soup
    

def main(base_url, screenshot_dir='./screens'):
    driver = enable_normal_mode()
    print(f"Getting {base_url}")
    soup = get_page(base_url, driver)
    time.sleep(random.uniform(*WAITING_PERIOD))  # Random delay
    
    while True:
        last_height = driver.execute_script("return document.body.scrollHeight")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height          
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    print(f"...saving {base_url}")
    take_screenshots(soup, driver, screenshot_dir)
    print(f"Saved {base_url}")

# Example usage
base_url = "https://www.avito.ru/brands/ileasing_auto/items/all?sellerId=bb0a7f8b42c052f45809909d17857309"
main(base_url)
