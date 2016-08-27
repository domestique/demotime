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
            $(e.target).parents('.comment_container').find('.new_comment_button').click();
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
        this.options.container = button.parents('.comment_container');
        this.options.comment = comment_parent.find('.form-control').val();

        this.start_loading_state();

        // Check for 'editing' data attr, otherwise it's a new comment
        if (this.options.container.data('editing')) {
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
                // Slide up the editor
                self.options.container.slideUp();

                // Write the new comment HTML
                var html = self.get_success_html(data);

                // Save pk for editing
                self.options.comment_pk = data.comment.id;

                // New comment DOM's a bit different than threaded DOM:
                if (thread) {
                    self.options.container.parent().before(html);
                } else {
                    self.options.container.before(html);
                }

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
        var html = '<div class="comments-reply">';

        html += '<blockquote><div class="blockquote-body">' + this.options.comment;

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

        html += '<br><br>(<a href="#" class="comment_edit">edit</a>)</div></blockquote>';

        html += '</div>'

        return html;
    },

    comment_edit: function(event) {
        var self = this;
        event.preventDefault();

        // Remove old comment
        $(event.target).parents('.comments-reply').slideUp().remove();

        // Disable attachment editing (for now)
        this.options.container.find('.attachments, .summary').remove();

        // Enable 'editing' mode
        this.options.container.data('editing', true);

        // Re-show wysiwyg
        this.options.container.slideDown(function() {
            self.options.container.find('.wysiwyg-editor').focus();
        });
    },

    show_errors: function(msg) {
        var self = this;
        this.options.container.before('<ul class="errorlist"><li>' + msg + '</li></ul>');
        $('html, body').animate({
            scrollTop: self.options.container.offset().top - 150
        }, 500);
    },

    start_loading_state: function() {
        this.options.container.find('input, button').prop('disabled', true);
    },

    end_loading_state: function() {
        this.options.container.find('input, button').prop('disabled', false);
    },

    // Leave a comment and approve at the same time
    reply_and_approve: function(event) {
        this.post_new_comment(event, true);
    },

    // Expand collapse top level comments
    collapse_comment: function(event) {
        var e = event,
            collapser = $(event.target);

        if (collapser.prop("tagName") != "A") {
            collapser.parents('.collapser_parent').find('.collapseable').slideToggle(function() {
                if (collapser.attr('class').match('squared')) {
                    if ($(this).is(":visible")) {
                        collapser.removeClass('icon-plus-squared-alt');
                        collapser.addClass('icon-minus-squared-alt');
                    } else {
                        collapser.addClass('icon-plus-squared-alt');
                        collapser.removeClass('icon-minus-squared-alt');
                    }
                }
            });
        }
    },

    // Expand 'reply' wysiwyg on 'Leave a reply' click
    expand_new_reply: function(event) {
        event.preventDefault();

        this.options.trigger_link = $(event.target);

        this.options.trigger_link.next('.comment_container').slideDown(function() {
            var container = $(this);
            container.find('.wysiwyg-editor').html('').focus();
            container.find('input[type="file"]').val('');
            container.find('select[name="attachment_type"]').val('');
            container.find('input[name="attachment_description"]').val('');
            if ($(window).width() > 720) {
                $('html, body').animate({
                    scrollTop: container.offset().top - 200
                }, 500);
            }
        });
        this.options.trigger_link.hide();
    }
});
