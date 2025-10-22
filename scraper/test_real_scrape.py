
import os
from dotenv import load_dotenv
from twitter_scraper import Twitter_Scraper

load_dotenv()

scraper = Twitter_Scraper(
    mail=os.getenv("TWITTER_MAIL"),
    username=os.getenv("TWITTER_USERNAME"),
    password=os.getenv("TWITTER_PASSWORD"),
    headlessState="no"  # or "no" to see browser
)

print("Logging in...")
scraper.login()

print("\nScraping real tweet...")
result = scraper.scrape_single_tweet("https://x.com/Ashcryptoreal/status/1977255774788444420")

if result:
    print("\n✅ SUCCESS!")
    print(f"User: {result['user']}")
    print(f"Content: {result['content']}")
    print(f"Likes: {result['likes']}")
else:
    print("\n❌ Failed")

scraper.driver.close()