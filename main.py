# -*- coding: utf-8 -*-
import asyncio
import sqlite3
import os
import glob
from telethon import TelegramClient, events
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, GetUserPhotosRequest, DeletePhotosRequest
from telethon.tl.types import InputPhoto
from telethon.errors import FloodWaitError

# --- إعدادات الحساب (تُجلب من إعدادات السيرفر) ---
# تأكد من إضافة API_ID و API_HASH في إعدادات (Variables) الخاصة بمنصة الاستضافة
API_ID = int(os.environ.get("API_ID"))          
API_HASH = os.environ.get("API_HASH")    
client = TelegramClient('session_mousawi', API_ID, API_HASH)

# --- إعداد المجلدات ---
if not os.path.exists('backup_photos'):
    os.makedirs('backup_photos')

def init_db():
    conn = sqlite3.connect('final_master.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS profile_backup (id INTEGER PRIMARY KEY, first_name TEXT, last_name TEXT, bio TEXT)')
    conn.commit()
    conn.close()

# --- بقية الكود الخاص بك ---
@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^\.انتحال(?:\s+@?([\w_]+))?'))
async def clone_profile_cmd(event):
    # ... (باقي كود أمر الانتحال كما هو دون تغيير)
    target = None
    if event.is_reply:
        reply = await event.get_reply_message()
        target = await client.get_entity(reply.sender_id)
    elif event.pattern_match.group(1):
        try: target = await client.get_entity(event.pattern_match.group(1))
        except: return await event.edit("⚠️ يوزر غير صحيح.")
    else: return await event.edit("⚠️ يرجى الرد على الشخص أو كتابة اليوزر.")

    await event.edit("🚀 `بدء عملية الانتحال (النسخة الآمنة)...`")

    try:
        full_target = await client(GetFullUserRequest(target))
        target_bio = full_target.full_user.about or ""
        
        me = await client.get_me()
        full_me = await client(GetFullUserRequest('me'))
        my_bio = full_me.full_user.about or ""
        
        conn = sqlite3.connect('final_master.db')
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO profile_backup (id, first_name, last_name, bio) VALUES (1, ?, ?, ?)', 
                       (me.first_name, me.last_name or "", my_bio))
        conn.commit()
        conn.close()

        for f in glob.glob('backup_photos/*'): os.remove(f)
        photos = await client.get_profile_photos('me')
        for i, photo in enumerate(photos):
            await client.download_media(photo, f'backup_photos/orig_{i}.jpg')

        await client(UpdateProfileRequest(first_name=target.first_name, last_name=target.last_name or "", about=target_bio))
        
        if photos:
            await client(DeletePhotosRequest(id=[InputPhoto(id=p.id, access_hash=p.access_hash, file_reference=p.file_reference) for p in photos]))
            
        target_photos = await client(GetUserPhotosRequest(user_id=target.id, offset=0, max_id=0, limit=5))
        for photo in reversed(target_photos.photos):
            file = await client.download_media(photo)
            await asyncio.sleep(2) 
            try:
                if file.endswith(('.mp4', '.mov')):
                    await client(UploadProfilePhotoRequest(video=await client.upload_file(file), video_start_ts=0.0))
                else:
                    await client(UploadProfilePhotoRequest(file=await client.upload_file(file)))
            finally:
                if os.path.exists(file): os.remove(file)
        
        await event.edit(f"✅ **تم انتحال {target.first_name} بنجاح.**")
        
    except Exception as e:
        await event.edit(f"❌ خطأ: {str(e)}")

# --- أمر الرجوع ---
@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^\.رجوع'))
async def restore_profile_cmd(event):
    await event.edit("♻️ `جاري استعادة هويتك الأصلية...`")
    conn = sqlite3.connect('final_master.db')
    cursor = conn.cursor()
    cursor.execute('SELECT first_name, last_name, bio FROM profile_backup WHERE id = 1')
    row = cursor.fetchone()
    conn.close()
    
    if not row: return await event.edit("⚠️ لا توجد نسخة احتياطية.")
    
    try:
        await client(UpdateProfileRequest(first_name=row[0], last_name=row[1], about=row[2]))
        photos = await client.get_profile_photos('me')
        if photos:
            await client(DeletePhotosRequest(id=[InputPhoto(id=p.id, access_hash=p.access_hash, file_reference=p.file_reference) for p in photos]))
        
        for f in sorted(glob.glob('backup_photos/orig_*.jpg')):
            await client(UploadProfilePhotoRequest(file=await client.upload_file(f)))
            await asyncio.sleep(2) 
            
        await event.edit("✅ **تمت استعادة هويتك بالكامل.**")
    except Exception as e:
        await event.edit(f"❌ خطأ أثناء الاستعادة: {str(e)}")

async def main():
    init_db()
    await client.start()
    print("السورس يعمل (Final Stable Edition).")
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
    
