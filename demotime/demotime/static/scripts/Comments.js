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
        this.options = options;

        Mousetrap.bind('command+enter', function(e) {
            $(e.target).parents('.comment_container').find('.new_comment_button').click();
            return false;
        });
    },

    post_new_comment: function(event, also_approve) {
        var button = $(event.target),
            self = this,
            comment_parent = button.parents('.comment_parent'),
            container = button.parents('.comment_container'),
            comment = comment_parent.find('.form-control').val(),
            thread = comment_parent.data('thread');
            attachment_file = comment_parent.find('input[type="file"]'),
            attachment_type = comment_parent.find('select[name="attachment_type"]').val(),
            attachment_desc = comment_parent.find('input[name="description"]');

        // Check for 'editing' data attr, otherwise it's a new comment
        if (container.data('editing')) {
            // PATCH needs data jsonified
            var data = {
                comment_pk: self.options.comment_pk,
                thread: thread,
                comment: comment
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
            formData.append('comment', comment);
            if (attachment_file[0].files[0]) {
                formData.append('attachment', attachment_file[0].files[0]);
                formData.append('attachment_type', attachment_type);
            }

            var req = $.ajax({
                url: self.options.comments_url,
                method: 'POST',
                contentType: false,
                processData: false,
                data: formData
            });
        }

        req.success(function(data) {
            // Slide up the editor
            container.slideUp();

            // Write the new comment HTML
            var html = '<div class="comments-reply">'

            html += '<blockquote>' + comment;

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

            html += '<br><br>(<a href="#" class="comment_edit">edit</a>)</blockquote>';

            html += '</div>'

            // Save some values for editing
            self.options.container = container;
            self.options.comment_pk = data.comment.id;

            // New comment DOM's a bit different than threaded DOM:
            if (thread) {
                container.parent().before(html);
            } else {
                container.before(html);
            }

            if (also_approve) {
                $('a[data-type="approved"]').click();
            }
        });

        req.error(function(data) {
            // Write the error message html
            container.before('<ul class="errorlist"><li>' + data.responseJSON.errors + '</li></ul>');
        });
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
        var link = $(event.target);

        link.next('.comment_container').slideDown(function() {
            $(this).find('.wysiwyg-editor').focus();
        });
        link.hide();
    }
});
