document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    document.querySelectorAll('form.filter-form').forEach(form => {
        const checkboxes = form.querySelectorAll('input[type="checkbox"]');
        const selects = form.querySelectorAll('select');

        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => form.submit());
        });

        selects.forEach(select => {
            select.addEventListener('change', () => form.submit());
        });
    });
});