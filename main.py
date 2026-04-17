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
SENT_LOG = "sent_news.txt"

def is_already_sent(link, chat_id):
    if not os.path.exists(SENT_LOG): return False
    unique_entry = f"{chat_id}|{link}"
    with open(SENT_LOG, "r") as f:
        return unique_entry in f.read()

def log_sent_news(link, chat_id):
    unique_entry = f"{chat_id}|{link}"
    with open(SENT_LOG, "a") as f:
        f.write(unique_entry + "\n")

def process_item(item, use_telegraph, chat_id):
    try:
        if is_already_sent(item['link'], chat_id):
            print(f"[-] Skipping: {str(item['title'])[:30]} (Already in {chat_id})")
            return

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
                # Fixed newline replacement
                html_body = f"<figure><img src='{item['image']}'></figure><h3>{mm_title}</h3><hr><p>{mm_full.replace('\\n', '<br>')}</p>"
                page = tg.create_page(title=mm_title[:100], html_content=html_body)
                link_footer = f'📖 <a href="https://telegra.ph/{page["path"]}">Full Article (Instant View)</a>\n\n{link_footer}'
            except:
                pass

        caption = f"<b>🔥 {mm_title.upper()}</b>\n━━━━━━━━━━━━━━━\n\n<b>📝 Analysis:</b>\n{mm_summary}\n\n{link_footer}"
        payload = {"chat_id": chat_id, "photo": item['image'], "caption": caption[:1024], "parse_mode": "HTML"}
        
        res = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", json=payload, timeout=30)
        if res.status_code == 200:
            log_sent_news(item['link'], chat_id)
            print(f"[+] Post Success to {chat_id}")
    except Exception as e:
        print(f"[-] Item Error: {e}")

def run(rss_links=None, mode="1", chat_id=None):
    if not TOKEN or not rss_links: return
    print(f"[*] Processing {len(rss_links)} sources for {chat_id} (Mode: {mode})...")
    with ThreadPoolExecutor(max_workers=2) as ex:
        for url in rss_links:
            news = get_news_details(url)
            for item in news:
                ex.submit(process_item, item, mode == "2", chat_id)

