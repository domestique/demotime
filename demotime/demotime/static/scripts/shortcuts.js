$('textarea').addClass('mousetrap');

Mousetrap.bind('command+enter', function(e) {
    $(e.target).parents('form').submit();
    return false;
});
