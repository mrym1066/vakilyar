/* ===========================================================
   Vakilyar — main.js
   اسکریپت‌های اصلی سایت
   =========================================================== */

/* ═══════════════════════════════════════════════════════════
   بخش ۱: اسکریپت‌های عمومی سایت (jQuery)
   ═══════════════════════════════════════════════════════════ */
(function ($) {
    'use strict';

    $(document).ready(function () {

        // ─── Scroll to top
        if ($.fn.scrollUp) {
            $.scrollUp({
                scrollName: 'scrollUp',
                topDistance: '300',
                topSpeed: 300,
                animation: 'fade',
                animationInSpeed: 200,
                animationOutSpeed: 200,
                scrollText: '<i class="fa fa-angle-up"></i>',
                activeOverlay: false
            });
        }

        // ─── Smooth scroll برای لینک‌های داخلی
        $('a[href^="#"]').on('click', function (e) {
            const hash = this.hash;
            if (hash && hash !== '#') {
                const target = $(hash);
                if (target.length) {
                    e.preventDefault();
                    $('html, body').animate({
                        scrollTop: target.offset().top - 80
                    }, 400);
                }
            }
        });

        // ─── Tooltip
        if ($.fn.tooltip) {
            $('[data-toggle="tooltip"]').tooltip();
        }

        // ─── Popover
        if ($.fn.popover) {
            $('[data-toggle="popover"]').popover();
        }

        // ─── Active state توی منو
        const currentPath = window.location.pathname;
        $('.mainmenu .nav li a').each(function () {
            const href = $(this).attr('href');
            if (href && href !== '/' && currentPath.startsWith(href)) {
                $(this).addClass('active');
            }
        });

        // ─── Scroll to top button (fallback)
        const $scrollUp = $('#scrollUp');
        if ($scrollUp.length && !$.fn.scrollUp) {
            $(window).on('scroll', function () {
                if ($(this).scrollTop() > 300) {
                    $scrollUp.fadeIn(200);
                } else {
                    $scrollUp.fadeOut(200);
                }
            });

            $scrollUp.on('click', function (e) {
                e.preventDefault();
                $('html, body').animate({ scrollTop: 0 }, 400);
            });
        }

    });

})(jQuery);

/* ═══════════════════════════════════════════════════════════
   بخش ۲: چاپ متن لایحه دفاعیه (Vanilla JS)
   ═══════════════════════════════════════════════════════════ */
(function () {
    'use strict';

    function printDefenseDocument() {
        var content = document.getElementById('printable-content');
        if (!content) {
            alert('محتوایی برای چاپ یافت نشد.');
            return;
        }

        var subject = content.dataset.subject || 'لایحه دفاعیه';
        var movakel = content.dataset.movakel || '';
        var stage   = content.dataset.stage   || '';
        var date    = content.dataset.date    || '';

        var iframe = document.createElement('iframe');
        iframe.style.position = 'fixed';
        iframe.style.right = '0';
        iframe.style.bottom = '0';
        iframe.style.width = '0';
        iframe.style.height = '0';
        iframe.style.border = '0';
        iframe.style.visibility = 'hidden';
        document.body.appendChild(iframe);

        var doc = iframe.contentWindow.document;

        doc.open();
        doc.write('<!DOCTYPE html>');
        doc.write('<html dir="rtl" lang="fa">');
        doc.write('<head>');
        doc.write('<meta charset="UTF-8">');
        doc.write('<title>' + subject + '</title>');
        doc.write('<style>');
        doc.write('@page { size: A4; margin: 15mm 12mm; }');
        doc.write('* { box-sizing: border-box; }');
        doc.write('body { font-family: Vazirmatn, Tahoma, sans-serif; direction: rtl; text-align: right; color: #000; font-size: 11.5pt; line-height: 2; margin: 0; padding: 0; }');
        doc.write('.print-header { border-bottom: 2px solid #333; padding-bottom: 12px; margin-bottom: 16px; }');
        doc.write('.print-header h1 { font-size: 14pt; margin: 0 0 8px; font-weight: 700; }');
        doc.write('.print-header .meta { font-size: 10.5pt; color: #333; display: flex; gap: 20px; flex-wrap: wrap; }');
        doc.write('.print-content { white-space: pre-wrap; word-wrap: break-word; text-align: justify; }');
        doc.write('.print-content img { max-width: 100%; height: auto; }');
        doc.write('.print-footer { margin-top: 30px; padding-top: 12px; border-top: 1px dashed #666; font-size: 10pt; text-align: center; color: #555; }');
        doc.write('</style>');
        doc.write('</head>');
        doc.write('<body>');

        doc.write('<div class="print-header">');
        doc.write('<h1>' + subject + '</h1>');
        doc.write('<div class="meta">');
        if (movakel) doc.write('<span><strong>موکل:</strong> ' + movakel + '</span>');
        if (stage)   doc.write('<span><strong>مرحله:</strong> ' + stage + '</span>');
        if (date)    doc.write('<span><strong>تاریخ:</strong> ' + date + '</span>');
        doc.write('</div>');
        doc.write('</div>');

        doc.write('<div class="print-content">');
        doc.write(content.innerHTML);
        doc.write('</div>');

        doc.write('<div class="print-footer">');
        doc.write('این سند از سامانه وکیل‌یار چاپ شده است.');
        doc.write('</div>');

        doc.write('</body></html>');
        doc.close();

        var doPrint = function () {
            try {
                iframe.contentWindow.focus();
                iframe.contentWindow.print();
            } catch (e) {
                console.error('Print error:', e);
            }
            setTimeout(function () {
                if (iframe && iframe.parentNode) {
                    iframe.parentNode.removeChild(iframe);
                }
            }, 1000);
        };

        if (iframe.contentWindow.document.readyState === 'complete') {
            setTimeout(doPrint, 300);
        } else {
            iframe.onload = function () { setTimeout(doPrint, 300); };
        }
    }

    // اتصال به دکمه چاپ
    document.addEventListener('DOMContentLoaded', function () {
        var printBtn = document.getElementById('btn-print-document');
        if (printBtn) {
            printBtn.addEventListener('click', printDefenseDocument);
        }
    });

})();