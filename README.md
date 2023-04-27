# Scrape Opéra de Paris

Scrape opera website for available seats and email availabilities to be run periodically with cronjob

## Requirements

Python

###Install geckodriver:
```
wget https://github.com/mozilla/geckodriver/releases/download/v0.24.0/geckodriver-v0.24.0-linux64.tar.gz
tar -xvzf geckodriver*
chmod +x geckodriver
export PATH=$PATH:/path-to-extracted-file/.
```
###Setup env
```
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
```
