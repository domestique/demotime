/** ajax-y comments */
DemoTime.Comments = Backbone.View.extend({
    el: '.comment_wrapper',

    events: {
        'click .collapser': 'collapse_comment',
        'click .expand_reply_link': 'expand_new_reply',
        'click .reply_and_approve': 'reply_and_approve',
        'click .new_comment_button': 'post_new_comment',
        'click .comment_edit': 'comment_edit'
    },

    initialize: function(options) {
        this.options = options || [];

        Mousetrap.bind('command+enter', function(e) {
            $(e.target).parents('.comment_form_container').find('.new_comment_button').click();
            return false;
        });
    },

    post_new_comment: function(event, also_approve) {
        var button = $(event.target),
            self = this,
            comment_parent = button.parents('.comment_parent'),
            thread = comment_parent.data('thread'),
            attachment_file = comment_parent.find('input[type="file"]'),
            attachment_type = comment_parent.find('select[name="attachment_type"]').val(),
            attachment_desc = comment_parent.find('input[name="description"]');

        // Saving container as an option for global use
        this.options.comment_form_container = button.parents('.comment_form_container');
        this.options.comment = comment_parent.find('.form-control').val();

        this.start_loading_state();

        // Check for 'editing' data attr, otherwise it's a new comment
        if (this.options.comment_form_container.data('editing')) {
            // PATCH needs data jsonified
            var data = {
                comment_pk: self.options.comment_pk,
                comment: self.options.comment,
                thread: thread
            }
            var req = $.ajax({
                url: self.options.comments_url,
                method: 'PATCH',
                dataType: 'json',
                data: JSON.stringify(data)
            });
        } else { // new comment
            var formData = new FormData();
            if (thread) {
                formData.append('thread', thread);
            }
            formData.append('comment', self.options.comment);
            if (attachment_file[0].files[0]) {
                formData.append('attachment', attachment_file[0].files[0]);
                formData.append('attachment_type', attachment_type);
                formData.append('sort_order', 1);
            }

            var req = $.ajax({
                url: self.options.comments_url,
                method: 'POST',
                contentType: false,
                processData: false,
                data: formData
            });
        }

        req.always(function() {
            // Remove any errors
            comment_parent.find('.errorlist').remove();

            // Cancel loading state
            self.end_loading_state();
        });

        req.success(function(data) {
            if (data.status == 'failure') {
                // Write the error message html
                self.show_errors(data.errors.comment);
            } else {
                // Slide up the editor if in a thread
                if (thread) {
                    self.options.comment_form_container.slideUp();
                } else {
                    comment_parent.find('.wysiwyg-editor').html('').focus();
                    self.options.comment_form_container.find('input[type="file"]').val('');
                    self.options.comment_form_container.find('select[name="attachment_type"]').val('');
                    self.options.comment_form_container.find('input[name="description"]').val('');

                }

                // Write the new comment HTML
                var html = self.get_success_html(data);

                // New comment DOM's a bit different than threaded DOM:
                if (thread) {
                    self.options.comment_form_container.parent().before(html);
                } else {
                    self.options.comment_form_container.before(html);
                }

                // Syntax highlighting
                comment_parent.find('pre').each(function(i, block) {
                    hljs.highlightBlock(block);
                });

                // If reply and approve, trigger button click, otherwise
                // just scroll the new comment in to view.
                if (also_approve) {
                    $('a[data-type="approved"]').click();
                } else {
                    $('html, body').animate({
                        scrollTop: comment_parent.find('.comments-reply').last().offset().top - 75
                    }, 500);

                    // Show 'new reply' link
                    if (self.options.trigger_link) {
                        self.options.trigger_link.show();
                    }
                }
            }
        });

        req.error(function(data) {
            // Write the error message html
            if (data.statusText == 'error') {
                self.show_errors('Sorry, the server is not responding at this time.');
            } else {
                self.show_errors(data.statusText);
            }
        });
    },

    get_success_html: function(data) {
        var html = '<div class="comment_parent comments-reply">';
        html += '<div class="demobox">'
        html += '<div class="demobox-header">Your comment <a href="#" class="comment_edit" data-comment="' + data.comment.id + '">edit this reply</a></div>'
        html += '<div class="demobox-body">' + this.options.comment;

        if (data.comment.attachment_count && data.comment.attachments[0].attachment_type == 'image') {
            html += '<br><br><div class="attachment-card image collapseable">\
                <section>\
                    <h3 class="heading icon icon-image">\
                        Image\
                    </h3>\
                    <span class="attachment-image">\
                        <a href="' + data.comment.attachments[0].static_url + '" class="lightbox_img">\
                            <img src="' + data.comment.attachments[0].static_url + '" class="img-thumbnail" height="300" width="300">\
                        </a>\
                    </span>\
                </section>\
            </div>';
        } else if (data.comment.attachment_count) {
            html += '<p><em>Your attachment was uploaded successfully.</em></p>';
        }

        html += '</div>'

        return html;
    },

    comment_edit: function(event) {
        var self = this,
            link = $(event.target),
            comment = link.parents('.comment_parent');

        // Grab edit html
        var edit_html = link.parents('.demobox').find('.demobox-body').html();

        event.preventDefault();

        // Remove old comment
        link.parents('.demobox').slideUp().remove();
        // Clean up conflicting DOM
        comment.find('.expand_reply_link, .icon-comment').remove();

        // Disable attachment editing (for now)
        comment.find('.attachments, .summary').remove();

        // Grab comment ID
        this.options.comment_pk = link.data('comment');

        // Set the form container
        this.options.comment_form_container = comment.find('.comment_form_container');

        // Enable 'editing' mode
        this.options.comment_form_container.data('editing', true);

        // Re-show wysiwyg
        this.options.comment_form_container.slideDown(function() {
            self.options.comment_form_container.find('.wysiwyg-editor').html(edit_html);
            self.options.comment_form_container.find('.wysiwyg-editor').focus();
            if ($(window).width() > 720) {
                $('html, body').animate({
                    scrollTop: self.options.comment_form_container.offset().top - 200
                }, 500);
            }
        });
    },

    show_errors: function(msg) {
        var self = this;
        this.options.comment_form_container.before('<ul class="errorlist"><li>' + msg + '</li></ul>');
        $('html, body').animate({
            scrollTop: self.options.comment_form_container.offset().top - 150
        }, 500);
    },

    start_loading_state: function() {
        this.options.comment_form_container.find('input, button').prop('disabled', true);
    },

    end_loading_state: function() {
        this.options.comment_form_container.find('input, button').prop('disabled', false);
    },

    // Leave a comment and approve at the same time
    reply_and_approve: function(event) {
        this.post_new_comment(event, true);
    },

    // Expand 'reply' wysiwyg on 'Leave a reply' click
    expand_new_reply: function(event) {
        event.preventDefault();

        this.options.trigger_link = $(event.target);

        // Grab and clean-up new comment_form_container
        var comment_form_container = this.options.trigger_link.next('.comment_form_container');
        comment_form_container.find('.wysiwyg-editor').html('');
        comment_form_container.find('input[type="file"]').val('');
        comment_form_container.find('select[name="attachment_type"]').val('');
        comment_form_container.find('input[name="description"]').val('');

        // Show new comment container
        this.options.trigger_link.next('.comment_form_container').slideDown(function() {
            comment_form_container.find('.wysiwyg-editor').focus();
            if ($(window).width() > 720) {
                $('html, body').animate({
                    scrollTop: comment_form_container.offset().top - 200
                }, 500);
            }
        });
        this.options.trigger_link.hide();
    }
});
