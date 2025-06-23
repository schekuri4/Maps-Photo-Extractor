import webbrowser
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests

def open_website(url):
    try:
        webbrowser.open(url)
        print(f"Opened {url} in your default browser.")
    except webbrowser.Error as e:
        print(f"Error opening URL: {e}")

def search_business_on_maps(business_name):
    query = business_name.replace(' ', '+')
    maps_url = f"https://www.google.com/maps/search/{query}"
    open_website(maps_url)

def extract_and_download_photos(business_name, download_dir="downloaded_photos", max_photos=20):
    query = business_name.replace(' ', '+')
    maps_url = f"https://www.google.com/maps/search/{query}"
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(maps_url)
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a.hfpxzc')))
    except Exception:
        print("Timed out waiting for search results.")
        driver.quit()
        return
    try:
        first_result = driver.find_element(By.CSS_SELECTOR, 'a.hfpxzc')
        first_result.click()
        time.sleep(5)
    except Exception:
        print("Could not find the business on Google Maps.")
        driver.quit()
        return
    try:
        photos_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-value="Photos"]'))
        )
        photos_button.click()
        time.sleep(5)
    except Exception:
        print("Could not find the original Photos button. Available clickable elements:")
        buttons = driver.find_elements(By.TAG_NAME, 'button')
        links = driver.find_elements(By.TAG_NAME, 'a')
        for el in buttons + links:
            try:
                text = el.text
                if text:
                    print(f"Clickable: {text}")
            except Exception:
                continue
        found = False
        for el in buttons + links:
            try:
                text = el.text.lower()
                if 'photo' in text or 'see photos' in text:
                    el.click()
                    time.sleep(5)
                    found = True
                    break
            except Exception:
                continue
        if not found:
            print("Could not open the photos tab.")
            driver.quit()
            return
    photo_urls = set()
    for _ in range(5):
        thumbnails = driver.find_elements(By.CSS_SELECTOR, 'img[src^="https://lh3.googleusercontent.com/"]')
        for img in thumbnails:
            src = img.get_attribute('src')
            if src and src not in photo_urls:
                photo_urls.add(src)
                if len(photo_urls) >= max_photos:
                    break
        if len(photo_urls) >= max_photos:
            break
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(2)
    driver.quit()
    if not photo_urls:
        print("No photos found.")
        return
    os.makedirs(download_dir, exist_ok=True)
    print(f"Downloading {len(photo_urls)} photos...")
    for i, url in enumerate(photo_urls):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                with open(os.path.join(download_dir, f"photo_{i+1}.jpg"), 'wb') as f:
                    f.write(response.content)
        except Exception as e:
            print(f"Failed to download {url}: {e}")
    print(f"Downloaded {len(photo_urls)} photos to '{download_dir}'.")

if __name__ == "__main__":
    business_names = input("Enter business names separated by commas (e.g., McDonald's New York, McDonald's Chicago, McDonald's LA): ")
    business_list = [name.strip() for name in business_names.split(',') if name.strip()]
    for business_name in business_list:
        print(f"\nProcessing: {business_name}")
        safe_name = business_name.replace(' ', '_').replace('\\', '').replace('/', '')
        extract_and_download_photos(business_name, download_dir=f"downloaded_photos_{safe_name}")