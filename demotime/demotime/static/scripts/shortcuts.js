setTimeout(function () {
    $('textarea, .wysiwyg-editor').addClass('mousetrap');
}, 100);

Mousetrap.bind('command+enter', function(e) {
    /* for fast typers */
    $(e.target).trigger('keypress');
    /* submit! */
    $(e.target).parents('form').submit();
    return false;
});
