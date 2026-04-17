import feedparser
import cloudscraper
from bs4 import BeautifulSoup
import time
import re

# Backup Image အတွက်
BACKUP_IMG = "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800"

def get_news_details(url):
    """RSS Feed ကနေ သတင်းခေါင်းစဉ်၊ ပုံနဲ့ Link တွေကို ဆွဲထုတ်ပေးမယ့် Function"""
    rss_url = url
    # TechCrunch အတွက် special case
    if "techcrunch.com" in url and "feed" not in url:
        rss_url = "https://techcrunch.com/category/artificial-intelligence/feed/"
    
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )
    
    try:
        feed = feedparser.parse(rss_url)
    except Exception as e:
        print(f"[*] Feed Error: {e}")
        return []

    results = []
    for entry in feed.entries[:8]: # နောက်ဆုံး ၈ ခုပဲယူမယ်
        img_url = ""
        try:
            # ၁။ RSS ထဲမှာ ပုံပါမပါ အရင်ရှာမယ်
            if 'media_content' in entry:
                img_url = entry.media_content[0]['url']
            elif 'links' in entry:
                for link in entry.links:
                    if 'image' in link.get('type', ''):
                        img_url = link.get('href', '')

            # ၂။ ပုံမတွေ့ရင် Website ထဲဝင်ပြီး Meta Tags တွေမှာ ထပ်ရှာမယ်
            if not img_url or "placeholder" in img_url:
                r = scraper.get(entry.link, timeout=10)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    # og:image, twitter:image သို့မဟုတ် ပထမဆုံး article image ကို ရှာမယ်
                    meta_img = soup.find("meta", property="og:image") or \
                               soup.find("meta", attrs={"name": "twitter:image"})
                    if meta_img:
                        img_url = meta_img.get("content", "")
        except:
            pass

        results.append({
            'title': entry.title,
            'summary': entry.get('summary', entry.title),
            'link': entry.link,
            'image': img_url if img_url else BACKUP_IMG
        })
        time.sleep(0.3) # Rate limit ရှောင်ရန်
        
    return results

def get_full_content(url):
    """သတင်း link ထဲဝင်ပြီး စာသားအပြည့်အစုံကို Missing မဖြစ်အောင် ဆွဲထုတ်ပေးမယ့် Function"""
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )
    
    try:
        res = scraper.get(url, timeout=15)
        if res.status_code != 200: return None
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # မလိုတဲ့ အစိတ်အပိုင်းတွေကို အကုန်ဖယ်မယ်
        for s in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'iframe', 'button', 'ad']):
            s.decompose()

        # Content ကို ရှာဖွေမယ့် Priority List (Missing ဖြစ်တာကို ကာကွယ်ဖို့)
        content = None
        
        # ၁။ Standard Tags
        content = soup.find(['article', 'main'])
        
        # ၂။ Common Class Names (Regex သုံးပြီး ပိုကျယ်ပြန့်အောင် ရှာမယ်)
        if not content:
            content = soup.find('div', class_=re.compile(r'article|post-content|entry-content|main-content|story-body', re.I))
        
        # ၃။ IDs
        if not content:
            content = soup.find('div', id=re.compile(r'article|content|main', re.I))

        # ၄။ Last Resort - Body Paragraphs
        target = content if content else soup.body
        
        if not target: return None

        paragraphs = target.find_all('p')
        # စာလုံးရေ ၅၀ ကျော်တဲ့ စာပိုဒ်တွေကိုပဲ စုစည်းမယ်
        full_text_list = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50]
        
        # Telegram Message Limit အတွက် စာသားကို ဖြတ်တောက်မယ် (ဥပမာ- စာလုံးရေ ၃၅၀၀ ဝန်းကျင်)
        full_text = "\n\n".join(full_text_list)
        
        if len(full_text) > 3500:
            full_text = full_text[:3500] + "...\n\n(စာသားအပြည့်အစုံဖတ်ရန် Link ကို နှိပ်ပါ)"

        return full_text if len(full_text) > 150 else None
        
    except Exception as e:
        print(f"[*] Scraper Error: {e}")
        return None

