import cloudscraper
from bs4 import BeautifulSoup

def get_news_details(url):
    scraper = cloudscraper.create_scraper()
    print(f"Connecting to {url}...")
    
    try:
        response = scraper.get(url, timeout=15)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # TechCrunch ရဲ့ current structure အရ loop-card သို့မဟုတ် post-block တွေကို ရှာမယ်
        articles = soup.find_all('div', class_='loop-card') or soup.find_all('article')
        
        results = []
        for article in articles[:10]:
            # Title & Link
            title_tag = article.find('h3') or article.find('h2')
            if not title_tag: continue
            
            link_tag = title_tag.find('a', href=True)
            title = title_tag.get_text(strip=True)
            link = link_tag['href'] if link_tag else ""

            # Image
            img_tag = article.find('img')
            image_url = img_tag.get('src') or img_tag.get('data-src') if img_tag else "https://via.placeholder.com/800x400.png?text=AI+News"

            # Summary
            summary_tag = article.find('div', class_='loop-card__content') or article.find('p')
            summary = summary_tag.get_text(strip=True) if summary_tag else "No summary available."

            if len(title) > 10:
                results.append({
                    'title': title,
                    'summary': summary,
                    'link': link,
                    'image': image_url
                })
        
        return results

    except Exception as e:
        print(f"Scraper Error: {e}")
        return []

