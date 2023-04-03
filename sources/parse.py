## Scrape bleau.info
## Probably not ideal in terms of DB organization, will change it later once architecture is fixed

import argparse
import os
import pickle
import requests
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from tqdm import tqdm


def scrape_boulders_images(area):
    
    url_area = f'https://bleau.info/{area}'

    # Send a GET request to the area page
    response = requests.get(url_area)

    # Parse the HTML content of the area page
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all the links to boulder pages on the area page
    boulder_links = []
    for link in soup.find_all('a'):

        href = link.get('href')

        if not href or not href.endswith('.html'):
            continue

        boulder_linkname = href.split('/')[-1]

        if any(substring in boulder_linkname for substring in ['topo', 'circuit']):
            continue

        boulder_links.append(href)

    # Mapping associating boulder to all its images links
    dbMapping = {}

    # Set up Selenium webdriver with Chrome (interact with the browser)
    options = Options()
    options.add_argument('--headless')  # Set to False to see the browser window
    driver = webdriver.Chrome(options=options)

    # Loop through all the boulder links and download the boulder info
    for boulder_link in tqdm(boulder_links):

        boulder_url = f'https://bleau.info{boulder_link}'

        response = requests.get(boulder_url)

        if not response:
            continue

        # Load the boulder page with Selenium
        driver.get(boulder_url)

        # Find the "See more" button and click it to load all the images
        while True:
            try:
                more_button = driver.find_element(By.CLASS_NAME, 'load-more-variant-images')
                more_button.click()
                time.sleep(1)  # Wait for the images to load
            except:
                break

        # Extract the URLs of all the images on the page
        image_links = []
        for img in driver.find_elements(By.TAG_NAME, 'img'):

            src = img.get_attribute('src')

            if not src or not src.startswith('https://bleau.info/'):
                continue

            if any(substring in src for substring in ['favicon-', 'french-', 'english-']):
                continue

            # Download the image from the URL and save it to the specified path
            response = requests.get(src)
            img_title = src.split('/')[-1]
            local_img_path = os.path.join('..', 'data', area, img_title)
            with open(local_img_path, "wb") as f:
                f.write(response.content)

            image_links.append(src.split('/')[-1])

        dbMapping[boulder_url] = image_links

    # save dictionary to pkl file
    with open(f'../data/{area}/{area}.pkl', 'wb') as fp:
        pickle.dump(dbMapping, fp)

    driver.quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape images of Fontainebleau boulders from bleau.info ')
    parser.add_argument('area', metavar='area', type=str, help='the name of the area to scrape, as in the url of bleau.info webpage')
    args = parser.parse_args()

    area = args.area.lower()
    if not os.path.exists(f'../data/{area}'):
        os.makedirs(f'../data/{area}')

    scrape_boulders_images(area)
