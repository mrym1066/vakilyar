document.addEventListener('DOMContentLoaded', function () {
    const serviceTypeField = document.querySelector('#id_service_type');
    const priceField = document.querySelector('#id_service_price');

    if (serviceTypeField) {
        serviceTypeField.addEventListener('change', function () {
            const serviceTypeId = this.value;

            if (serviceTypeId) {
                // ارسال درخواست AJAX به سرور برای دریافت قیمت
                fetch(`/admin/get_service_price/${serviceTypeId}/`)
                    .then(response => response.json())
                    .then(data => {
                        priceField.value = data.price || 'N/A';
                    })
                    .catch(error => {
                        console.error('Error fetching service price:', error);
                    });
            } else {
                priceField.value = '';
            }
        });
    }
});
