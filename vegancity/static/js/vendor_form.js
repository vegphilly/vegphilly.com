/*global $ */
$(document).ready(function() {

    function sanitizePhoneNumber(number) {
        var pattern = /[0-9]{10}/;
        if (pattern.test(number)) {
            var area_code = number.slice(0, 3);
            var prefix = number.slice(3, 6);
            var suffix = number.slice(6, 10);
            return "(" + area_code + ") " + prefix + "-" + suffix;
        } else {
            return number;
        }
    }
    $('#id_phone').blur(function (event) {
        var $el = $(event.target),
            number = $el.val();
        $el.val(sanitizePhoneNumber(number));
    });
});
