# SYLA
This is a D2L scraping application to retrieve and organize dropbox and quiz assignments within a Flask webapp 
<br>

The project was made as a personal tool only tested on UWaterloo's LEARN. Can be configured.

# Installation

**Clone the repo**
```bash
   git clone https://github.com/itxwilliam/syla.git
   cd syla
```

2. **Create a virtual environment** (recommended)
```bash
   python -m venv env
   source env/bin/activate   # on Windows: env\Scripts\activate
```

3. **Install dependencies**
```bash
   pip install -r requirements.txt
```

4. **Create a `.env` file** in the project root with the following:
```dotenv
   COOKIE_FILE_NAME=learn_cookies.json
   COMPLETED_FILE=completed_tasks.json
   LOGIN_SITE=https://learn.yourschool.edu
   D2L_URL=https://learn.yourschool.edu
```
   Replace `learn.yourschool.edu` with your institution's actual D2L URL.

5. **Run the app**
```bash
   python app.py
```
   Then open **http://127.0.0.1:5000** in your browser.


# Framework


### Overview
cookie_save.py --> scraper.py --> app.py

### cookie_save.py
This program opens a chromium tab and prompts the user to login to D2L. Once the user has logged in the session's cookies will be saved locally to allow for requests

### scraper.py
This program will send requests to D2L while sorting and organizng quizes and dropbox assignments.

### app.py
This manages the frontend, further and further processing
