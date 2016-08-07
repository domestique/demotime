// Slide toggle summary boxes
$('body').on('click', '.summary a', function(event) {
    event.preventDefault();
    $(this).parents('.summary').next().slideToggle();
});

$(document).ready(function() {
    $('.subnav').stick_in_parent({
        'parent': 'body',
        'recalc_every': 100,
    });
});

// Dynamically add attachment type
$('body').on('click', '.attachment-file', function() {
    var file = $(this).find('input');

    file.change(function() {
        var filename = $(this).val(),
            attachment_type = $(this).parents('.attachment-container').find('.attachment-type select');

        if (filename) {
            filename = filename.split('.');
            ext = filename.slice(-1)[0].toLowerCase();

            if (ext.match(/png|gif|bmp|jpg|jpeg|tiff|svg/g)) {
                attachment_type.val('image');
            } else if (ext.match(/doc|pdf|docx|txt/g)) {
                attachment_type.val('document');
            } else if (ext.match(/mkv|mov|avi|divx|mpeg|webm|mp4|mpeg4/g)) {
                attachment_type.val('movie');
            } else if (ext.match(/mp3|wav|aiff|ogg|mpeg3/g)) {
                attachment_type.val('audio');
            } else {
                attachment_type.val('other');
            }
        }
    });
});
// Dynamically add additional attachments
$('.attachment-add').click(function(event) {
    event.preventDefault();
    $(this).parents('section').nextAll('section').not(':visible').first().slideDown();
    //$(this).css('visibility', 'hidden');
});
$('.attachment-remove').click(function(event) {
    event.preventDefault();
    $(this).parents('.attachment-container').parent().slideUp(function() {
        $(this).remove();
    });
});

// Linkify URLs
if ($('blockquote p, .review-overview li, .review-overview p').length) {
    $('blockquote p, .review-overview li, .review-overview p').linkify({
        target: "_blank"
    });
}

// Handle review form submits (some light validation on attachments)
$('.review form, .new_comment form').submit(function(e) {
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
        $('body').on('click', '.game', function(event) {
            event.preventDefault();
            var game = $('#game_container'),
                link = $(this);
            game.find('param').val('/static/games/' + link.data('game') + '.swf');
            game.find('embed').attr('src', '/static/games/' + link.data('game') + '.swf');
            $('#game_container').slideDown();
            $('.game').remove();
            $('.sweet-alert').css('margin-top', '-325px');
        });

        var text = 'Just a sec...';
        text += '<a href="javascript:void(0)" class="game" data-game="pacman">pacman</a>'
        text += '<a href="javascript:void(0)" class="game" data-game="galaga">galaga</a>'
        text += '<a href="javascript:void(0)" class="game" data-game="asteroids">asteroids</a>'
        text += '<a href="javascript:void(0)" class="game" data-game="pong">pong</a>'
        text += '<a href="javascript:void(0)" class="game" data-game="tetris">tetris</a>'
        text += '<a href="javascript:void(0)" class="game" data-game="doom">doom</a>'

        swal ({
            title: 'Updating review',
            text: text + '<br><table id="game_container" style="display: none; margin: 20px 0 10px 0; width:460px; background:#fff; border:1px solid #F3F3F3;" cellspacing="0" cellpadding="0"><tr><td style="font-family:verdana; font-size:11px; color:#000; padding:5px 5px;"><object classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000" codebase="https://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=6,0,29,0" width="460" height="280"><param name="movie" value="/static/games/pacman.swf"><param name="quality" value="high"></param><param name="menu" value="false"></param><embed src="/static/games/pacman.swf" width="460" height="280" quality="high" pluginspage="https://www.macromedia.com/go/getflashplayer" type="application/x-shockwave-flash" menu="false" ></embed></object></td></tr>',
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
