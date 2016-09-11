var MentionModel = Backbone.Model.extend();

DemoTime.Mention = Backbone.View.extend({
    el: 'body',

    events: {
        'keyup .wysiwyg-editor': 'mention_checker',
        'keydown .wysiwyg-editor': 'navigate_mentions',
        'click .mentioner-user': 'add'
    },

    initialize: function(options) {
        this.options = options;
        this.options.interval = 250;

        // Catch arrows for nav
        var self = this;

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

            if ($('#mentioner').length) {
                // Grab the mentioner container template (popup)
                var html = $('#mentioner').html();
                self.options.template = _.template(html);
                self.options.template = self.options.template ({ user: self.users.get('users') });
            }
        });
    },

    // Keyboard navigation within the @mentions bar
    navigate_mentions: function(event) {
        var wysiwyg = $(event.target),
            code = event.keyCode,
            self = this;

        this.options.form = wysiwyg.parents('form');
        var mentioner = this.options.form.find('.mentioner');
        clearTimeout(self.options.timer);

        if (mentioner.is(':visible') && this.using_arrows(code)) {
            event.preventDefault();

            // 37 = left, 38 = up, 39 = right, 40 = down
            if (code == 37) {
                current = mentioner.find('.mentioner-active');
                if (current.prev().length) {
                    current.prev().addClass('mentioner-active');
                    current.removeClass('mentioner-active');
                }
            } else if (code == 38) {
                mentioner.find('.mentioner-active').removeClass('mentioner-active');
                mentioner.find('a').first().addClass('mentioner-active');
            } else if (code == 39) {
                current = mentioner.find('.mentioner-active');
                if (current.next().length) {
                    current.next().addClass('mentioner-active');
                    current.removeClass('mentioner-active');
                }
            } else if (code == 40) {
                mentioner.find('.mentioner-active').removeClass('mentioner-active');
                mentioner.find('a').last().addClass('mentioner-active');
            }

            if (code == 13) {
                mentioner.find('.mentioner-active').click();
            }
        }
    },

    // Clear countdown on keyup, trigger mention
    mention_checker: function(event) {
        var self = this,
            code = event.keyCode;

        if (self.options.form) {
            var mentioner = self.options.form.find('.mentioner');
        }

        if (mentioner) {
            clearTimeout(self.options.timer);

            // If the user isn't pressing an arrow key (navigating mentions)
            // then remove the mentioner (to avoid previous mention popups
            // while typing.
            if (!self.using_arrows(code)) {
                mentioner.remove();
            }

            // Execute after the interval is done
            function finished() {
                // If the mentioner isn't already visible...
                if (!mentioner.is(':visible')) {
                    self.get_last_word(event);
                }
            }
            self.options.timer = setTimeout(finished, self.options.interval);
        }
    },

    // Return true if the user is navigating with arrows
    using_arrows: function(code) {
        if ((code >= 37 && code <= 40) || code == 13) {
            return true;
        } else {
            return false;
        }
    },

    // Grabbing the last word typed
    get_last_word: function(event) {
        var wysiwyg = $(event.target),
            clean_html = wysiwyg.html().replace(/<.*?>/g, ' ');

        this.options.last_word = clean_html.substr(clean_html.trim().lastIndexOf(" ")+1).trim();

        if (this.options.last_word.length > 1) {
            this.do_mention(event);
        }
    },

    // The actual mention popup (triggered by interval)
    do_mention: function(event) {
        var wysiwyg = $(event.target),
            self = this;

        self.options.form.find('.mentioner').remove();

        // Write the HTML for the popup
        wysiwyg.before(self.options.template)

        // Cleanse the popup of non-matching users
        $('.mentioner-user').each(function() {
            mentioned_user = $(this).html().toLowerCase();
            if (!mentioned_user.indexOf(self.options.last_word.replace('@', '').replace('&nbsp;', '').toLowerCase()) == 0) {
                $(this).remove();
            }
        });
        $('.mentioner-user').first().addClass('mentioner-active');

        // Pop up the box after giving JS a chance to cleanse
        if ($('.mentioner-user').length) {
            if (self.options.form.find('.mentioner').not(':visible')) {
                self.options.form.find('.mentioner').show();
            }
        }
    },

    // The actual 'click' event inside the popup
    add: function(event) {
        var link = $(event.target),
            wysiwyg = this.options.form.find('.wysiwyg-editor');

        event.preventDefault();

        // Focus the wysiwyg
        wysiwyg.get(0).focus();

        // Insert the clicked item with a hook for cleaning up user input
        // (we have to delete what they typed after inserting the mention)
        wysiwyg.parents('form').find('textarea').wysiwyg('shell').insertHTML('||@' + link.html());

        // Clean up the final mention (support for the user typing @name and cleansing any
        // wysiwyg HTML)
        wysiwyg.html(wysiwyg.html().replace(/[^<> \t\n\r\f\v]*\|\|/g, '').replace('@@', '@'));

        // move the caret after the @mention to
        // let the user continue typing normally
        this.move_caret(wysiwyg.get(0));

        // And hide the box after selecting a user.
        if (this.options.form.find('.mentioner').is(':visible')) {
            this.options.form.find('.mentioner').remove();
        }
    },

    // Move caret within a contenteditable div
    move_caret: function(el) {
        if (typeof window.getSelection != "undefined"
                && typeof document.createRange != "undefined") {
            var range = document.createRange();
            range.selectNodeContents(el);
            range.collapse(false);
            var sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
        } else if (typeof document.body.createTextRange != "undefined") {
            var textRange = document.body.createTextRange();
            textRange.moveToElementText(el);
            textRange.collapse(false);
            textRange.select();
        }
    }
})
