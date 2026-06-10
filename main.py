import os
from telethon import TelegramClient
from telethon.sessions import StringSession

# قراءة البيانات من إعدادات السيرفر (وليس من الكود)
api_id = int(os.environ.get('API_ID'))
api_hash = os.environ.get('API_HASH')
session_string = os.environ.get('SESSION_STRING')

# تشغيل البوت باستخدام الجلسة المخزنة
client = TelegramClient(StringSession(session_string), api_id, api_hash)

async def main():
    await client.start()
    print("البوت يعمل الآن بنجاح!")
    await client.run_until_disconnected()

import asyncio
if __name__ == '__main__':
    asyncio.run(main())
