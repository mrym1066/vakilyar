// تابع باز کردن مودال با محتوای داینامیک
function openEditModal(url, title) {
    // تنظیم عنوان مودال
    $('#modalTitle').text(title);
    
    // نمایش پیام بارگذاری
    $('#modalBody').html(`
        <div class="text-center py-5">
            <i class="fa fa-spinner fa-spin fa-3x" style="font-size: 48px;"></i>
            <p class="mt-3">در حال بارگذاری فرم ویرایش...</p>
        </div>
    `);
    
    // نمایش مودال
    $('#universalEditModal').modal('show');
    
    // دریافت فرم از سرور با Ajax
    $.ajax({
        url: url,
        type: 'GET',
        success: function(response) {
            $('#modalBody').html(response);
            // اجرای اسکریپت‌های داخل فرم
            executeScriptsInContainer($('#modalBody')[0]);
        },
        error: function(xhr) {
            $('#modalBody').html(`
                <div class="alert alert-danger">
                    <strong>خطا!</strong> خطا در دریافت فرم ویرایش
                    <br>
                    <small>${xhr.status} - ${xhr.statusText}</small>
                </div>
            `);
        }
    });
}

// تابع کمکی برای اجرای اسکریپت‌های داخل HTML دریافتی
function executeScriptsInContainer(container) {
    const scripts = container.querySelectorAll('script');
    scripts.forEach(script => {
        const newScript = document.createElement('script');
        if (script.src) {
            newScript.src = script.src;
        } else {
            newScript.textContent = script.textContent;
        }
        document.body.appendChild(newScript);
    });
}