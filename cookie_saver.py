from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os

load_dotenv()

def save_cookie(file_path : str, login_site : str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto(login_site)

        page.wait_for_url("**/d2l/home*", timeout=300000)

        context.storage_state(path=file_path)

        browser.close()



if __name__ == "__main__":
    save_cookie(
        file_path= os.getenv("COOKIE_FILE_NAME"),
        login_site= os.getenv("LOGIN_SITE") 
    )