import undetected_chromedriver as uc
from time import sleep
from selenium.webdriver.common.keys import Keys
import random

class UndetectedTwitterScraper:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        
        options = uc.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        self.driver = uc.Chrome(options=options)
        self.driver.maximize_window()
    
    def login(self):
        self.driver.get("https://twitter.com/i/flow/login")
        sleep(5)  # Let page fully load
        
        # Username
        username_field = self.driver.find_element("xpath", "//input[@autocomplete='username']")
        for char in self.username:
            username_field.send_keys(char)
            sleep(random.uniform(0.1, 0.3))
        sleep(2)
        username_field.send_keys(Keys.RETURN)
        sleep(5)
        
        # Password
        password_field = self.driver.find_element("xpath", "//input[@autocomplete='current-password']")
        for char in self.password:
            password_field.send_keys(char)
            sleep(random.uniform(0.1, 0.3))
        sleep(2)
        password_field.send_keys(Keys.RETURN)
        sleep(5)
        
        print("Login successful!")

# Test it
scraper = UndetectedTwitterScraper("your_username", "your_password")
scraper.login()
input("Press Enter to close...")
scraper.driver.quit()