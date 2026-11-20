import json
import requests
from datetime import datetime, timezone, timedelta

# --- تنظیمات ---
TELEGRAM_BOT_TOKEN = "9140051518:AAHh16276FCkEIzzSmtaunrNcAff70Gczcc"  # توکن دریافتی از BotFather
TELEGRAM_CHAT_ID = "1864304786"              # چت‌آیدی عددی شما یا آیدی کانال (مثلاً @mychannel)
MCP_URL = "https://mcp.producthunt.com/mcp"

def get_producthunt_leaderboard():
    session = requests.Session()
    
    # ۱. برقراری اتصال اولیه پروتکل MCP
    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "telegram-sync", "version": "1.0"}
        }
    }
    session.post(MCP_URL, json=init_payload)
    session.post(MCP_URL, json={"jsonrpc": "2.0", "method": "notifications/initialized"})
    
    # ۲. تعیین تاریخ ۲۴ ساعت گذشته به وقت پاسیفیک (Product Hunt بر اساس منطقه زمانی Pacific روز را می‌بندد)
    # ساعت ۱۲ شب به وقت پاسیفیک معادل ساعت ۱۱:۳۰ صبح ایران است
    yesterday_pt = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    # ۳. فراخوانی ابزار دریافت لیدربورد
    call_payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "get_product_leaderboard",
            "arguments": {
                "date": yesterday_pt,
                "limit": 3
            }
        }
    }
    
    response = session.post(MCP_URL, json=call_payload)
    result = response.json()
    
    # استخراج داده‌های جیسون از خروجی MCP
    data_text = result["result"]["content"][1]["text"]
    data = json.loads(data_text)
    return yesterday_pt, data["data"]["results"]

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    requests.post(url, json=payload)

def main():
    date_str, products = get_producthunt_leaderboard()
    
    msg = f"🏆 <b>برترین محصولات روز Product Hunt</b>\n"
    msg += f"📅 تاریخ: <code>{date_str}</code>\n"
    msg += "───────────────────\n\n"
    
    medals = ["🥇", "🥈", "🥉"]
    for i, product in enumerate(products):
        launch = product["launches"][0]
        name = launch["name"]
        tagline = launch["tagline"]
        points = launch["points"]
        url = launch["url"].split("?")[0]  # لینک تمیز صفحه محصول
        
        msg += f"{medals[i]} <b>رتبه #{i+1}: <a href='{url}'>{name}</a></b>\n"
        msg += f"💬 <i>{tagline}</i>\n"
        msg += f"🔺 آپووت‌ها: <b>{points:,}</b>\n\n"
        
    msg += "───────────────────\n"
    msg += "🔗 <a href='https://www.producthunt.com/leaderboard/daily'>مشاهده کل لیدربورد</a>"
    
    send_to_telegram(msg)
    print("پیام با موفقیت ارسال شد.")

if __name__ == "__main__":
    main()
