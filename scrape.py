from selenium import webdriver
from bs4 import BeautifulSoup
import re
import os
import urllib.request
from IPython import embed

base_driver = webdriver.Firefox()
base_driver.set_window_size(1120, 550)
save_directory = ""
base_url = 'https://rpg.rem.uz/'

# Start at parent folder (DND 5th Ed For Now)
base_driver.get(base_url + "Dungeons%20%26%20Dragons/D%26D%205th%20Edition/")
# Get all links from parent folder
innerHTML = base_driver.page_source
soup = BeautifulSoup(innerHTML, "lxml")
base_driver.close()

page_body = soup.find('body')
folder_links = page_body.find_all('a')

for folder_link in folder_links:
    if re.findall('(/_h5ai/public/images/themes/default/folder.svg)', str(folder_link)):
        split_folder_link = folder_link.prettify(formatter=None).split("\"")
        if split_folder_link.index(' title=') is -1:
            continue
        current_dir = save_directory + split_folder_link[split_folder_link.index(' title=') + 1]
        current_folder_url = base_url + split_folder_link[1]

        sub_driver = webdriver.Firefox()
        sub_driver.set_window_size(1120, 550)
        sub_driver.get(current_folder_url)
        innerHTML = sub_driver.page_source
        soup = BeautifulSoup(innerHTML, "lxml")
        sub_driver.quit()

        # Pull all text from the BodyText div
        links = soup.find_all('a')

        for link in links:
            if not os.path.exists(current_dir):
                os.makedirs(current_dir)
            if re.findall('(.pdf)', str(link)):
                split_link = link.prettify(formatter=None).split("\"")
                print("Dir: " + current_dir)
                print("split_folder_link: " + str(split_link))
                url_name = base_url + split_link[split_folder_link.index('<a href=') + 1]
                file_name = split_link[split_folder_link.index(' title=') + 1]
                download(url_name, current_dir + '/' + file_name)
