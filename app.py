import smtplib
import ssl
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import sleep
import os
from pyvirtualdisplay import Display

import requests
from bs4 import BeautifulSoup
from selenium import webdriver


session = requests.Session()

FIGARO_URL = "https://www.operadeparis.fr/saison-22-23/opera/les-noces-de-figaro"

SENDER_EMAIL = "strike.price.notification@gmail.com"
SENDER_PASSWORD = os.environ.get("PASSWORD")
RECEIVER_EMAILS = ["renauxlouis@gmail.com"]

display = Display(visible=False, size=(1024, 768))
display.start()

def parse(url):
    response = webdriver.Firefox()
    response.get(url)
    sleep(3)
    source_code = response.page_source
    return  source_code


def soup_http_download(url, params=None, retries=3):

    try:
        soup = BeautifulSoup(parse(FIGARO_URL),'lxml')
    except requests.exceptions.RetryError:
        if retries:
            sleep(2)
            soup_http_download(url, params=params, retries=retries-1)
        else:
            sys.exit(f"Exceeded max retries when querying {url}")

    return soup


def create_secure_connection_and_send_email(title, content):

    port = 465
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        for receiver_email in RECEIVER_EMAILS:
            send_email(server, receiver_email, title, content)


def send_email(server, receiver_email, title, content):

    assert receiver_email.split("@")[1] == "gmail.com"

    msg_root = MIMEMultipart("alternative")
    msg_root["Subject"] = title
    msg_root["From"] = SENDER_EMAIL
    msg_root["To"] = receiver_email
    msg_root.preamble = title

    msg_root.attach(MIMEText(content))

    server.sendmail(SENDER_EMAIL, receiver_email, msg_root.as_string())


def run_scrape():

    soup = soup_http_download(FIGARO_URL)
    dates_ul = soup.find_all("ul", {"class": "component__list"})[6]
    dates = dates_ul.find_all("li")
    for date in dates:
        uls = date.find_all("ul")
        if uls:
            categories_table = uls[0]
            place_categories = categories_table.find_all("li")
            for place_category in place_categories:
                color = place_category.find_all("span")[0]["style"]
                not_grey = not "#CCCCCC" in color
                not_25 = place_category.find_all("p")[1].text != "25 €"
                if not_grey and not_25:
                    create_secure_connection_and_send_email("OPERA AVAILABILITY", FIGARO_URL)


if __name__ == "__main__":
    run_scrape()
