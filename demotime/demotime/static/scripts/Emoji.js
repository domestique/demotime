var GiphyModel = Backbone.Model.extend();
DemoTime.Emoji = Backbone.View.extend({
    el: '.emoji',

    events: {
        'click .add_emoji': 'add_emoji',
        'click .add_gif': 'add_gif',
        'keyup .giphy_input': 'capture_giphy_keyword',
        'click .giphy_button': 'giphy_button_click',
        'click .giphy_result_image': 'insert_giphy'
    },

    initialize: function(options) {
        this.options = options;
    },

    // Emoji click-to-add event
    add_emoji: function(event) {
        var img = $(event.target),
            self = this;

        img.parents('.wysiwyg-container').find('textarea').wysiwyg('shell').insertHTML("<img class='emoji' width='30' height='30' src='" + self.options.dt_url + img.attr('src') + "'>");
        img.parents('.wysiwyg-container').find('.wysiwyg-editor').trigger('keyup');
    },

    toggle_html: function(event) {
        var wysiwyg = $(event.target).parents('.wysiwyg-container'),
            editor = wysiwyg.find('.wysiwyg-editor');

        event.preventDefault();

        wysiwyg.find('textarea').slideToggle(function() {
            if ($(this).is(':visible')) {
                editor.hide();
            } else {
                editor.html($(this).val());
                editor.show();
            }
        });
    },

    add_gif: function(event) {
        this.options.wysiwyg = $(event.target).parents('.wysiwyg-container');
        var giphy_search_panel = this.options.wysiwyg.find('.giphy_input_panel');

        giphy_search_panel.slideToggle(function() {
            if ($(this).is(':visible')) {
                $(this).find('input').focus();
            }
        });
    },

    capture_giphy_keyword: function(event) {
        var input = $(event.target),
            code = event.keyCode;

        return event.keyCode != 13;

        if (code == 13) {
            event.preventDefault();
            this.search_giphy(input.val());
        }
    },

    giphy_button_click: function() {
        this.search_giphy(this.$el.find('.giphy_input').val());
    },

    // Giphy click-to-add event
    search_giphy: function(term) {
        var self = this;

        var req = $.ajax({
            url: self.options.giphy_url,
            method: 'get',
            data: {
                'q': term.replace(' ', '+')
            }
        });
        req.success(function(data) {
            var giphy_model = new GiphyModel(data.data);
            // Grab the container template
            var html = self.options.wysiwyg.find('#giphy_results').html(),
                template = _.template(html);
            template = template ({ gif: giphy_model.attributes });

            //self.options.wysiwyg.find('.giphy_results').html(template).slideDown();
        });
    },

    insert_giphy: function(event) {
        var gif = $(event.target),
            wysiwyg = gif.parents('.wysiwyg-container');

        gif.parents('.wysiwyg-container').find('textarea').wysiwyg('shell').insertHTML("<img src='" + gif.data('full') + "'>");
        wysiwyg.find('.wysiwyg-editor').trigger('keypress');
        wysiwyg.find('.giphy_results, .giphy_input_panel').slideUp();
    }
});
