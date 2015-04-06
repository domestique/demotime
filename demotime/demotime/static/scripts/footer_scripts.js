$(document).ready(function() {
    $('.lightboxed').fancybox();
    $('.content input[type="text"]').first().focus();

    $('.summary a').click(function(event) {
        event.preventDefault();
        $(this).parents('.summary').next().slideToggle();
    });
});
