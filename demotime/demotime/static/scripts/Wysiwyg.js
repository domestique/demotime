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
            'height': '150',
            maximumImageFileSize: 2621440, // 2.5MB
            shortcuts: false,
            toolbar: [
                ['style', ['color', 'bold', 'italic', 'underline', 'strikethrough', 'clear']],
                ['para', ['ul', 'ol']],
                ['misc', ['undo', 'redo', 'codeview', 'link']],
                ['insert', ['table', 'picture']]
            ]
        });

        this.fix_tab_index();

        this.render();
    },

    // focus the wysiwyg when the input prior to hits TAB
    fix_tab_index: function() {
        var wysiwyg_form_group = this.$el.find('.note-editor').parents('.form-group'),
            previous_input = wysiwyg_form_group.prev('.form-group').find('input');

        previous_input.keydown(function(event) {
            if (event.keyCode == 9) {
                event.preventDefault();
                wysiwyg_form_group.find('textarea').summernote('focus');
                // clean up
                wysiwyg_form_group.find('.note-editor .note-editor').remove();
            }
        });
    },

    render: function() {
        var self = this;
        setTimeout(function() {
            // Grab the container template
            var html = $('#wysiwyg_footer').html(),
                template = _.template(html);
            template = template();

            self.$el.find('.note-editor').append(template);
        }, 1000);
    },

    add: function(event) {
        var img = $(event.target),
            self = this;

        img.parents('.note-editor').prev('textarea').summernote('insertImage', self.options.dt_url + img.attr('src'), function ($image) {
            $image.addClass('emoji');
            $image.attr('width', '30');
            $image.attr('height', '30');
        });
    }
});
