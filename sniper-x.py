#!/user/bin/env python3.6
# sniper-x, a url screenshotting and request redirect checker
# verion, v1.00
# ex. usage: python3 sniper-x.py -t www.duckduckgo.com/ -o ~/Desktop/screen_shot
# ex. usage: python3 sniper-x.py -l ~/Desktop/urllist.txt -o ~/Desktop/screen_shot -s
# requires:
#   osx or linux
#   python3.6
#   pip3 install selenium
#   pip3 install requests
#   pip3 install requests[security]
#   sudo cp <geckodriver> /usr/local/bin/geckodriver
# driver resources:
#   https://github.com/mozilla/geckodriver/releases
#   https://chromedriver.storage.googleapis.com/index.html?path=2.43/

import argparse
import os
import re
import requests
import sys

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--silent', action="store_true")
parser.add_argument('-t', '--target', action="store")
parser.add_argument('-l', '--list', action="store")
parser.add_argument('-o', '--output', action="store")
parser.add_argument('-r', '--html', action="store_true")
parser.add_argument('-d', '--debug', action="store_true")
args = parser.parse_args()

def file_handler(folder, f_name, data):
    """Simple file handler function for writing outputs of this script to file."""
    f = open(f"{folder}/{f_name}.txt", 'a')
    f.write(f"{data}\n")
    f.close()

def request_handler(folder, url_name, f_name):
    """Perform a GET request to the target url to get an HTTP status code result."""
    # http headers to minimize 403/429 when making requests
    http_headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        'referrer': 'https://google.com',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Pragma': 'no-cache',
    }
    try:
        req = requests.get(url_name, headers=http_headers, timeout=1.0)
    except Exception as e:
        if not args.silent:
            print(f'{url_name}. Error continuing on.')
        file_handler(folder, f"{f_name}-failure-log", f"{url_name} {e}. Error continuing on.")
    if not args.silent:
        print(f"HTTP status returned: {req.status_code}")
    rdir = 1
    # show redirects, if any
    for resp in req.history:
        if not args.silent:
            print(f"Redirect {rdir} - {resp.status_code} {resp.url}")
        file_handler(folder, f_name, f"Redirect {rdir} - {resp.status_code} {resp.url}")
        rdir += 1
    if not args.silent:    
        print(f"{req.status_code} {req.url}")
    file_handler(folder, f_name, f"{req.status_code} {req.url}")
    if args.html:
        file_handler(folder, f"{f_name}-html", req.text)

def screenshot_handler(folder, url_name, f_name):
    """Uses Selenium to grab a PNG image of the website in its current state."""
    options = Options()
    options.add_argument("--headless")
    # location of headless driver
    try:
        try:
            driver = webdriver.Firefox(firefox_options=options, executable_path="/usr/local/bin/geckodriver")
        except:
            driver = webdriver.Chrome(chrome_options=options, executable_path="/usr/local/bin/chromedriver")
    except:
        print("Could not initialize either Firefox or Chrome headless browser. Check your driver location and ensure that is in '/usr/local/bin'")
        sys.exit(1)
    if not args.silent:    
        print("Headless browser invoked")
    # full url path, passed as arg -t or -l 'http://duckduckgo.com/'
    driver.get(url_name)
    # set parameters to grab entire page
    width = driver.execute_script("return Math.max(document.body.scrollWidth, \
    document.body.offsetWidth, document.documentElement.clientWidth, \
    document.documentElement.scrollWidth, document.documentElement.offsetWidth);")
    height = driver.execute_script("return Math.max(document.body.scrollHeight, \
    document.body.offsetHeight, document.documentElement.clientHeight, \
    document.documentElement.scrollHeight, document.documentElement.offsetHeight);")
    driver.set_window_size(width+100, height+100)
    # output location && file name, appends .png, passed as arg -o './my_screenshot.png'
    img_name = f"{f_name}.png"
    driver.save_screenshot(f"{folder}/{img_name}")
    if not args.silent:
        print(f"Screenshot saved to {folder}/{img_name}")
    driver.quit()

def main():
    """Main function and body of the script"""
    # parse the args for the indicated urls to snipe
    if args.target:
        urlzz = [args.target]
    elif args.list:
        with open(args.list) as f:
            urlzz = f.read().splitlines()
    else:
        print('Specify either -t <url> for a single target; or, -l <path_to_list> for multiple targets')
        sys.exit(1)
    # takes specified output location, or creates a default one in the current directory
    if not args.output:
        folder = 'sniper-x_default'
    elif args.output:
        folder = args.output
    # output folder name handling
    if not os.path.exists(folder):
        os.mkdir(folder)
    else:
        count_out = 0
        while os.path.exists(folder) is True:
            count_out += 1
            folder = folder.split('_')[0]
            folder = f"{folder}_{str(count_out)}"
        os.mkdir(folder)
        
    # main function and loop
    for url_name in urlzz:
        try:
            #strip the url to just the domain name
            f_name = re.sub(r'^\.', '', str(re.search(r'((?<=//)|(?<=w.)|(?<=^))[a-z0-9-.]{2,256}\.[a-z]{2,10}(\.[a-z][a-z])?(?!\.)', url_name.lower(), re.IGNORECASE).group(0)).strip('/')).replace('.','_')
            count_it = 0
            # check to see if the files exists from privious gets, append a new unique marker for differentiation
            while os.path.isfile(f"{folder}/{f_name}.txt") is True:
                count_it += 1
                f_name = f_name.split('_')[0]
                f_name = f"{f_name}_{str(count_it)}"
            # clean the urls to ensure they are grabbed in other functions, adding http:// because selenium is sometimes a special little snowflake
            if not 'http' in url_name:
                url_name = f"https://{url_name}"
            if not args.silent:
                print(f"Targeting {url_name}")
        except:
            if args.debug:
                raise
            if not args.silent:
                print('Error parsing url, continuing to next url. Run again with -d for debug. information')
                continue
        try:
            request_handler(folder, url_name, f_name)
        except:
            if args.debug:
                raise
            if not args.silent:
                print('Error, skipping http redirect checker. Run again with -d for debug. information')
                continue
        try:
            screenshot_handler(folder, url_name, f_name)
            request_handler(folder, url_name, f_name)
        except:
            if args.debug:
                raise
            if not args.silent:
                print('Error, skipping screenshot operation. Run again with -d for debug information.')
                continue

if __name__ == "__main__": # execute this as a program drectly. do not make available functions as standalone.
    main()
