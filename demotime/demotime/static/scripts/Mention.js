var MentionModel = Backbone.Model.extend();

DemoTime.Mention = Backbone.View.extend({
    el: 'body',

    events: {
        'keyup .trumbowyg-editor': 'changed',
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

            // Grab the mentioner container template (popup)
            var html = $('#mentioner').html();
            self.options.template = _.template(html);
            self.options.template = self.options.template ({ user: self.users.get('users') });
        });
    },

    // The actual 'user is typing' event
    changed: function(event) {
        var wysiwyg = $(event.target),
            parent_form = wysiwyg.parents('form'),
            control = parent_form.find('.form-control'),
            editor = parent_form.find('.trumbowyg-editor'),
            interval = 250,
            self = this,
            timer;

        // Set an interval checker
        timer = setTimeout(do_mention, interval);
        lastWord = this.get_word(wysiwyg[0]);

        // The actual mention popup (triggered by interval)
        function do_mention() {
            // Clear the interval
            clearTimeout(timer);

            parent_form.find('.mentioner').remove();

            // Write the HTML for the popup
            wysiwyg.before(self.options.template)

            // Cleanse the popup of non-matching users
            $('.mentioner-user').each(function() {
                mentioned_user = $(this).html().toLowerCase();
                if (!mentioned_user.indexOf(lastWord.replace('@', '').toLowerCase()) == 0) {
                    $(this).remove();
                }
            });

            // Pop up the box after giving JS a chance to cleanse
            if ($('.mentioner-user').length) {
                setTimeout(function() {
                    parent_form.find('.mentioner').show();
                }, 300);
            }
        }
    },

    get_word: function(sel) {
        // Use JS to grab the last word typed
        var word = "";
        if (window.getSelection && (sel = window.getSelection()).modify) {
            var selectedRange = sel.getRangeAt(0);
            sel.collapseToStart();
            sel.modify("move", "backward", "word");
            sel.modify("extend", "forward", "word");

            word = sel.toString();

            // Restore selection
            sel.removeAllRanges();
            sel.addRange(selectedRange);
        } else if ( (sel = document.selection) && sel.type != "Control") {
            var range = sel.createRange();
            range.collapse(true);
            range.expand("word");
            word = range.text;
        }

        return '@' + word;
    },

    // The actual 'click' event inside the popup
    add: function(event) {
        var link = $(event.target),
            form = link.parents('form'),
            wysiwyg = form.find('.trumbowyg-editor');

        event.preventDefault();

        // Focus the wysiwyg
        wysiwyg.get(0).focus();

        // Insert the clicked item with a hook for cleaning up user input
        this.insert_text('||@' + link.html());

        // move the caret after the @mention
        this.move_caret(wysiwyg.get(0));

        // Clean up the final mention
        wysiwyg.html(wysiwyg.html().replace(/\S*\|\|/g, '').replace('@@', '@'));

        // And hide the box after selecting a user.
        form.find('.mentioner').remove();
    },

    // Insert text at caret position within a contenteditable div
    insert_text: function(text) {
        var sel, range, html;
        if (window.getSelection) {
            sel = window.getSelection();
            if (sel.getRangeAt && sel.rangeCount) {
                range = sel.getRangeAt(0);
                range.deleteContents();
                range.insertNode( document.createTextNode(text) );
            }
        } else if (document.selection && document.selection.createRange) {
            document.selection.createRange().text = link.html();
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
