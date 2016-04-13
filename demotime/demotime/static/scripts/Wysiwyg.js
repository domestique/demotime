// Dynamically add/remove reviewers
DemoTime.Wysiwyg = Backbone.View.extend({
    el: 'body',

    events: {
        'click .add_emoji': 'add'
    },

    initialize: function(options) {
        this.options = options;

        $('textarea').summernote({
            'width': '100%',
            'height': '100',
            shortcuts: false,
            toolbar: [
                ['style', ['color', 'bold', 'italic', 'underline', 'strikethrough', 'clear']],
                ['para', ['ul', 'ol']],
                ['misc', ['undo', 'redo', 'codeview', 'link']],
                ['insert', ['table']]
            ]
        });
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

        img.parents('.note-editor').prev('textarea').summernote('insertImage', this.options.dt_url + img.attr('src'), function ($image) {
            $image.addClass('emoji');
        });
    }
});
