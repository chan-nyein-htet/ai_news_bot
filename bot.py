import os, uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, PicklePersistence
from main import run

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 5768501788)) 
GUIDE_IMG = "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800"

def init_data(context):
    if 'channels' not in context.bot_data: context.bot_data['channels'] = {}
    if 'tokens' not in context.bot_data: context.bot_data['tokens'] = {}
    if 'subs' not in context.bot_data: context.bot_data['subs'] = {}

async def get_user_sub(user_id, context):
    init_data(context)
    uid = str(user_id)
    sub = context.bot_data['subs'].get(uid)
    if not sub:
        expiry = datetime.now() + timedelta(days=3)
        context.bot_data['subs'][uid] = {'expiry': expiry.isoformat(), 'limit': 1, 'status': 'FREE'}
        sub = context.bot_data['subs'][uid]
    expiry_date = datetime.fromisoformat(sub['expiry'])
    status = "EXPIRED" if datetime.now() > expiry_date else sub.get('status', 'PAID')
    return {"status": status, "limit": sub['limit'], "expiry": expiry_date.strftime("%Y-%m-%d %H:%M")}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_data(context)
    user_id = update.effective_user.id
    sub = await get_user_sub(user_id, context)
    
    welcome_msg = (
        "<b>🤖 AI Content Automation System (v1.1)</b>\n\n"
        f"👤 <b>Plan:</b> {sub['status']} | 📊 <b>Limit:</b> {sub['limit']} Ch\n"
        f"📅 <b>Expiry:</b> {sub['expiry']}\n\n"
        "<b>💡 Gemini Prompt အသုံးပြုနည်း:</b>\n"
        "အောက်ပါ Prompt ကို Copy ကူးပြီး Gemini (AI) တွင် မေးမြန်းခြင်းဖြင့် မိမိလိုချင်သော သတင်းများ၏ RSS Feed Link များကို ရှာဖွေနိုင်ပါသည်။\n\n"
        "<code>Please provide a list of valid RSS feed URLs for [Topic]. Ensure the links end in /feed/ or .xml.</code>\n\n"
        "<b>📖 အသုံးပြုပုံ:</b>\n"
        "၁။ Channel တွင် Bot ကို Admin ခန့်ပါ။\n"
        "၂။ Channel သတ်မှတ်ပြီး Link များထည့်ပါ။\n"
        "၃။ Bot မှ ၄ နာရီတစ်ခါ အလိုအလျောက် သတင်းတင်ပေးပါမည်။"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 Sync News Now", callback_data='start_sync')],
        [InlineKeyboardButton("➕ Add New Channel", callback_data='add_new')],
        [InlineKeyboardButton("⚙️ Manage Links", callback_data='view_details')],
        [InlineKeyboardButton("🔑 Redeem Token", callback_data='redeem_btn')]
    ]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🎫 [Admin] Token Manager", callback_data='admin_token_mgr')])

    markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.message.delete()
        await update.callback_query.message.reply_photo(photo=GUIDE_IMG, caption=welcome_msg, reply_markup=markup, parse_mode='HTML')
    else:
        await update.message.reply_photo(photo=GUIDE_IMG, caption=welcome_msg, reply_markup=markup, parse_mode='HTML')

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_data(context)
    query = update.callback_query
    user_id = query.from_user.id
    uid = str(user_id)
    await query.answer()

    if query.data == 'start_sync':
        kb = [[InlineKeyboardButton("⚡ Fast Mode", callback_data='sync_mode_1')],
              [InlineKeyboardButton("📖 Detailed Mode", callback_data='sync_mode_2')],
              [InlineKeyboardButton("🔙 Back", callback_data='main_menu')]]
        await query.message.reply_text("🎯 <b>တင်ဆက်မည့် ပုံစံရွေးချယ်ပါ:</b>", reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')

    elif query.data.startswith('sync_mode_'):
        mode = query.data.split('_')[-1]
        user_channels = context.bot_data['channels'].get(uid, {})
        if not user_channels:
            await query.message.reply_text("❌ Channel မရှိသေးပါ။")
            return
        await query.message.reply_text("🔄 <b>သတင်းများ စစ်ဆေးနေပါသည်...</b>", parse_mode='HTML')
        for ch, links in user_channels.items():
            if links: run(rss_links=links, mode=mode, chat_id=ch)
        await query.message.reply_text("✅ Sync ပြီးဆုံးပါပြီ။")

    elif query.data == 'add_new':
        sub = await get_user_sub(user_id, context)
        if len(context.bot_data['channels'].get(uid, {})) >= sub['limit']:
            await query.message.reply_text("❌ <b>Limit ပြည့်နေပြီ!</b>")
            return
        await query.message.reply_text("📝 <b>Step 1:</b> Channel @username ကို ပေးပို့ပါ:", parse_mode='HTML')
        context.user_data['waiting_for_channel'] = True

    elif query.data == 'view_details':
        user_channels = context.bot_data['channels'].get(uid, {})
        if not user_channels:
            await query.message.reply_text("❌ ဘာမှ မရှိသေးပါ။")
            return
        kb = [[InlineKeyboardButton(f"🛠 Manage {ch}", callback_data=f"manage_{ch}")] for ch in user_channels.keys()]
        kb.append([InlineKeyboardButton("🔙 Back", callback_data='main_menu')])
        await query.message.reply_text("📋 <b>သင်၏ Channel များ:</b>", reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')

    elif query.data.startswith('manage_'):
        ch_id = query.data.replace('manage_', '')
        links = context.bot_data['channels'].get(uid, {}).get(ch_id, [])
        text = f"🎯 <b>Channel: {ch_id}</b>\n\n" + ("\n".join([f"{i+1}. {l}" for i, l in enumerate(links)]) if links else "Links မရှိသေးပါ။")
        kb = [[InlineKeyboardButton("➕ Add Link", callback_data=f"addlink_{ch_id}")],
              [InlineKeyboardButton("🗑 Clear All", callback_data=f"clear_{ch_id}")],
              [InlineKeyboardButton("🔙 Back", callback_data='view_details')]]
        await query.message.reply_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb), disable_web_page_preview=True)

    elif query.data.startswith('addlink_'):
        context.user_data['current_ch'] = query.data.replace('addlink_', '')
        context.user_data['waiting_for_link'] = True
        await query.message.reply_text(f"🌐 <b>{context.user_data['current_ch']}</b> အတွက် RSS Link ပေးပို့ပါ:", parse_mode='HTML')

    elif query.data.startswith('clear_'):
        ch_id = query.data.replace('clear_', '')
        if uid in context.bot_data['channels'] and ch_id in context.bot_data['channels'][uid]:
            context.bot_data['channels'][uid][ch_id] = []
            await query.message.reply_text(f"✅ {ch_id} မှ Link အားလုံးကို ဖျက်လိုက်ပါပြီ။")
        await start(update, context)

    elif query.data == 'admin_token_mgr' and user_id == ADMIN_ID:
        tokens = context.bot_data.get('tokens', {})
        kb = []
        text = "<b>🎫 Active Tokens:</b>\n\n" if tokens else "🎫 <b>No Active Tokens.</b>"
        for tk, val in tokens.items():
            text += f"• <code>{tk}</code> ({val['days']}d/{val['limit']}ch)\n"
            kb.append([InlineKeyboardButton(f"🗑 Del {tk}", callback_data=f"deltk_{tk}")])
        kb.append([InlineKeyboardButton("➕ Gen New Token", callback_data='admin_gen')])
        kb.append([InlineKeyboardButton("🔙 Back", callback_data='main_menu')])
        await query.message.reply_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))

    elif query.data.startswith('deltk_'):
        tk_id = query.data.replace('deltk_', '')
        if tk_id in context.bot_data.get('tokens', {}): del context.bot_data['tokens'][tk_id]
        await query.message.reply_text(f"✅ Token {tk_id} Deleted.")
        await start(update, context)

    elif query.data == 'redeem_btn':
        await query.message.reply_text("Token ကုဒ်ကို ရိုက်ထည့်ပါ:")
        context.user_data['waiting_for_token'] = True

    elif query.data == 'admin_gen' and user_id == ADMIN_ID:
        await query.message.reply_text("🎫 ရက်နှင့် ချန်နယ်ကို ပေးပို့ပါ (ဥပမာ- 30_5):")
        context.user_data['waiting_for_gen'] = True

    elif query.data == 'main_menu':
        await start(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    uid = str(user_id)
    text = update.message.text.strip()
    init_data(context)

    if context.user_data.get('waiting_for_gen') and user_id == ADMIN_ID:
        try:
            d, l = map(int, text.split('_'))
            token = f"CHAN-{uuid.uuid4().hex[:6].upper()}"
            context.bot_data['tokens'][token] = {'days': d, 'limit': l}
            kb = [[InlineKeyboardButton("🔙 Back", callback_data='admin_token_mgr')]]
            await update.message.reply_text(f"<code>{token}</code>", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))
        except: await update.message.reply_text("❌ 30_5 ပုံစံပို့ပါ။")
        context.user_data['waiting_for_gen'] = False

    elif context.user_data.get('waiting_for_token'):
        token_in = text.upper()
        if token_in in context.bot_data.get('tokens', {}):
            t_data = context.bot_data['tokens'].pop(token_in)
            expiry = datetime.now() + timedelta(days=t_data['days'])
            context.bot_data['subs'][uid].update({'expiry': expiry.isoformat(), 'limit': t_data['limit'], 'status': 'PAID'})
            kb = [[InlineKeyboardButton("🏠 ပင်မစာမျက်နှာသို့", callback_data='main_menu')]]
            await update.message.reply_text(f"✅ Success!\nသက်တမ်း: {expiry.date()}\nLimit: {t_data['limit']} Ch", reply_markup=InlineKeyboardMarkup(kb))
        else: await update.message.reply_text("❌ Token မှားယွင်းနေသည်။")
        context.user_data['waiting_for_token'] = False

    elif context.user_data.get('waiting_for_channel'):
        if text.startswith('@'):
            context.user_data['current_ch'], context.user_data['waiting_for_channel'], context.user_data['waiting_for_link'] = text, False, True
            # Parse Mode ထည့်သွင်းပေးလိုက်သည်
            await update.message.reply_text(f"✅ Target: {text}\n🌐 RSS Link ပေးပို့ပါ:", parse_mode='HTML')
        else: await update.message.reply_text("❌ @username ပုံစံဖြင့်ပို့ပါ။")

    elif context.user_data.get('waiting_for_link'):
        ch_id = context.user_data.get('current_ch')
        if text.startswith('http'):
            context.bot_data['channels'].setdefault(uid, {}).setdefault(ch_id, []).append(text)
            kb = [[InlineKeyboardButton("➕ ထပ်ထည့်မည်", callback_data=f"addlink_{ch_id}")], [InlineKeyboardButton("✅ ပြီးပြီ", callback_data='main_menu')]]
            await update.message.reply_text("✅ သိမ်းဆည်းပြီး။", reply_markup=InlineKeyboardMarkup(kb))
            context.user_data['waiting_for_link'] = False

if __name__ == '__main__':
    persistence = PicklePersistence(filepath='bot_data.pickle')

    app = ApplicationBuilder().token(TOKEN).persistence(persistence).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 Bot v1.1 Live (Persistent Mode Enabled)...")
    app.run_polling()

