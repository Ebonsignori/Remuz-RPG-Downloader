from threading import Event, Thread
from tkinter import Tk, ttk
from urllib.request import urlretrieve
import tkinter as tk
from selenium import webdriver
from bs4 import BeautifulSoup
import re
import os
from sys import exit
from tkinter import filedialog, simpledialog
import webbrowser
from IPython import embed


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master, relief="raised", bd=2)
        self.master = master

        # Global variables
        self.base_url = 'https://rpg.rem.uz/'
        self.trying_to_quit = False
        self.current_directory = '/'

        # Create toplevel menu
        menubar = tk.Menu(master)
        menubar.add_command(label="About", command=self.about_window)
        menubar.add_separator()
        menubar.add_command(label="Help", command=self.help_window)
        master.config(menu=menubar)

        # Create and place widgets
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        # Main scrape functionality
        self.main_frame = tk.Frame()
        self.main_frame.pack(fill="x", expand="true")

        # Choose parent directory to download content from
        self.first_frame = tk.Frame(self.main_frame)
        self.first_frame.pack(side='top', pady="5")
        self.first_label = tk.Label(self.first_frame, text="Step 1:")
        self.first_label.pack(side='left', padx='1')
        self.base_directory_btn = tk.Button(self.first_frame, text="URL to parent Remuz RPG Directory",
                                         command=self.prompt_url)
        self.base_directory_btn.pack()

        # Choose local directory for saving contents of Remuz directory scraping
        self.second_frame = tk.Frame(self.main_frame)
        self.second_frame.pack(pady="5")
        self.second_label = tk.Label(self.second_frame, text="Step 2:")
        self.second_label.pack(side='left', padx='1')
        self.save_btn = tk.Button(self.second_frame, text="Choose Local Save Location", command=self.save_location)
        self.save_btn.pack()
        self.save_btn['state'] = 'disabled'

        # Begin scrape if base directory and local save location are selected
        self.third_frame = tk.Frame(self.main_frame)
        self.third_frame.pack(pady="10")
        self.third_label = tk.Label(self.third_frame, text="Step 3:")
        self.third_label.pack(side='left', padx='1')
        self.scrape_btn = tk.Button(self.third_frame, text="Scrape", command=self.scrape)
        self.scrape_btn.pack()
        self.scrape_btn['state'] = 'disabled'

        # Scrape Options
        self.selection_frame = tk.Frame()
        self.selection_frame.pack(fill="x", expand="true", pady='15')
        self.selections_label = tk.Label(self.selection_frame, text="Options:")
        self.selections_label.pack(side='top')

        # Check if subdirectories of subdirectories should be downloaded
        self.check_subfolders = tk.BooleanVar()
        self.check_subfolders_btn = tk.Checkbutton(self.selection_frame, text="Download All Subfolders of Subfolders", variable=self.check_subfolders)
        self.check_subfolders_btn.pack()
        # Options to exclude certain files
        self.exclude_pdf = tk.BooleanVar() # Option to exclude .pdf files
        self.exclude_pdf_btn = tk.Checkbutton(self.selection_frame, text="Exclude .pdf Files",
                                                   variable=self.exclude_pdf)
        self.exclude_pdf_btn.pack()
        self.exclude_mp3 = tk.BooleanVar()  # Option to exclude .mp3 files
        self.exclude_mp3_btn = tk.Checkbutton(self.selection_frame, text="Exclude .mp3 Files",
                                              variable=self.exclude_mp3)
        self.exclude_mp3_btn.pack()
        self.exclude_txt = tk.BooleanVar()  # Option to exclude .txt files
        self.exclude_txt_btn = tk.Checkbutton(self.selection_frame, text="Exclude .txt Files",
                                              variable=self.exclude_txt)
        self.exclude_txt_btn.pack()
        self.exclude_png = tk.BooleanVar()  # Option to exclude .png files
        self.exclude_png_btn = tk.Checkbutton(self.selection_frame, text="Exclude .png Files",
                                              variable=self.exclude_png)
        self.exclude_png_btn.pack()
        self.exclude_jpg = tk.BooleanVar()  # Option to exclude .jpg files
        self.exclude_jpg_btn = tk.Checkbutton(self.selection_frame, text="Exclude .jpg Files",
                                              variable=self.exclude_jpg)
        self.exclude_jpg_btn.pack()

        # Download progress labels
        self.status_frame = tk.Frame()
        self.status_frame.pack(fill="x", expand="true", pady='5')

        # Folder download progress current/total folders
        self.folder_progress_text = tk.StringVar()
        self.folder_progress = tk.Label(self.status_frame, textvariable=self.folder_progress_text)
        self.folder_progress_text.set("Folder Progress: ")
        self.folder_progress.pack()
        # File download progress current/total files in current folder
        self.file_progress_text = tk.StringVar()
        self.file_progress = tk.Label(self.status_frame, textvariable=self.file_progress_text)
        self.file_progress_text.set("Files In Folder Progress: ")
        self.file_progress.pack()

        self.stop_btn = tk.Button(self.status_frame, text="Stop / Quit (Remembers where it left off)", command=self.stop_scrape)
        self.stop_btn.pack(side='bottom', pady='5')
        self.stop_btn['state'] = 'disabled'

    def prompt_url(self):
        """Simple dialog top window that prompts user for url of parent Remuz folder for scraping"""
        self.save_btn['state'] = 'disabled' # Disable next step until a valid url is entered by user
        self.starting_point = simpledialog.askstring("URL:", "DND 5E Example: https://rpg.rem.uz/Dungeons%20%26%20Dragons/")

        # Validate URL regex
        regex = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        # Prompt until valid URL is entered
        while (True):
            if regex.search(self.starting_point) and self.starting_point is not None:
                self.save_btn['state'] = 'normal' # Enable next step when valid url is entered by user
                break
            else:
                self.starting_point = simpledialog.askstring("Invalid URL, Try Again:",
                                                             "DND 5E Example: https://rpg.rem.uz/Dungeons%20%26%20Dragons/")

    def save_location(self):
        """Directory save dialog that prompts for location to save Remuz scraping results"""
        self.save_directory = filedialog.askdirectory()
        self.scrape_btn['state'] = 'normal' # Enable next step when valid directory is selected

    def update_folder_progress(self):
        self.folder_progress_text.set("Folder Progress: " + str(self.current_folder) + " / " + str(self.total_folders))
        self.update()

    def update_file_progress(self):
        self.file_progress_text.set("File Progress: " + str(self.current_file) + " / " + str(self.total_files))
        self.update()

    def get_files(self, current_dir, file_links):
        self.current_file = 0
        self.total_files = len(file_links)
        self.update_file_progress()  # Update total file status

        # Download each file in directory
        for link in file_links:
            if self.trying_to_quit:
                break

            # Update progress
            self.current_file += 1
            self.update_file_progress()

            # Get url name for downloading and file name for saving
            url_name = link.find('a', href=True)['href'] # Get href attribute
            file_name = link.find("span", title=True)['title'] # Get title attribute
            # Check if file is excluded
            if self.exclude_pdf.get():
                if len(re.findall('(\.pdf)$', file_name)) >= 1:
                    continue
            if self.exclude_mp3.get():
                if len(re.findall('(\.mp3)$', file_name)) >= 1:
                    continue
            if self.exclude_txt.get():
                if len(re.findall('(\.txt)$', file_name)) >= 1:
                    continue
            if self.exclude_png.get():
                if len(re.findall('(\.png)$', file_name)) >= 1:
                    continue
            if self.exclude_jpg.get():
                if len(re.findall('(\.jpg)$', file_name)) >= 1:
                    continue
            # Check that file doesn't already exists, and if  it doesn't download file
            print("here2")
            if os.path.isfile(current_dir + '/' + file_name):
                continue
            self.download(self.base_url + url_name, current_dir + '/' + file_name) # Download file

    def scrape(self):
        """Main program logic. Scrapes from directories starting at the starting directory as specified by user,
         and calls download_directory() to download contents of each sub directory and itself"""

        self.base_driver = webdriver.Firefox()  # Firefox webdriver for scraping JS pages
        self.base_driver.set_window_size(5, 5)

        # Disable buttons to prevent interruption
        self.scrape_btn['state'] = 'disabled'
        self.save_btn['state'] = 'disabled'
        self.base_directory_btn['state'] = 'disabled'
        self.stop_btn['state'] = 'normal' # Enable stop button
        self.trying_to_quit = False

        # Start at parent folder and extract innerHTML
        self.base_driver.get(self.starting_point)
        innerHTML = self.base_driver.page_source
        soup = BeautifulSoup(innerHTML, "lxml")
        page_body = soup.find("div", {"id": "view"}) # Get relevant content from innerHTML

        # Get all subdirectories from current directory
        directory_links = page_body.select('[class="item folder"]')
        self.current_folder = 0
        self.total_folders = len(directory_links)
        self.update_folder_progress() # Update total folder status

        # Get all files in current directory
        file_links = page_body.select('[class="item file"]')
        self.get_files(self.save_directory, file_links)

        for directory_link in directory_links:
            if self.trying_to_quit:
                break
            self.current_folder += 1
            self.update_folder_progress()  # Update total folder status
            directory_name = directory_link.find("span", title=True)['title']
            directory_url = directory_link.find('a', href=True)['href']
            self.scrape_directory(directory_name, directory_url)

    def scrape_directory(self, directory_name, directory_url):
        full_directory_path = self.save_directory + "/" + directory_name
        if not os.path.exists(full_directory_path):
            os.makedirs(full_directory_path)
            print("making directory: " + full_directory_path)
        # Get current directory's innerHTML
        self.base_driver.get(self.base_url + directory_url)
        innerHTML = self.base_driver.page_source
        soup = BeautifulSoup(innerHTML, "lxml")

        page_body = soup.find("div", {"id": "view"})  # Get relevant content from innerHTML

        # If getting subdirectories of subdirectories, update total folder and get directory links
        if self.check_subfolders.get():
            directory_links = page_body.select('[class="item folder"]')
            # Check that there are subdirectories
            if len(directory_links) is not 0:
                self.total_folders += len(directory_links) # Update count to include subdirectories
                # Recursively download each directories contents
                for directory_link in directory_links:
                    print("here")
                    self.current_folder += 1
                    sub_directory = directory_name + '/' + directory_link.find("span", title=True)['title']
                    sub_url = directory_link.find("span", title=True)['href']
                    self.scrape_directory(sub_directory, sub_url)

        # Get all files in current directory
        file_links = page_body.select('[class="item file"]')
        self.get_files(full_directory_path, file_links)

    def download(self, url, filename):
        """Url retrieve wrapper that provides a progress bar in a new tkinter window when downloading from url"""
        root = progressbar = quit_id = None
        ready = Event()

        def reporthook(blocknum, blocksize, totalsize):
            nonlocal quit_id
            if blocknum == 0:  # started downloading
                def guiloop():
                    nonlocal root, progressbar
                    root = Tk()
                    root.lift()
                    progressbar = ttk.Progressbar(root, length=400)
                    progressbar.grid()
                    # show progress bar if the download takes more than .5 seconds
                    root.after(500, root.deiconify)
                    ready.set()  # gui is ready
                    root.mainloop()

                Thread(target=guiloop).start()
            ready.wait(1)  # wait until gui is ready
            percent = blocknum * blocksize * 1e2 / totalsize  # assume totalsize > 0
            if quit_id is None:
                root.title('%%%.0f %s' % (percent, filename,))
                progressbar['value'] = percent  # report progress
                if percent >= 100:  # finishing download
                    quit_id = root.after(0, root.destroy)  # close GUI

        return urlretrieve(url, filename, reporthook)

    def stop_scrape(self):
        self.trying_to_quit = True
        stop_window = tk.Toplevel()
        first_text = tk.Label(stop_window, text="Wait Until Current Download Is Finished!")
        first_text.pack()
        second_text = tk.Label(stop_window, text="If run again, choose same directory and url to resume from where you left off")
        second_text.pack()
        stop_window.focus()
        # Quit Button
        stop_btn = tk.Button(stop_window, text="Quit", command=self.quit)
        stop_btn.pack(pady='5')

    def quit(self):
        self.base_driver.close()
        exit(0)

    def help_window(self):
        help_top_window = tk.Toplevel()
        help_top_window.focus()
        first_text = tk.Label(help_top_window, text="Read the GitHub for a tutorial:")
        first_text.pack()
        github_link = tk.Label(help_top_window, text="Github Link", fg="blue", cursor="hand2")
        github_link.bind("<Button-1>", lambda x: webbrowser.open_new(r"https://github.com/Ebonsignori/Remuz-RPG-Downloader"))
        github_link.pack(pady='5')

        second_text = tk.Label(help_top_window, text="For any questions not answered in the GitHub, email me at:")
        second_text.pack(pady='5')
        email_link = tk.Label(help_top_window, text="evan@ebonsignori.com", fg="blue", cursor="hand2")
        email_link.bind("<Button-1>", lambda x: webbrowser.open_new(r"mailto:evan@evanbonsignori.com"))
        email_link.pack(pady='5')

    def about_window(self):
        about_top_window = tk.Toplevel()
        about_top_window.focus()
        first_text = tk.Label(about_top_window, text="Read the GitHub for a tutorial:")
        first_text.pack()
        github_link = tk.Label(about_top_window, text="Github Link", fg="blue", cursor="hand2")
        github_link.bind("<Button-1>",
                         lambda x: webbrowser.open_new(r"https://github.com/Ebonsignori/Remuz-RPG-Downloader"))
        github_link.pack(pady='5')

        second_text = tk.Label(about_top_window, text="For any questions not answered in the GitHub, email me at:")
        second_text.pack(pady='5')
        email_link = tk.Label(about_top_window, text="evan@ebonsignori.com", fg="blue", cursor="hand2")
        email_link.bind("<Button-1>", lambda x: webbrowser.open_new(r"mailto:evan@evanbonsignori.com"))
        email_link.pack(pady='5')


# Application entry point and GUI loop
if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    app.master.title("Remuz RPG Downloader") # Window title
    root.resizable(width=False, height=False) # Window is fixed
    root.geometry('{}x{}'.format(275, 425)) # Window Dimensions
    app.mainloop()
