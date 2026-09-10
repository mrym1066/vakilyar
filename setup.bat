@echo off
chcp 65001 > nul
echo.
echo ========================================
echo    وکیل‌یار — راه‌اندازی خودکار
echo ========================================
echo.

REM بررسی Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [خطا] Python نصب نیست. لطفاً از python.org نصب کنید.
    pause
    exit /b 1
)

echo [1/5] ساخت محیط مجازی...
python -m venv venv
call venv\Scripts\activate.bat

echo [2/5] نصب پکیج‌ها...
pip install -r requirements.txt --quiet

echo [3/5] تنظیم فایل .env ...
if not exist .env (
    copy .env.example .env
    echo فایل .env ساخته شد. در صورت نیاز آن را ویرایش کنید.
)

echo [4/5] اجرای migration...
python manage.py migrate --run-syncdb

echo [5/5] جمع‌آوری فایل‌های استاتیک...
python manage.py collectstatic --noinput --clear

echo.
echo ========================================
echo    راه‌اندازی کامل شد!
echo ========================================
echo.
echo برای ساخت کاربر ادمین:
echo    python manage.py createsuperuser
echo.
echo برای اجرای سرور:
echo    python manage.py runserver
echo.
echo سپس مرورگر را باز کنید:
echo    http://127.0.0.1:8000
echo.
pause
