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
});

// Linkify URLs
$('blockquote p, .review-overview li, .review-overview p').linkify({
    target: "_blank"
});

// Initialize tooltips
$('.tooltip').tooltipster();

// Initialized button clicks
$('button').click(function() {
    if ($(this).data('href')) {
        window.location.href = $(this).data('href');
    }
});

// Smooth scroll to links
var ScrollToLink = new DemoTime.ScrollToLink();

// Emoji!
var Emoji = new DemoTime.Emoji();

// Handle review form submits (some light validation on attachments)
$('.review form').submit(function(e) {
    var form = $(this),
        proceed = true;

    // Remove dialog warning
    $(window).unbind('beforeunload');
    window.onbeforeunload = null;

    $('.attachment-container:visible').each(function() {
        var select = $(this).find('.attachment-type select'),
            file = $(this).find('.attachment-file input');

        if (!select.val() && file.val()) {
            proceed = false;
        }
    });

    if (!proceed) {
        e.preventDefault();
        sweetAlert("Sorry...", "Please select an attachment type.", "error");
    } else {
        swal ({
            title: "Updating review",
            text: "Just a sec...",
            type: "success",
            showConfirmButton: false
        });
    }
});

$('.review input:not(#find_reviewer)').keyup(function() {
    window.onbeforeunload = function(e) {
        return 'You have unsaved changes. Exit DemoTime?.';
    };
});
