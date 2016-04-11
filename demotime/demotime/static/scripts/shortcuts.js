setTimeout(function () {
    $('textarea, .panel-body').addClass('mousetrap');
}, 100);

Mousetrap.bind('command+enter', function(e) {
    $(e.target).parents('form').submit();
    return false;
});
