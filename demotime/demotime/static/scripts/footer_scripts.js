$(document).ready(function() {
    $('.lightboxed').fancybox();
    $('.content input[type="text"]').first().focus();

    $('.summary a').click(function(event) {
        event.preventDefault();
        $(this).parents('.summary').next().slideToggle();
    });

    $('.attachment-add').click(function(event) {
        event.preventDefault();
        $(this).parents('section').next().slideDown();
    });

    $('.tooltip').tooltipster();
});
