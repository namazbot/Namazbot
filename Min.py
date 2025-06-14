import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from datetime import datetime, timedelta
import requests
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def load_storage():
    if os.path.exists("storage.json"):
        with open("storage.json", "r") as f:
            return json.load(f)
    return {}

def save_storage(data):
    with open("storage.json", "w") as f:
        json.dump(data, f)

def get_prayer_times(city, country):
    url = f"http://api.aladhan.com/v1/timingsByCity?city={city}&country={country}&method=2"
    response = requests.get(url)
    data = response.json()
    if data["code"] == 200:
        return data["data"]["timings"]
    return None

def time_to_datetime(time_str):
    now = datetime.now()
    h, m = map(int, time_str.split(":"))
    return now.replace(hour=h, minute=m, second=0, microsecond=0)

async def prayer_reminder_loop():
    while True:
        storage = load_storage()
        for chat_id, user_data in storage.items():
            timings = user_data.get("timings", {})
            for name, t in timings.items():
                prayer_time = time_to_datetime(t) - timedelta(minutes=10)
                now = datetime.now()
                if now.strftime("%H:%M") == prayer_time.strftime("%H:%M") and not user_data["notified"].get(name):
                    await bot.send_message(chat_id, f"⏰ {name} এর সময় ১০ মিনিট পর!")
                    user_data["notified"][name] = True
        save_storage(storage)
        await asyncio.sleep(60)

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.reply("🌙 স্বাগতম! আপনার শহরের নাম লিখুন (যেমন: Dhaka,Bangladesh)")

@dp.message()
async def handle_city(message: types.Message):
    try:
        parts = message.text.split(",")
        if len(parts) != 2:
            await message.reply("❗ সঠিক ফরম্যাট: City,Country (যেমন: Dhaka,Bangladesh)")
            return
        city, country = parts[0].strip(), parts[1].strip()
        timings = get_prayer_times(city, country)
        if timings:
            storage = load_storage()
            storage[str(message.chat.id)] = {
                "timings": timings,
                "notified": {name: False for name in timings}
            }
            save_storage(storage)
            msg = "📿 আজকের নামাজের সময়সূচি:\n\n"
            for name, t in timings.items():
                msg += f"🕓 {name}: {t}\n"
            msg += "\n⏰ প্রতি নামাজের ১০ মিনিট আগে নোটিফিকেশন পাবেন!"
            await message.reply(msg)
        else:
            await message.reply("🙏 দুঃখিত, সময়সূচি পাওয়া যায়নি। শহরের নাম চেক করুন।")
    except Exception as e:
        await message.reply(f"⚠️ সমস্যা হয়েছে: {e}")

async def main():
    asyncio.create_task(prayer_reminder_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
