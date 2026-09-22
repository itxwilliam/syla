import requests
import json
from dotenv import load_dotenv
import os
import cookie_saver

load_dotenv()

#==================#
# HELPER FUNCTIONS #
#==================#

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


def build_quiz_url(course_id, quiz_id):
    base_url = os.getenv("D2L_URL")
    return f"{base_url}/d2l/lms/quizzing/user/quiz_summary.d2l?qi={quiz_id}&ou={course_id}"

def build_dropbox_url(course_id, dropbox_id):
    base_url = os.getenv("D2L_URL")
    return f"{base_url}/d2l/lms/dropbox/user/folder_submit_files.d2l?db={dropbox_id}&grpid=0&isprv=0&bp=0&ou={course_id}"

#=========#
# CLASSES #
#=========#

class Quiz:
    def __init__(self, name, id, start, due, end, url):
        self.name = name
        self.id = id

        self.start = start
        self.due = due
        self.end = end

        self.url = url
        
    def __repr__(self):
        return f"({self.name}, {self.id})"

class Dropbox:
    def __init__(self, name, id, due, url):
        self.name = name
        self.id = id

        self.due = due

        self.url = url

    def __repr__(self):
        return f"({self.name}, {self.id})"

class Course:
    def __init__(self, name, id, type, start, end):
        self.name = name
        self.id = id
        self.type = type

        #access
        self.start = start
        self.end = end

        # populated by sessions scrape methods
        self.quizzes = {}
        self.dropboxes = {}

    def add_quiz(self, quiz:Quiz):
        self.quizzes[quiz.id] = quiz

    def get_quizzes(self) -> dict:
        return self.quizzes

    def get_quiz(self, quiz_id) -> Quiz:
        return self.quizzes.get(quiz_id)

    def add_dropbox(self, dropbox:Dropbox):
        self.dropboxes[dropbox.id] = dropbox

    def get_dropboxes(self) -> dict:
        return self.dropboxes

    def get_dropbox(self, dropbox_id) -> Dropbox:
        return self.dropboxes.get(dropbox_id)

    def __repr__(self):
        return f"({self.name}, {self.id})"

class Session:
    def __init__(self, scraped_cookies = None):
        self.session = requests.Session()

        self.scraped_cookies = [] if not scraped_cookies else scraped_cookies 
        self.url = os.getenv("D2L_URL")

        self.courses = {}   
        # intialization
        if self.scraped_cookies:
            self.set_session_cookies()

    def set_session_cookies(self, scraped_cookies = None):
        if scraped_cookies:
            self.scraped_cookies = scraped_cookies

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
        return response


    def validate_request(self) -> bool:
        response = self._exec_request(get_endpoint("whoami"))
        return response.status_code == 200
        

    def scrape_courses(self) -> dict:
        endpoint = get_endpoint("enrollments")
        response = self._exec_request(endpoint)

        for course in response.json().get("Items", []):
            course_data = course.get("OrgUnit")

            course_type = course_data.get("Type").get("Id")
            course_name = course_data.get("Name")
            course_id = course_data.get("Id")

            course_access = course.get("Access")
            course_start = course_access.get("StartDate")
            course_end = course_access.get("EndDate")

            if course_type == 3 and course_end and course_start: # I think 3 gives the most relevant courses
                self.courses[course_id] = Course(
                    name=course_name,
                    id=course_id,
                    type=course_type,
                    start=course_start,
                    end=course_end
                    )

        return self.courses

    def get_courses(self) -> dict:
        return self.courses if self.courses else self.scrape_courses()

    def get_course(self, course_id) -> Course:
        return self.courses.get(course_id)

    def scrape_quizzes(self, course_id : int):
        endpoint = get_endpoint("quizzes").format(course_id=course_id)
        response = self._exec_request(endpoint)

        for quiz in response.json().get("Objects", []):
            quiz_name = quiz.get("Name")
            quiz_id = quiz.get("QuizId")

            quiz_start = quiz.get("StartDate")
            quiz_end = quiz.get("EndDate")
            quiz_due = quiz.get("DueDate")

            scraped_quiz = Quiz(
                name = quiz_name,
                id = quiz_id,
                start = quiz_start,
                due = quiz_due,
                end = quiz_end,
                url=build_quiz_url(course_id, quiz_id),
            )

            self.get_course(course_id).add_quiz(scraped_quiz)

    def scrape_dropboxes(self, course_id : int):
        endpoint = get_endpoint("dropbox_folders").format(course_id=course_id)
        response = self._exec_request(endpoint)

        for dropbox in response.json():
            dropbox_name = dropbox.get("Name")
            dropbox_id = dropbox.get("Id")

            dropbox_due = dropbox.get("DueDate")

            scraped_dropbox = Dropbox(
                name = dropbox_name,
                id = dropbox_id,
                due=dropbox_due,
                url=build_dropbox_url(course_id, dropbox_id)
            )
            
            self.get_course(course_id).add_dropbox(scraped_dropbox)

    def populate_courses(self):
        self.scrape_courses()
        for course_id in self.courses.keys():
            self.scrape_dropboxes(course_id)
            self.scrape_quizzes(course_id)

#======#
# AUTH #
#======#

def get_authenticated_session(cookie_file : str, login_site : str, max_attempts : int = 2, populate : bool = False) -> Session:
    for attempt in range(max_attempts):
        scraped_cookies = valid_cookies(cookie_file)

        if scraped_cookies:
            format_json(cookie_file)
            client_session = Session()
            client_session.set_session_cookies(scraped_cookies)

            if client_session.validate_request():
                if populate:
                    client_session.populate_courses()
                return client_session

        cookie_saver.save_cookie(cookie_file, login_site)
    raise RuntimeError(f"Couldn't establish an authenticated session after {max_attempts} attempts")

  

#=======#
# DEBUG #
#=======#

if __name__ == "__main__":
    cookie_file = os.getenv("COOKIE_FILE_NAME")
    login_site = os.getenv("LOGIN_SITE")

    client_session = get_authenticated_session(cookie_file, login_site, populate=True)

    for course_id, course in client_session.get_courses().items():
        print(course)
        print(course.get_quizzes())
        print(course.get_dropboxes())
        for i in range(4):
            print("\n")