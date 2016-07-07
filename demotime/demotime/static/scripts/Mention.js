var MentionModel = Backbone.Model.extend();

DemoTime.Mention = Backbone.View.extend({
    el: 'body',

    events: {
        'keyup .note-editable': 'changed',
        'click .mentioner-user': 'add'
    },

    initialize: function(options) {
        this.options = options;
        this.render();
    },

    render: function() {
        var self = this;

        var user_req = $.ajax({
            url: self.options.user_url,
            method: 'POST',
            data: {
                action: 'search_users',
                name: ''
            }
        });

        user_req.success(function(data) {
            self.users = new MentionModel(data);

            setTimeout(function() {
                // Grab the container template
                var html = $('#mentioner').html();
                self.options.template = _.template(html);
                self.options.template = self.options.template ({ user: self.users.get('users') });
            }, 1000);
        });
    },

    changed: function(event) {
        $('.form-control').show();
        var wysiwyg = $(event.target),
            parent_form = wysiwyg.parents('form'),
            control = parent_form.find('.form-control'),
            interval = 250,
            self = this,
            timer;

        timer = setTimeout(do_mention, interval);
        parent_form.find('.mentioner').hide();

        var words = control.val().replace(/<\/?[^>]+>/gi, '').split(' ');
        var lastWord = words[words.length - 1];
        lastWord = lastWord.replace('&nbsp;', '');

        function do_mention() {
            if (lastWord.match('@') && lastWord.length > 1 && event.keyCode != 32) {
                clearTimeout(timer);

                var name_array = lastWord.split('@');
                self.options.temp_user = name_array[name_array.length - 1];
                user = self.options.temp_user.replace('@', '').replace('&nbsp;', '').toLowerCase();
                console.log(user.replace('&nbsp;', ''));

                wysiwyg.before(self.options.template)
                $('.mentioner-user').each(function() {
                    mentioned_user = $(this).html().toLowerCase();
                    if (!mentioned_user.indexOf(user) == 0) {
                        $(this).remove();
                    }
                });
                setTimeout(function() {
                    parent_form.find('.mentioner').show();
                }, 250);
                if (!$('.mentioner-user').length) {
                    $('.mentioner').remove();
                }
            } else {
                parent_form.find('.mentioner').hide();
            }
        }
    },

    add: function(event) {
        var link = $(event.target),
            form = link.parents('form'),
            wysiwyg = form.find('.note-editable'),
            self = this;

        event.preventDefault();

        wysiwyg.html(wysiwyg.html().replace(this.options.temp_user, link.html()));
        link.parents('form').find('.mentioner').hide();
    }
})
