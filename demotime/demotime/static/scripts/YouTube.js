/** convert URLs to YouTube */
DemoTime.YouTube = Backbone.View.extend({
    initialize: function(options) {
        $('.comments a').each(function() {
            var yturl= /(?:https?:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?([\w\-]{10,12})(?:&feature=related)?(?:[\w\-]{0})?/g;
            var ytplayer= '<iframe width="640" height="360" src="http://www.youtube.com/embed/$1" frameborder="0" allowfullscreen></iframe>';

            var url = $(this).attr('href');
            if (url != null) {
                var matches = url.match(yturl);
                if (matches) {
                    var embed = $(this).attr('href').replace(yturl, ytplayer);
                    var iframe = $(embed);

                    iframe.insertAfter(this);
                    $(this).remove();
                }
            }
        });
    }
});
var youtube = new DemoTime.YouTube();
