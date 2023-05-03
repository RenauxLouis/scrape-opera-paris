import smtplib
import ssl
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import sleep
import os
from pyvirtualdisplay import Display
import sys

import requests
from bs4 import BeautifulSoup
from selenium import webdriver


session = requests.Session()

ARIODANTE_URL = "https://www.operadeparis.fr/saison-22-23/opera/ariodante"
MAURICE_BEJART_URL = "https://www.operadeparis.fr/saison-22-23/ballet/maurice-bejart"
URLS_TO_CHECK = [MAURICE_BEJART_URL]
VALID_DATES_PER_URL = {
    ARIODANTE_URL: [
        "30/dim./avr.",
        "02/mar./mai.",
        "07/dim./mai.",
        "09/mar./mai.",
        "11/jeu./mai.",
        "14/dim./mai.",
        "16/mar./mai.",
        "18/jeu./mai.",
        "20/sam./mai.",
    ],
    MAURICE_BEJART_URL: [
        "10/mer./mai",
        "12/ven./mai",
        # "13/sam./mai",
        "16/mar./mai"
    ]
}
INVALID_PRICES_PER_URL = {
    ARIODANTE_URL: [],
    MAURICE_BEJART_URL: []
}

SENDER_EMAIL = "strike.price.notification@gmail.com"
SENDER_PASSWORD = os.environ.get("PASSWORD")
RECEIVER_EMAILS = ["renauxlouis@gmail.com"]

def parse(url):

    display = Display(visible=False, size=(1024, 768))
    display.start()

    driver = webdriver.Firefox(executable_path="/home/ubuntu/geckodriver")
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


def seat_selector(date_table, valid_dates, invalid_prices, date):

    if date not in valid_dates:
        return False

    uls = date_table.find_all("ul")
    if not uls:
        return False

    categories_table = uls[0]
    place_categories = categories_table.find_all("li")
    
    available_places = [place for place in place_categories if "entry-disabled" not in place["class"]]

    for place in available_places:
        
        good_seat = place.find_all("p")[1].text not in invalid_prices

        if good_seat:
            return True


def scape_opera_page(soup, url):

    valid_dates = VALID_DATES_PER_URL[url]
    invalid_prices = INVALID_PRICES_PER_URL[url]

    calendar_div = soup.find("div", {"id": "calendar"})
    dates_ul = calendar_div.find_all("ul", {"class": "component__list"})[0]
    dates_tables = dates_ul.find_all("li")
    for date_table in dates_tables:

        date = "/".join([date_tag.text for date_tag in date_table.find_all("span")[:3]])
        selected_seat = seat_selector(date_table, valid_dates, invalid_prices, date)
        if selected_seat:
            email_content = url + "    " + date
            create_secure_connection_and_send_email("OPERA AVAILABILITY", email_content)


def run_scrape():

    for url in URLS_TO_CHECK:
        soup = soup_http_download(url)
        scape_opera_page(soup, url)
    

if __name__ == "__main__":
    run_scrape()
