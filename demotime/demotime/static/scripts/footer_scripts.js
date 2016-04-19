// Initialize lightboxes
$('.lightboxed').fancybox();

// Set focus on pageload
$('.content input[type="text"]:not(#find_reviewer)').first().focus();

// Animate buttons
$('button, .button-link, input[type="submit"]').click(function() {
    $(this).addClass('animated pulse');
});

// Slide toggle summary boxes
$('.summary a').click(function(event) {
    event.preventDefault();
    $(this).parents('.summary').next().slideToggle();
});

// Dynamically add additional attachments
$('.attachment-add').click(function(event) {
    event.preventDefault();
    $(this).parents('section').next().slideDown();
    $(this).remove();
});

// Linkify URLs
$('blockquote p, .review-overview li, .review-overview p').linkify({
    target: "_blank"
});

// Initialize tooltips
$('.help').tooltipster();

// Initialized button clicks
$('button').click(function() {
    if ($(this).data('href')) {
        window.location.href = $(this).data('href');
    }
});

// Smooth scroll to links
var ScrollToLink = new DemoTime.ScrollToLink();

// Handle review form submits (some light validation on attachments)
$('.review form').submit(function(e) {
    var form = $(this),
        proceed = true,
        reason = '';

    // Remove dialog warning
    $(window).unbind('beforeunload');
    window.onbeforeunload = null;

    $('.attachment-container:visible').each(function() {
        var select = $(this).find('.attachment-type select'),
            file = $(this).find('.attachment-file input'),
            desc = $(this).find('.attachment-desc input');

        if (!select.val() && file.val()) {
            reason = 'an attachment type';
            proceed = false;
        }
        if (!file.val() && desc.val()) {
            reason = 'an attachment';
            proceed = false;
        }
    });

    if (!proceed) {
        e.preventDefault();
        sweetAlert('Sorry...', 'One of your attachments is missing ' + reason, 'error');
    } else {
        swal ({
            title: 'Updating review',
            text: 'Just a sec...',
            type: 'success',
            showConfirmButton: false
        });
    }
});

$('.review input:not(.find_person)').keyup(function() {
    window.onbeforeunload = function(e) {
        return 'You have unsaved changes. Exit DemoTime?.';
    };
});
