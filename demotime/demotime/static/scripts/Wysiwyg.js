// Dynamically add/remove reviewers
DemoTime.Wysiwyg = Backbone.View.extend({
    el: 'body',

    events: {
        'click .add_emoji': 'add'
    },

    initialize: function(options) {
        this.options = options;

        $('textarea').trumbowyg({
            autogrow: true
        });

        this.render();
    },

    // Add the custom footer to wysiwygs (emoticons)
    render: function() {
        var self = this;
        setTimeout(function() {
            // Grab the container template
            var html = $('#wysiwyg_footer').html(),
                template = _.template(html);
            template = template();

            self.$el.find('.trumbowyg-box').append(template);
        }, 1000);
    },

    // Emoticon click-to-add event
    add: function(event) {
        var img = $(event.target),
            self = this;

        img.parents('.trumbowyg-box').find('.trumbowyg-editor').append("<img class='emoji' width='30' height='30' src='" + self.options.dt_url + img.attr('src') + "'>").trigger('keyup');
    }
});
