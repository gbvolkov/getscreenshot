from bs4 import BeautifulSoup
import requests
import os
from twocaptcha import TwoCaptcha
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def get_driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def extract_captcha_id(page_url):
    driver = get_driver()
    driver.get(page_url)
    try:
        # Locate the "Click to Verify" button
        verify_button = driver.find_element(By.CLASS_NAME, 'geetest_radar_tip_content')
        verify_button.click()
        time.sleep(5)  # Wait for CAPTCHA to load
    except Exception as e:
        print("Error finding or clicking Verify button:", e)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    elements = soup.find_all(True)
    
    for element in elements:
        #print(element)
        if 'captcha_id' in element.get_text():
            src = element.get_text()
            params = dict(item.split('=') for item in src.split('?')[1].split('&'))
            return params.get('captcha_id')

    return None

def solve_captcha(captcha_id, page_url):
    api_key = os.getenv('APIKEY_2CAPTCHA', 'YOUR_API_KEY')
    solver = TwoCaptcha(api_key)
    
    try:
        result = solver.geetest_v4(
            captcha_id=captcha_id,
            url=page_url
        )
    except Exception as e:
        return str(e)
    else:
        return result

def inject_response_and_submit(page_url, captcha_solution):
    driver_path = r'C:\path\to\chromedriver.exe'  # Update this path to your chromedriver.exe location
    driver = webdriver.Chrome(executable_path=driver_path)
    driver.get(page_url)
    
    driver.execute_script(f"document.querySelector('input[name=\"geetest_challenge\"]').value='{captcha_solution['geetest_challenge']}'")
    driver.execute_script(f"document.querySelector('input[name=\"geetest_seccode\"]').value='{captcha_solution['geetest_seccode']}'")
    driver.execute_script(f"document.querySelector('input[name=\"geetest_validate\"]').value='{captcha_solution['geetest_validate']}'")
    
    submit_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
    submit_button.click()
    
    time.sleep(5)
    
    driver.quit()

# Example usage:
#page_url = 'https://2captcha.com/demo/geetest-v4'
page_url = 'https://www.geetest.com/en/demo'
captcha_id = extract_captcha_id(page_url)

if captcha_id:
    captcha_solution = solve_captcha(captcha_id, page_url)
    if isinstance(captcha_solution, dict):
        inject_response_and_submit(page_url, captcha_solution)
    else:
        print('Error solving CAPTCHA:', captcha_solution)
else:
    print('CAPTCHA ID not found')
