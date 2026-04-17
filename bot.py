import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# main.py မှ run function ကို ချိတ်ဆက်ခြင်း
from main import run

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Guide ပုံရိပ်
GUIDE_IMG = "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ပင်မလမ်းညွှန်ချက်စာမျက်နှာ"""
    
    if 'rss_links' not in context.user_data:
        context.user_data['rss_links'] = []
    if 'channel_id' not in context.user_data:
        context.user_data['channel_id'] = os.getenv("TELEGRAM_CHAT_ID", "")

    welcome_msg = (
        "<b>🤖 AI Content Automation System</b>\n\n"
        "ဤစနစ်သည် RSS Feed များမှတစ်ဆင့် အကြောင်းအရာမျိုးစုံကို အလိုအလျောက် စုစည်းဘာသာပြန်ဆိုပေးမည်ဖြစ်ပါသည်။\n\n"
        "<b>🛠 အသုံးပြုပုံ လမ်းညွှန်ချက်များ:</b>\n"
        "၁။ သင်၏ Channel တွင် Bot ကို <b>Admin</b> ခန့်အပ်ပါ။\n"
        "၂။ '⚙️ Channel သတ်မှတ်မည်' တွင် Channel @username ကို ပေးပို့ပါ။\n"
        "၃။ '🔗 RSS Link ထည့်သွင်းမည်' တွင် မိမိတင်လိုသော Link များ ထည့်သွင်းပါ။\n\n"
        "<b>🔎 Gemini အတွက် Prompt (Copy ယူပါ):</b>\n"
        "<code>Please provide a list of valid RSS feed URLs for [Content Type - e.g., Crypto Spot, AI News]. Ensure the links end in /feed/ or .xml.</code>"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 စတင်လုပ်ဆောင်မည်", callback_data='start_sync')],
        [InlineKeyboardButton("🔗 RSS Link ထည့်သွင်းမည်", callback_data='add_link')],
        [InlineKeyboardButton("⚙️ Channel သတ်မှတ်မည်", callback_data='set_channel')]
    ]
    
    if update.callback_query:
        await update.callback_query.message.delete()
        await update.callback_query.message.reply_photo(
            photo=GUIDE_IMG, caption=welcome_msg, 
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML'
        )
    else:
        await update.message.reply_photo(
            photo=GUIDE_IMG, caption=welcome_msg, 
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML'
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == 'add_link':
        await query.message.reply_text("🌐 <b>RSS Link ပေးပို့ခြင်း</b>\n\nကျေးဇူးပြု၍ RSS URL ကို ပေးပို့ပေးပါ (ဥပမာ- https://site.com/feed/):", parse_mode='HTML')
        context.user_data['waiting_for_link'] = True

    elif data == 'set_channel':
        await query.message.reply_text("📝 <b>Channel သတ်မှတ်ခြင်း</b>\n\nသင်၏ Channel @username ကို ပေးပို့ပေးပါ:", parse_mode='HTML')
        context.user_data['waiting_for_channel'] = True

    elif data == 'start_sync':
        links = context.user_data.get('rss_links', [])
        chat_id = context.user_data.get('channel_id')

        if not links:
            await query.message.reply_text("❌ ကျေးဇူးပြု၍ RSS Link အရင်ထည့်သွင်းပေးပါ။")
            return
        
        keyboard = [
            [InlineKeyboardButton("⚡ Fast Mode (အကျဉ်းချုပ်)", callback_data='run_1')],
            [InlineKeyboardButton("📖 Detailed Mode (အသေးစိတ်)", callback_data='run_2')],
            [InlineKeyboardButton("🔙 ပင်မစာမျက်နှာ", callback_data='main_menu')]
        ]
        await query.message.delete()
        await query.message.reply_photo(
            photo=GUIDE_IMG,
            caption=f"🎯 <b>တင်ဆက်မည့် ပုံစံရွေးချယ်ပါ</b>\n\nလက်ရှိ Link အရေအတွက်: {len(links)} ခု\nTarget: {chat_id}",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML'
        )

    elif data.startswith('run_'):
        mode = data.split('_')[1]
        links = context.user_data.get('rss_links')
        chat_id = context.user_data.get('channel_id')

        await query.message.reply_text("🔄 <b>လုပ်ဆောင်နေပါသည်...</b>\nContent များကို ပို့ဆောင်နေပါသည်။ ခေတ္တစောင့်ဆိုင်းပေးပါ...")
        
        run(rss_links=links, mode=mode, chat_id=chat_id)

        await query.message.reply_text("✅ <b>အောင်မြင်စွာ တင်ပြီးပါပြီ။</b>", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ပင်မစာမျက်နှာ", callback_data='main_menu')]]), 
            parse_mode='HTML'
        )

    elif data == 'main_menu':
        await start(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # RSS Link ထည့်သွင်းခြင်း (Loop ပတ်နိုင်အောင် ပြင်ဆင်ထားသည်)
    if context.user_data.get('waiting_for_link'):
        link = update.message.text.strip()
        if link.startswith('http'):
            context.user_data['rss_links'].append(link)
            
            keyboard = [
                [InlineKeyboardButton("➕ နောက်ထပ်ထည့်မည်", callback_data='add_link')],
                [InlineKeyboardButton("✅ ပြီးဆုံးပြီ (ပင်မစာမျက်နှာ)", callback_data='main_menu')]
            ]
            await update.message.reply_text(
                f"✅ Link ထည့်သွင်းပြီးပါပြီ။\n\nလက်ရှိ Link စုစုပေါင်း: {len(context.user_data['rss_links'])} ခု",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            context.user_data['waiting_for_link'] = False
        else:
            await update.message.reply_text("❌ Link ပုံစံမှားယွင်းနေပါသည်။ ပြန်လည်စစ်ဆေးပါ။")

    # Channel Username ထည့်သွင်းခြင်း
    elif context.user_data.get('waiting_for_channel'):
        username = update.message.text.strip()
        if username.startswith('@'):
            context.user_data['channel_id'] = username
            await update.message.reply_text(f"✅ Channel {username} အား သတ်မှတ်ပြီးပါပြီ။", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ပင်မစာမျက်နှာ", callback_data='main_menu')]]))
            context.user_data['waiting_for_channel'] = False

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 System is starting with improved UX...")
    app.run_polling()

