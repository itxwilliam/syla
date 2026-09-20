import requests
import json
from dotenv import load_dotenv
import os
import cookie_saver

load_dotenv()

def format_json(file_name : str):
    with open(file_name, "r") as f:
        cookie_data = json.load(f)

    with open(file_name, "w") as f:
        json.dump(cookie_data, f, indent = 4)

def get_endpoint(endpoint : str, file_name : str = "endpoints.json") -> str:
    with open(file_name, "r") as f:
        return json.load(f).get(endpoint, "")

def valid_cookies(file_path : str) -> dict:
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path) as f:
            browser_data = json.load(f)
    except:
        return {}

    cookies = browser_data.get("cookies", [])
    if not cookies:
        return {}

    return cookies

def pretty_print(data):
    print(json.dumps(data, indent=4, sort_keys=False, default=str))


class Course:
    def __init__(self, name, id, type):
        self.name
        self.id

        self.type

    

class Session:
    def __init__(self, scraped_cookies):
        self.session = requests.Session()

        self.scraped_cookies = scraped_cookies
        self.url = os.getenv("D2L_URL")

        self.courses = {}

        # intialization
        self.set_session_cookies()
        self.scrape_courses()

    def set_session_cookies(self):
        for cookie in self.scraped_cookies:
            cookie_name = cookie.get("name")
            cookie_value = cookie.get("value")
            cookie_domain = cookie.get("domain")
            cookie_path = cookie.get("path", "/")

            self.session.cookies.set(
                name = cookie_name,
                value = cookie_value,
                domain = cookie_domain,
                path = cookie_path,
            )

    def _exec_request(self, endpoint : str):
        return self.session.get(f"{self.url}{endpoint}")

    
    def test_request(self, endpoint : str):
        response = self._exec_request(endpoint)
        pretty_print(response.json())
        return response
        

    def scrape_courses(self):
        scraped_data = self._exec_request(get_endpoint("enrollments"))
        for course in scraped_data.json().get("Items", []):
            course_data = course.get("OrgUnit")

            course_type = course_data.get("Type").get("Id")
            if course_type == 3: # I think 3 gives the most relevant courses
                self.courses[course_data.get("Id")] = course_data.get("Name")

    




if __name__ == "__main__":
    cookie_file = os.getenv("COOKIE_FILE_NAME")
    login_site = os.getenv("LOGIN_SITE")

    scraped_cookies = valid_cookies(cookie_file)
    if scraped_cookies:
        format_json(cookie_file)
        client_session = Session(scraped_cookies);
        pretty_print(client_session.courses)
    
    else:

        print("Invalid cookies, please relogin")
        cookie_saver.save_cookie(cookie_file,login_site)
