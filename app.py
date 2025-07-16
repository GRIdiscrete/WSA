from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup
import time


app = Flask(__name__)


@app.route('/rfps')
def get_rfps():
    max_pages = request.args.get('max_pages', default=5, type=int)

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--user-data-dir=/tmp/chrome-user-data')

    driver = webdriver.Chrome(options=options)
    url = 'https://www.bidscanada.com/Default.CFM?Page=400&PC=457DDD89&UID=%2D&SID=%2D&BSID=0'
    driver.get(url)

    all_rfps = []
    current_page = 0

    while current_page < max_pages:
        try:
            # Wait for table to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "tr"))
            )

            # Parse current page
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            rows = soup.find_all('tr')

            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:
                    rfp = {
                        "Reference": cells[0].get_text(strip=True),
                        "Description": cells[1].get_text(strip=True),
                        "Region": cells[2].get_text(strip=True),
                        "Closing Date": cells[3].get_text(strip=True)
                    }
                    all_rfps.append(rfp)

            print(f"✔ Page {current_page + 1} scraped ({len(all_rfps)} RFPs)")

            # Try to go to the next page
            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@value='Next 50']"))
                )
                # Scroll into view & click using JavaScript (more reliable)
                driver.execute_script("arguments[0].scrollIntoView();", next_button)
                driver.execute_script("arguments[0].click();", next_button)
                current_page += 1
                time.sleep(3)  # Wait for the next page to load
            except (NoSuchElementException, TimeoutException):
                print("✖ No more pages available.")
                break

        except Exception as e:
            print(f"⚠ Error: {e}")
            break

    driver.quit()

    return jsonify({"rfps": all_rfps, "count": len(all_rfps)})


if __name__ == '__main__':
    app.run()
