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
SWAN_LAKE_URL = "https://www.operadeparis.fr/saison-22-23/ballet/le-lac-des-cygnes"
URLS_TO_CHECK = [FIGARO_URL, SWAN_LAKE_URL]
VALID_DATES_PER_URL = {
    FIGARO_URL: [
        "23/mer./nov.",
        "25/ven./nov.",
        "27/dim./nov.",
        "30/mer./nov.",
        "07/mer./déc.",
        "11/dim./déc.",
        "13/mar./déc.",
        "16/ven./déc.",
        "19/lun./déc.",
        "22/jeu./déc.",
        "25/dim./déc.",
    ],
    SWAN_LAKE_URL: [
        "10/sam./déc.",
        "11/dim./déc.",
        "13/mar./déc.",
        "14/mer./déc.",
        "16/ven./déc.",
        "17/sam./déc.",
        "19/lun./déc.",
        "20/mar./déc.",
        "22/jeu./déc.", 
        "23/ven./déc.", 
        "25/dim./déc."
    ]
}
INVALID_PRICES_PER_URL = {
    FIGARO_URL: ["25 €"],
    SWAN_LAKE_URL: []
}

SENDER_EMAIL = "strike.price.notification@gmail.com"
SENDER_PASSWORD = os.environ.get("PASSWORD")
RECEIVER_EMAILS = ["renauxlouis@gmail.com"]

def parse(url):

    display = Display(visible=False, size=(1024, 768))
    display.start()

    driver = webdriver.Firefox()
    driver.get(url)
    sleep(3)
    source_code = driver.page_source

    driver.quit()
    display.stop()

    return  source_code


def soup_http_download(url, params=None, retries=3):

    try:
        soup = BeautifulSoup(parse(url),'lxml')
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


def seat_selector(url, color, place_category, date):

    valid_dates = VALID_DATES_PER_URL[url]
    invalid_prices = INVALID_PRICES_PER_URL[url]

    available = not "#CCCCCC" in color
    good_seat = place_category.find_all("p")[1].text not in invalid_prices
    good_date = date in valid_dates

    return available and good_seat and good_date


def scape_opera_page(soup, url):

    calendar_div = soup.find("div", {"id": "calendar"})
    dates_ul = calendar_div.find_all("ul", {"class": "component__list"})[0]
    dates_tables = dates_ul.find_all("li")
    for date_table in dates_tables:
        date = "/".join([date_tag.text for date_tag in date_table.find_all("span")[:3]])
        uls = date_table.find_all("ul")
        if uls:
            categories_table = uls[0]
            place_categories = categories_table.find_all("li")
            for place_category in place_categories:
                color = place_category.find_all("span")[0]["style"]

                seat_available = seat_selector(url, color, place_category, date)
                if seat_available:
                    create_secure_connection_and_send_email("OPERA AVAILABILITY", url)


def run_scrape():

    for url in URLS_TO_CHECK:
        soup = soup_http_download(url)
        scape_opera_page(soup, url)


if __name__ == "__main__":
    run_scrape()
