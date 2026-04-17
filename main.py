import os, requests
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from telegraph import Telegraph
from scraper import get_news_details, get_full_content
from translator import translate_and_refine
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def process_item(item, use_telegraph, chat_id):
    try:
        print(f"[*] Analyzing: {str(item['title'])[:40]}...")
        mm_title = str(translate_and_refine(item['title']))
        raw_summary_text = BeautifulSoup(str(item['summary']), "html.parser").get_text()
        mm_summary = str(translate_and_refine(raw_summary_text))

        link_footer = f'🔗 <a href="{item["link"]}">Original Source</a>'

        if use_telegraph:
            full_text_en = get_full_content(item['link'])
            try:
                mm_full = str(GoogleTranslator(source='auto', target='my').translate(full_text_en if full_text_en else raw_summary_text))
                tg = Telegraph()
                tg.create_account(short_name='AI_News_Bot')
                html_body = f"<figure><img src='{item['image']}'></figure><h3>{mm_title}</h3><hr><p>{mm_full.replace('\n', '<br>')}</p>"
                page = tg.create_page(title=mm_title[:100], html_content=html_body)
                link_footer = f'📖 <a href="https://telegra.ph/{page["path"]}">Full Article (Instant View)</a>\n\n{link_footer}'
            except: 
                pass

        caption = f"<b>🔥 {mm_title.upper()}</b>\n━━━━━━━━━━━━━━━\n\n<b>📝 Analysis:</b>\n{mm_summary}\n\n{link_footer}"

        # Telegram သို့ ပို့ဆောင်ခြင်း
        payload = {"chat_id": chat_id, "photo": item['image'], "caption": caption[:1024], "parse_mode": "HTML"}
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", json=payload, timeout=30)
        print(f"[+] Post Success to {chat_id}")
    except Exception as e:
        print(f"[-] Item Error: {e}")

def run(rss_links=None, mode="1", chat_id=None):
    """
    bot.py မှ လှမ်းခေါ်နိုင်ရန် run function ကို parameter များဖြင့် ပြင်ဆင်ထားသည်။
    """
    if not TOKEN: 
        return print("❌ Token missing!")
    
    # CLI ဖြင့် တိုက်ရိုက် run လျှင် input တောင်းမည်
    if rss_links is None:
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        mode = input("1. Fast | 2. Detailed: ")
        url = input("URL: ").strip() or "https://techcrunch.com/category/artificial-intelligence/feed/"
        rss_links = [url]

    print(f"[*] Target Chat ID: {chat_id}")
    print(f"[*] Processing {len(rss_links)} sources...")

    with ThreadPoolExecutor(max_workers=2) as ex:
        for url in rss_links:
            news = get_news_details(url)
            for item in news[:3]: # တစ်ကြိမ်လျှင် ၂-၃ ပုဒ်သာ စမ်းသပ်တင်ရန်
                ex.submit(process_item, item, mode == "2", chat_id)

if __name__ == "__main__":
    run()

