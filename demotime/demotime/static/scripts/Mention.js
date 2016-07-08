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

    // The initial AJAX receive of users
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
                // Grab the mentioner container template (popup)
                var html = $('#mentioner').html();
                self.options.template = _.template(html);
                self.options.template = self.options.template ({ user: self.users.get('users') });
            }, 1000);
        });
    },

    // The actual 'user is typing' event
    changed: function(event) {
        var wysiwyg = $(event.target),
            parent_form = wysiwyg.parents('form'),
            control = parent_form.find('.form-control'),
            interval = 250,
            self = this,
            timer;

        // Set an interval checker
        timer = setTimeout(do_mention, interval);
        parent_form.find('.mentioner').hide();

        // Use JS to grab the last word typed
        var words = control.val().replace(/<\/?[^>]+>/gi, '').split(' ');
        var lastWord = words[words.length - 1];

        // The actual mention popup
        function do_mention() {
            // Clear the interval
            clearTimeout(timer);

            // If the last word is a mention and has good length... (32 = space)
            if (lastWord.match('@') && lastWord.length > 1 && event.keyCode != 32) {
                // Split the array
                var name_array = lastWord.split('@');
                // Assign a temporary string to clean up later (@ma should be replaced by @Mark)
                self.options.temp_string = name_array[name_array.length - 1];
                // Clean up the string for searching (damn you wysiwyg)
                user = self.options.temp_string.replace('&nbsp;', '').toLowerCase();

                // Write the HTML for the popup
                wysiwyg.before(self.options.template)

                // Cleanse the popup of non-matching users
                $('.mentioner-user').each(function() {
                    mentioned_user = $(this).html().toLowerCase();
                    if (!mentioned_user.indexOf(user) == 0) {
                        $(this).remove();
                    }
                });

                // Pop up the box after giving JS a chance to cleanse
                if ($('.mentioner-user').length) {
                    setTimeout(function() {
                        parent_form.find('.mentioner').show();
                    }, 250);
                }
            } else {
                // Not a mention, so hide the mentioner box
                parent_form.find('.mentioner').hide();
            }
        }
    },

    // The actual 'click' event inside the popup
    add: function(event) {
        var link = $(event.target),
            form = link.parents('form'),
            wysiwyg = form.find('.note-editable');

        event.preventDefault();

        console.log(this.options.temp_string + ":" + link.html())
        // Write the popped name in to the WYSIWYG, replacing the previously typed string
        wysiwyg.html(wysiwyg.html().replace('@' + this.options.temp_string, '<span class="mentioned">' + link.html() + '</span>&nbsp;'));

        // And hide the box after selecting a user.
        form.find('.mentioner').hide();

        //form.summernote('restoreRange');
    }
})
