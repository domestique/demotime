/** ajax-y comments */
DemoTime.Comments = Backbone.View.extend({
    el: '.comment_wrapper',

    events: {
        'click .collapser': 'collapse_comment',
        'click .expand_reply_link': 'expand_new_reply',
        'click .reply_and_approve': 'reply_and_approve',
        'click .new_comment_button': 'post_new_comment'
    },

    initialize: function(options) {
        this.options = options;
    },

    post_new_comment: function(event) {
        var button = $(event.target),
            self = this,
            comment_parent = button.parents('.comment_parent'),
            comment = comment_parent.find('.form-control').val(),
            thread = comment_parent.data('thread');
            //attachment_file = comment_parent.find('select[name="attachment"]'),
            //attachment_type = comment_parent.find('select[name="attachment_type"]'),
            //attachment_desc = comment_parent.find('select[name="description"]'),

        var req = $.ajax({
            url: self.options.comments_url,
            method: 'POST',
            data: {
                thread: thread,
                comment: comment
            }
        });

        req.success(function(data) {
            console.log(data);
        });

        req.error(function(data) {
            console.log(data);
        });
    },

    // Leave a comment and approve at the same time
    reply_and_approve: function(event) {},

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
        link.remove();
    }
});
