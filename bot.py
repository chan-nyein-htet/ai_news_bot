import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from main import run

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GUIDE_IMG = "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800"

def init_data(context):
    if 'channels' not in context.bot_data:
        context.bot_data['channels'] = {}

async def auto_sync_wrapper(context: ContextTypes.DEFAULT_TYPE):
    """JobQueue အတွက် Error ကင်းသော sync logic"""
    channels = context.bot_data.get('channels', {})
    for ch, links in channels.items():
        if links:
            run(rss_links=links, mode="1", chat_id=ch)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_data(context)
    welcome_msg = (
        "<b>🤖 AI Content Automation System (v2.3)</b>\n\n"
        "<b>💡 Gemini Prompt အသုံးပြုနည်း:</b>\n"
        "အောက်ပါ Prompt ကို Copy ကူးပြီး Gemini (AI) တွင် မေးမြန်းခြင်းဖြင့် မိမိလိုချင်သော သတင်းများ၏ RSS Feed Link များကို ရှာဖွေနိုင်ပါသည်။\n\n"
        "<code>Please provide a list of valid RSS feed URLs for [Topic]. Ensure the links end in /feed/ or .xml.</code>\n\n"
        "<b>📖 အသုံးပြုပုံ:</b>\n"
        "၁။ Channel တွင် Bot ကို Admin ခန့်ပါ။\n"
        "၂။ Channel သတ်မှတ်ပြီး Link များထည့်ပါ။\n"
        "၃။ Bot မှ ၄ နာရီတစ်ခါ အလိုအလျောက် သတင်းတင်ပေးပါမည်။"
    )
    keyboard = [
        [InlineKeyboardButton("🔄 လက်ရှိသတင်းတင်မည်", callback_data='start_sync')],
        [InlineKeyboardButton("➕ New Channel Setup", callback_data='add_new')],
        [InlineKeyboardButton("⚙️ Manage Links & Settings", callback_data='view_details')]
    ]
    
    if update.callback_query:
        await update.callback_query.message.delete()
        await update.callback_query.message.reply_photo(photo=GUIDE_IMG, caption=welcome_msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    else:
        await update.message.reply_photo(photo=GUIDE_IMG, caption=welcome_msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'add_new':
        await query.message.reply_text("📝 <b>Step 1:</b> Channel @username ကို ပေးပို့ပါ:", parse_mode='HTML')
        context.user_data['waiting_for_channel'] = True

    elif query.data == 'view_details':
        channels = context.bot_data.get('channels', {})
        if not channels:
            await query.message.reply_text("❌ ဘာမှ မသတ်မှတ်ရသေးပါ။", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='main_menu')]]))
            return
        
        text = "<b>📋 လက်ရှိ Channel နှင့် Link များ:</b>\n\n"
        keyboard = []
        for ch in channels.keys():
            text += f"🎯 <b>{ch}</b> ({len(channels[ch])} links)\n"
            keyboard.append([InlineKeyboardButton(f"🛠 Manage {ch}", callback_data=f"manage_{ch}")])
        
        keyboard.append([InlineKeyboardButton("🔙 ပင်မစာမျက်နှာ", callback_data='main_menu')])
        await query.message.reply_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith('manage_'):
        ch = query.data.replace('manage_', '')
        links = context.bot_data['channels'].get(ch, [])
        text = f"🎯 <b>Channel: {ch}</b>\n\n"
        for i, link in enumerate(links):
            text += f"{i+1}. {link}\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ Link အသစ်ထည့်မည်", callback_data=f"addlink_{ch}")],
            [InlineKeyboardButton("🗑 Link အားလုံးဖျက်မည်", callback_data=f"clear_{ch}")],
            [InlineKeyboardButton("🔙 Back", callback_data='view_details')]
        ]
        await query.message.reply_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith('addlink_'):
        ch = query.data.replace('addlink_', '')
        context.user_data['current_ch'] = ch
        context.user_data['waiting_for_link'] = True
        await query.message.reply_text(f"🌐 <b>{ch}</b> အတွက် RSS Link ပေးပို့ပါ:")

    elif query.data.startswith('clear_'):
        ch = query.data.replace('clear_', '')
        context.bot_data['channels'][ch] = []
        await query.message.reply_text(f"✅ {ch} မှ Link အားလုံးကို ဖျက်လိုက်ပါပြီ။")
        await start(update, context)

    elif query.data == 'start_sync':
        keyboard = [
            [InlineKeyboardButton("⚡ Fast Mode", callback_data='run_1'), InlineKeyboardButton("📖 Detailed Mode", callback_data='run_2')],
            [InlineKeyboardButton("🔙 ပင်မစာမျက်နှာ", callback_data='main_menu')]
        ]
        await query.message.reply_text("🎯 <b>တင်ဆက်မည့် ပုံစံရွေးချယ်ပါ:</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

    elif query.data.startswith('run_'):
        mode = query.data.split('_')[1]
        channels = context.bot_data.get('channels', {})
        await query.message.reply_text("🔄 <b>အသစ်များကို စစ်ဆေးနေပါသည်...</b>")
        for ch, links in channels.items():
            if links: run(rss_links=links, mode=mode, chat_id=ch)
        await query.message.reply_text("✅ လုပ်ဆောင်ချက် ပြီးဆုံးပါပြီ။")

    elif query.data == 'main_menu':
        await start(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_for_channel'):
        ch_id = update.message.text.strip()
        if ch_id.startswith('@'):
            context.user_data['current_ch'] = ch_id
            context.user_data['waiting_for_channel'] = False
            context.user_data['waiting_for_link'] = True
            await update.message.reply_text(f"✅ Target: <b>{ch_id}</b>\n\n🌐 <b>Step 2:</b> RSS Link ကို ပေးပို့ပါ:", parse_mode='HTML')
        else:
            await update.message.reply_text("❌ @username ပုံစံဖြင့် ပေးပို့ပါ။")

    elif context.user_data.get('waiting_for_link'):
        link = update.message.text.strip()
        ch_id = context.user_data.get('current_ch')
        init_data(context)
        
        if link.startswith('http'):
            ch_links = context.bot_data['channels'].setdefault(ch_id, [])
            if link in ch_links:
                await update.message.reply_text("⚠️ ဤ Link သည် ထည့်ပြီးသားဖြစ်နေသည်။")
            else:
                ch_links.append(link)
                keyboard = [[InlineKeyboardButton("➕ ထပ်ထည့်မည်", callback_data=f"addlink_{ch_id}")], [InlineKeyboardButton("✅ ပြီးပြီ", callback_data='main_menu')]]
                await update.message.reply_text(f"✅ သိမ်းဆည်းပြီး။", reply_markup=InlineKeyboardMarkup(keyboard))
                context.user_data['waiting_for_link'] = False
        else:
            await update.message.reply_text("❌ Link ပုံစံ မှားယွင်းနေသည်။")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.job_queue.run_repeating(auto_sync_wrapper, interval=14400, first=10)
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 Bot v2.3 Stable Live...")
    app.run_polling()

