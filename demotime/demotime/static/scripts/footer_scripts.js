// Initialize lightboxes
$('.lightboxed').fancybox();

// Set focus on pageload
$('.content input[type="text"]:not(.find_person)').first().focus();

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
            reason = 'a file';
            proceed = false;
        }
    });

    if (!proceed) {
        e.preventDefault();
        sweetAlert('Sorry...', 'One of your attachments is missing ' + reason, 'error');
    } else {
        $('body').on('click', '#game', function(event) {
            event.preventDefault();
            $('#game_container').slideDown();
            $('.sweet-alert').css('margin-top', '-325px');
        });

        swal ({
            title: 'Updating review',
            text: 'Just a sec... <a href="javascript:void(0)" id="game">bored?</a><br><table id="game_container" style="display: none; margin: 20px 0 10px 0; width:460px; background:#fff; border:1px solid #F3F3F3;" cellspacing="0" cellpadding="0"><tr><td style="font-family:verdana; font-size:11px; color:#000; padding:5px 5px;"><object classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000" codebase="https://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=6,0,29,0" width="460" height="280"><param name="movie" value="https://www.games68.com/games/pacman.swf"><param name="quality" value="high"></param><param name="menu" value="false"></param><embed src="/static/games/pacman.swf" width="460" height="280" quality="high" pluginspage="https://www.macromedia.com/go/getflashplayer" type="application/x-shockwave-flash" menu="false" ></embed></object></td></tr>',
            type: 'success',
            html: true,
            showConfirmButton: false
        });
    }
});

$('.review input:not(.find_person)').keyup(function() {
    window.onbeforeunload = function(e) {
        return 'You have unsaved changes. Exit DemoTime?.';
    };
});
