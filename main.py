import os
import time
import requests
from dotenv import load_dotenv
from scraper import get_news_details
from translator import translate_and_refine

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_news_to_telegram(title, mm_title, mm_summary, image_url, source_link):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    
    # Heading ကို Bold လုပ်ပြီး emoji လေးတွေနဲ့ ပိုလန်းအောင်ပြင်ထားတယ်
    caption = (
        f"🔥 *{mm_title}*\n\n"
        f"📝 *သတင်းအနှစ်ချုပ် -*\n{mm_summary}\n\n"
        f"🌐 [မူရင်းသတင်းဖတ်ရန် ဒီကိုနှိပ်ပါ]({source_link})\n"
        f"───────────────\n"
        f"📌 _Original: {title}_"
    )
    
    payload = {
        "chat_id": CHAT_ID,
        "photo": image_url,
        "caption": caption,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            # ပုံပို့မရရင် text ပဲပို့မယ်
            text_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(text_url, json={"chat_id": CHAT_ID, "text": caption, "parse_mode": "Markdown", "disable_web_page_preview": False})
    except Exception as e:
        print(f"Telegram Connection Error: {e}")

def run_news_factory():
    print("\n🚀 --- AI News Bot System (Premium Version) --- 🚀")
    target_url = input("Enter news URL: ")
    
    if not target_url:
        target_url = "https://techcrunch.com/category/artificial-intelligence/"
    
    news_items = get_news_details(target_url) 
    
    if not news_items:
        print("❌ No news found!")
        return

    print(f"\n[+] အကြောင်းအရာ {len(news_items)} ခု တွေ့ရှိသည်။ ဘာသာပြန်နေသည်...\n")

    for i, item in enumerate(news_items, 1):
        # Title ကို ပြန်မယ်
        mm_title = translate_and_refine(item['title'])
        
        # Summary ကို ပိုရှည်ရှည်နဲ့ စိတ်ဝင်စားဖို့ကောင်းအောင် ပြန်ခိုင်းမယ်
        # (translator.py ထဲက prompt မှာ 'summarize in 3 bullet points' လို့ ထည့်ထားရင် ပိုမိုက်တယ်)
        mm_summary = translate_and_refine(item['summary'])
        
        print(f"[{i}] Sending: {mm_title[:40]}...")
        
        send_news_to_telegram(
            item['title'], 
            mm_title, 
            mm_summary, 
            item['image'], 
            item['link']
        )
        
        time.sleep(3)

    print("\n✅ လုပ်ဆောင်ချက်အားလုံး ပြီးဆုံးပါပြီ။ Telegram ကို စစ်ကြည့်လိုက်ပါ Dude!")

if __name__ == "__main__":
    run_news_factory()

