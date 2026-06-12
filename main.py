import asyncio
import sqlite3
import docker
import random
import string
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# --- إعدادات ---
TOKEN = "8881752903:AAEHkVk3oRfsgm71f0fRpYIAbi55iXzZUG4"
docker_client = docker.from_env()
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- إدارة قاعدة البيانات (بأسلوب آمن) ---
def get_db_connection():
    conn = sqlite3.connect('hosting.db')
    conn.row_factory = sqlite3.Row  # لتسهيل الوصول للبيانات
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS projects 
                      (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT UNIQUE, 
                       type TEXT, container_id TEXT, status TEXT)''')

# --- التوليد التلقائي للأسماء ---
def generate_name():
    return "proj-" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

# --- حالات البوت ---
class ProjectStates(StatesGroup):
    waiting_for_name = State()

# --- أوامر البوت ---
@dp.message(Command("start"))
async def start(message: types.Message):
    # استخدام ReplyKeyboardMarkup مع طلب حذفها بعد الاختيار (اختياري)
    markup = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🚀 استضافة بكود"), types.KeyboardButton(text="📁 استضافة موقع")],
            [types.KeyboardButton(text="📂 مشاريعي")]
        ], 
        resize_keyboard=True
    )
    await message.answer("أهلاً بك في نظام الاستضافة السحابي! ☁️", reply_markup=markup)

@dp.message(F.text == "📁 استضافة موقع")
async def host_web(message: types.Message, state: FSMContext):
    await state.set_state(ProjectStates.waiting_for_name)
    await message.answer("اختر اسماً لموقعك (أو اكتب 'تلقائي' للاسم العشوائي):")

@dp.message(ProjectStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text if message.text.lower() != 'تلقائي' else generate_name()
    
    # 1. تحقق أمني بسيط: منع تكرار الأسماء في دوكر
    try:
        # 2. تشغيل الحاوية مع تحديد موارد (مهم جداً للحفاظ على السيرفر)
        container = docker_client.containers.run(
            "nginx:alpine", 
            detach=True, 
            name=name,
            mem_limit="128m", # تحديد الذاكرة لـ 128 ميجا
            restart_policy={"Name": "always"} # التشغيل التلقائي عند ريستارت السيرفر
        )
        
        # 3. حفظ آمن في قاعدة البيانات
        with get_db_connection() as conn:
            conn.execute("INSERT INTO projects (user_id, name, type, container_id, status) VALUES (?, ?, ?, ?, ?)",
                         (message.from_user.id, name, 'web', container.id, 'running'))
            
        await message.answer(f"✅ تم إنشاء مشروعك بنجاح!\n🔗 الرابط: http://{name}.yourdomain.com")
        
    except docker.errors.APIError as e:
        await message.answer(f"❌ خطأ في النظام: قد يكون الاسم مستخدماً بالفعل. حاول مجدداً.")
    except Exception as e:
        await message.answer(f"⚠️ حدث خطأ غير متوقع: {str(e)}")
    
    await state.clear()

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
