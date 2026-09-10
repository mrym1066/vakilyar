document.addEventListener('DOMContentLoaded', function() {

    // کلیک همبرگر — باز/بسته کردن
    document.querySelector('[data-lte-toggle="sidebar"]')?.addEventListener('click', function(e) {
        e.preventDefault();
        document.body.classList.toggle('sidebar-open');
    });

    // کلیک overlay — بستن
    document.querySelector('.sidebar-overlay')?.addEventListener('click', function() {
        document.body.classList.remove('sidebar-open');
    });
});