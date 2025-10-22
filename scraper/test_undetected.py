import os
import time
import random
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()

class UndetectedTwitterLogin:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        
        print("🚀 Initializing undetected Chrome...")
        options = uc.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--start-maximized')
        
        self.driver = uc.Chrome(options=options, version_main=None)
        self.wait = WebDriverWait(self.driver, 20)
    
    def human_type(self, element, text):
        """Type like a human with random delays"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def login(self):
        print("📱 Going to Twitter login...")
        self.driver.get("https://twitter.com/i/flow/login")
        time.sleep(random.uniform(3, 5))
        
        try:
            # Wait for username field
            print("⌨️  Entering username...")
            username_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='username']"))
            )
            time.sleep(random.uniform(1, 2))
            self.human_type(username_input, self.username)
            time.sleep(random.uniform(1, 2))
            username_input.send_keys(Keys.RETURN)
            
            # Wait for password field
            print("🔐 Entering password...")
            time.sleep(random.uniform(3, 5))
            password_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='current-password']"))
            )
            time.sleep(random.uniform(1, 2))
            self.human_type(password_input, self.password)
            time.sleep(random.uniform(1, 2))
            password_input.send_keys(Keys.RETURN)
            
            # Wait for login to complete
            print("⏳ Waiting for login...")
            time.sleep(5)
            
            # Check if we're on home page
            if "home" in self.driver.current_url or "x.com" in self.driver.current_url:
                print("✅ Login successful!")
                return True
            else:
                print("❌ Login failed - still on login page")
                return False
                
        except Exception as e:
            print(f"❌ Error during login: {e}")
            return False
    
    def scrape_tweet(self, tweet_url):
        """Scrape a single tweet"""
        print(f"\n📱 Scraping: {tweet_url}")
        self.driver.get(tweet_url)
        time.sleep(5)
        
        try:
            # Get tweet content
            tweet_element = self.wait.until(
                EC.presence_of_element_located((By.XPATH, '//article[@data-testid="tweet"]'))
            )
            
            # Extract text
            try:
                content = tweet_element.find_element(By.XPATH, './/div[@data-testid="tweetText"]').text
            except:
                content = "Could not extract content"
            
            # Extract user
            try:
                user = tweet_element.find_element(By.XPATH, './/div[@data-testid="User-Name"]//span').text
            except:
                user = "Unknown"
            
            print(f"✅ Successfully scraped!")
            print(f"   User: {user}")
            print(f"   Content: {content[:100]}...")
            
            return {
                "url": tweet_url,
                "user": user,
                "content": content
            }
            
        except Exception as e:
            print(f"❌ Error scraping tweet: {e}")
            return None
    
    def close(self):
        print("\n👋 Closing browser...")
        self.driver.quit()


# Test it
if __name__ == "__main__":
    scraper = UndetectedTwitterLogin(
        username=os.getenv("TWITTER_USERNAME"),
        password=os.getenv("TWITTER_PASSWORD")
    )
    
    if scraper.login():
        # Test scraping
        result = scraper.scrape_tweet("https://x.com/Ashcryptoreal/status/1977255774788444420")
        
        if result:
            print(f"\n📊 Result:")
            print(f"User: {result['user']}")
            print(f"Content: {result['content']}")
        
        input("\nPress Enter to close browser...")
    
    scraper.close()