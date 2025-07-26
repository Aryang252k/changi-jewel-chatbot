from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse
import re
import json


def get_urls_mainpg(url):
    """Extract href from home page"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, timeout=60000)
            time.sleep(2) 
        except PlaywrightTimeoutError as e:
             print(f"PlaywrightTimeoutError: {e}")
             print(f"Retring:{url}")
             page.goto(url, timeout=60000)
             time.sleep(2) 

        html = page.content()
        browser.close()
        soup = BeautifulSoup(html, "html.parser")
        [s.decompose() for s in soup(["script", "style"])]
        a=soup.find_all("a")
        return set([i.get('href') for i in a])

def scrape_page(url,max_retries = 3 ):
    """Extract page text with up to 3 retry attempts on timeout"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page_loaded = False
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1} to fetch: {url}")
                page.goto(url, timeout=60000)
                time.sleep(2)
                page_loaded = True
                break   
            except PlaywrightTimeoutError as e:
                print(f"PlaywrightTimeoutError on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:  
                    print(f"Failed to fetch {url} after {max_retries} attempts")
                    browser.close()
                    return None
                else:
                    print(f"Retrying to fetch: {url}")
            except Exception as e: 
                print(f"Unexpected error on attempt {attempt + 1}: {e}") 
                if attempt == max_retries - 1: 
                    print(f"Failed to fetch {url} after {max_retries} attempts")
                    browser.close()
                    return None
                else:
                    print(f"Retrying to fetch: {url}")
        
        if not page_loaded:
            browser.close()
            return None
        
        try:
            html = page.content()
            browser.close()
            soup = BeautifulSoup(html, "html.parser")
            [s.decompose() for s in soup(["script", "style", "footer", "nav"])]
            text = soup.get_text(separator="\n")
            
            if text:
                return text.strip()
            else:
                return None
                
        except Exception as e:
            print(f"Error processing page content: {e}")
            browser.close()
            return None
               
def clean_and_classify_urls(urls):
    """Clear and claassify_urls"""
    pages = []
    for url in urls:
        if not url or url.startswith("#") or url.startswith("javascript:"):
            continue  # Skip invalid URLs
        
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        path = parsed.path.lower()
 
        if "jewelchangiairport.com" in netloc:
                    location = "jewel"
        elif "changiairport.com" in netloc:
            location = "changi"
        
        else:
            continue  

        # Extract section from path heuristically
        section = "home"
        path_parts = [p for p in path.split("/") if p and p != "in" and p != "en"]
        if path_parts:
            section_guess = path_parts[-1].replace("-", " ").replace(".html", "")
            section_guess = re.sub(r'\W+', ' ', section_guess).strip()
            section = section_guess or "unknown"

        pages.append({
            "url": url,
            "location": location,
            "section": section
        })

    return pages

def save_json(urls,all_links):
        print(f"Total nunmber of links to extract : {len(urls)}")
        pages_to_scrape = clean_and_classify_urls(urls)
        scraped_data = []
        for page in pages_to_scrape:
            content = scrape_page(page["url"])
            if content:
                scraped_data.append({
                    "text": content,
                    "metadata": {
                        "source": page["url"],
                        "location": page["location"],
                        "section": page["section"]
                    }
                })
                print(f"Completed url:{page["url"]}")

        scraped_data.append({
                "text": str(all_links),
                "metadata": {
                    "source": "Social media links and changi app apple and playstore app download links",
                    "location": '',
                    "section": "Both changi and jewel social media links and changi app apple and playstore app download links"
                }
            })
        
        print("Data saved to ./data/scraped_changi_jewel.json")
        with open("./data/scraped_changi_jewel.json", "w") as f:
            json.dump(scraped_data, f, indent=2)

def filter_urls(urls,base):
    filter_ls=["facebook","instagram","linkedin","Telegram","tiktok","x.com","youtube","wechat","weibo","xiaohongshu","t.me","whatsapp","apps.apple","play.google"]
    connect_ls=[]
    filtered_ls=[]
    for u in urls:
        flag=True
        if u:
            if u.startswith("/"):
                u=base+u

            for i in filter_ls:
                if i in u:
                    connect_ls.append(u)
                    flag=False 

            if flag:
                filtered_ls.append(u)

    return filtered_ls,connect_ls
    
        

#main funtion generate json data
def generate_data_json():
    websites=["https://www.changiairport.com","https://www.jewelchangiairport.com"]
    all_links=[]
    extr_urls=[]
 
    for url in websites:
        print(f"Url extration started for {url}")
        urls_uf=get_urls_mainpg(url=url)
        urls,sm_urls=filter_urls(urls=urls_uf,base=url)
        all_links.extend(sm_urls)
        extr_urls.extend(urls)
       
    save_json(urls=extr_urls,all_links=all_links)

