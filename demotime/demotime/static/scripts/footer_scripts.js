// Initialize lightboxes
$('.lightboxed').fancybox();

// Set focus on pageload
$('.content input[type="text"]').first().focus();

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

// Initialize tooltips
$('.tooltip').tooltipster();

// Initialized button clicks
$('button').click(function() {
    if ($(this).data('href')) {
        window.location.href = $(this).data('href');
    }
});

// Handle review form submits (some light validation on attachments)
$('.review form').submit(function(e) {
    var form = $(this),
        proceed = true;

    $('.attachment-container:visible').each(function() {
        var select = $(this).find('.attachment-type select'),
            file = $(this).find('.attachment-file input');

        if (!select.val() && file.val()) {
            proceed = false;
        }
    });

    if (proceed) {
        swal ({
            title: "Updating review",
            text: "Just a sec...",
            type: "success",
            showConfirmButton: false
        });
        setTimeout(function() {
            form.submit();
        }, 500);
    } else {
        e.preventDefault();
        sweetAlert("Sorry...", "Please select an attachment type.", "error");
    }
});

// Attach 'markdown supported' links after wysiwyg boxes
setTimeout(function() {
    $('.markItUpEditor').after('<div class="mdhelper"><a href="/markdown" target="_blank" class="mdhelper">Markdown supported</a></div>');
}, 1);
