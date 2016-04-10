// Dynamically add/remove reviewers
DemoTime.Emoji = Backbone.View.extend({
    el: '.review',

    events: {
        'click .add_emoji': 'add'
    },

    initialize: function() {
        this.render();
    },

    render: function() {
        var self = this;
        setTimeout(function() {
            // Grab the container template
            var html = $('#emoji').html(),
                template = _.template(html);
            template = template();

            self.$el.find('.note-editor').append(template);
        }, 1000);
    },

    add: function(event) {
        var img = $(event.target);
        $summernote.summernote('insertImage', img.attr('src'));
    }
});
