$('body').on('click', '.toggle_sibling', function(event) {
    event.preventDefault();
    $(this).next().slideToggle();
});
$('body').on('click', 'a.attachment_delete', function(event) {
    var el = $(this);

    event.preventDefault();

    var del = $.ajax({
        type: "DELETE",
        url: el.data('url'),
        data: {}
    });

    del.always(function() {
        parent = el.parents('.demobox');
        parent.slideUp(function() {
            $(this).remove();
            if (!$('.current_attachments .demobox').length) {
                $('.current_attachments .attachments').html('No attachments found');
            }
        });
    });
});

$(document).ready(function() {
    if ($(window).width() > 375) {
        $('.subnav').stick_in_parent({
            'parent': 'body',
            'recalc_every': 100,
        });
    }
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
});

$('.review input:not(.find_person)').keyup(function() {
    window.onbeforeunload = function(e) {
        return 'You have unsaved changes. Exit DemoTime?.';
    };
});
