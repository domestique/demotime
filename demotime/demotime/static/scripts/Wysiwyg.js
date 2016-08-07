// Dynamically add/remove reviewers
var GiphyModel = Backbone.Model.extend({});
DemoTime.Wysiwyg = Backbone.View.extend({
    el: 'body',

    events: {
        'click .add_emoji': 'add_emoji',
        'click .add_gif': 'add_gif',
        'click .toggle_html': 'toggle_html',
        'keyup .giphy_input': 'capture_giphy_keyword',
        'click .giphy_button': 'giphy_button_click',
        'click .giphy_result_image': 'insert_giphy',
        'keypress form': 'disable_form_enter',
        'keypress .wysiwyg-editor': 'send_contents'
    },

    disable_form_enter: function(event) {
        if ($(event.target).hasClass('giphy_input')) {
            return event.keyCode != 13;
        }
    },

    // Send wysiwyg contents to hidden form on keypress
    send_contents: function(event) {
        var wysiwyg = $(event.target);
        wysiwyg.parents('.wysiwyg-container').find('.form-control').val(wysiwyg.html())
    },

    initialize: function(options) {
        this.options = options;

        $('textarea').wysiwyg({
            buttons: {
                insertimage: {
                    image: '\uf030'
                },
                bold: {
                    title: 'Bold (Ctrl+B)',
                    image: '\uf032',
                    hotkey: 'b'
                },
                italic: {
                    title: 'Italic (Ctrl+I)',
                    image: '\uf033',
                    hotkey: 'i'
                },
                underline: {
                    title: 'Underline (Ctrl+U)',
                    image: '\uf0cd',
                    hotkey: 'u'
                },
                strikethrough: {
                    title: 'Strikethrough (Ctrl+S)',
                    image: '\uf0cc',
                    hotkey: 's'
                },
                forecolor: {
                    title: 'Text color',
                    image: '\uf1fc'
                },
                orderedList: {
                    title: 'Ordered list',
                    image: '\uf0cb',
                    showselection: false
                },
                unorderedList: {
                    title: 'Unordered list',
                    image: '\uf0ca',
                    showselection: false
                },
                insertlink: {
                    title: 'Insert link',
                    image: '\uf08e'
                },
                removeformat: {
                    title: 'Remove format',
                    image: '\uf12d'
                }
            },
            submit: {
                title: 'Submit',
                image: '\uf00c'
            },
            selectImage: 'Click or drop image',
            placeholderUrl: 'http://example.com',
            maxImageSize: [600,600]
        });

        this.fix_tab_index();

        this.render();
    },

    // focus the wysiwyg when the input prior to hits TAB
    fix_tab_index: function() {
        var wysiwyg_form_group = this.$el.find('.wysiwyg-editor').parents('.form-group'),
            previous_input = wysiwyg_form_group.prev('.form-group').find('input');

        previous_input.keydown(function(event) {
            if (event.keyCode == 9) {
                event.preventDefault();
                wysiwyg_form_group.find('.wysiwyg-editor').focus();
            }
        });
    },

    // Add the custom footer to wysiwygs (emoticons)
    render: function() {
        var self = this;
        setTimeout(function() {
            // Grab the container template
            var html = $('#wysiwyg_footer').html(),
                template = _.template(html);
            template = template();

            self.$el.find('.wysiwyg-container').append(template);
        }, 1000);
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
        var giphy_search_panel = $(event.target).parents('.wysiwyg-container').find('.giphy_input_panel');

        giphy_search_panel.slideToggle(function() {
            if ($(this).is(':visible')) {
                $(this).find('input').focus();
            }
        });
    },

    capture_giphy_keyword: function(event) {
        var input = $(event.target),
            code = event.keyCode;

        if (code == 13) {
            event.preventDefault();
            this.search_giphy(input.val());
            input.val('');
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
            var html = $('#giphy_results').html(),
                template = _.template(html);
            template = template ({ gif: giphy_model.attributes });

            self.$el.find('.giphy_results').html(template).slideDown();
        });
    },

    insert_giphy: function(event) {
        var gif = $(event.target),
            wysiwyg = gif.parents('.wysiwyg-container'),
            editor = wysiwyg.find('.wysiwyg-editor'),
            html = editor.html(); // grab current html

        // Clear existing HTML (to append gif at end)
        editor.html('');
        // Write html/gif to wysiwyg
        gif.parents('.wysiwyg-container').find('textarea').wysiwyg('shell').insertHTML(html + "<img src='" + gif.data('full') + "'>");
        // Trigger wysiwyg key-up to send contents to form control
        wysiwyg.find('.wysiwyg-editor').trigger('keypress');
        // Slide up wysiwyg panel
        wysiwyg.find('.giphy_results, .giphy_input_panel').slideUp();
    }
});
