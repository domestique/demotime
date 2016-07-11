DemoTime.Review = Backbone.View.extend({
    el: 'body',

    events: {
        'click .collapser': 'collapse_comment',
        'click .review-changer': 'change_review_state',
        'click .leave_reply_link': 'leave_reply',
        'click .reply_and_approve': 'reply_and_approve'
    },

    initialize: function(options) {
        this.options = options;
        this.setup_comment_hooks();
        this.render();
    },

    render: function() {
        // Spawn new windows for links
        this.$el.find('.review-overview a').attr('target', '_blank');
    },

    // Update the 'state' of the review, be it a reviwer
    // state change or an over-arching demo state change
    change_review_state: function(event) {
        var self = this,
            link = $(event.target),
            type = link.data('type');

        event.preventDefault();

        if (!type) return false;

        if (self.options.is_reviewer || self.options.is_creator) {
            if (self.options.is_reviewer) {
                self.change_reviewer_state(type, 'reload');
            }
            if (self.options.is_creator) {
                self.change_demo_state(type);
            }
        }
    },

    // Changing reviewer state
    change_reviewer_state: function(type, action) {
        var self = this;

        // Sets the new reviewer status
        var req = $.ajax({
            url: self.options.reviewer_url,
            method: 'POST',
            data: {
                review: self.options.review_pk,
                reviewer: self.options.reviewer_pk,
                status: type
            }
        });

        req.success(function(msg) {
            if (msg.success) {
                window.location.hash = 'state_change';
                if (action == 'reload') {
                    window.location.reload();
                }
            }
        });
    },

    // Leave a comment and approve at the same time
    reply_and_approve: function(event) {
        var self = this,
            button = $(event.target);
        this.change_reviewer_state(button.data('type'));
        setTimeout(function() {
            button.parents('form').attr('action', '');
            button.parents('form').submit();
        }, 500);
    },

    // Changing demo state
    change_demo_state: function(type) {
        var self = this;

        // Check to warn if there are active reviewers
        if ((type == 'closed' || type == 'aborted') && self.options.reviewer_state == 'reviewing') {
            self.check_for_active_reviewers(type);
        } else {
            self.finish_demo_state_change(type);
        }
    },

    // Finishing the demo state change after confirm
    finish_demo_state_change: function(type) {
        var self = this;

        var req = $.ajax({
            url: self.options.review_url,
            method: 'POST',
            data: {
                review: self.options.review_pk,
                reviewer: self.options.creator_pk,
                state: type
            }
        });

        req.success(function(msg) {
            if (msg.success) {
                window.location.hash = 'state_change';
                window.location.reload();
            }
        });
    },

    check_for_active_reviewers: function(type) {
        var self = this;

        swal({
            title: "Are you sure?",
            text: "There are active reviewers. Are you sure you wish to change this review to " + type + "?",
            type: "warning",
            showCancelButton: true,
            confirmButtonColor: "#DD6B55",
            confirmButtonText: "Confirm",
            closeOnConfirm: false
        },
        function (isConfirm) {
            if (isConfirm) {
                self.finish_demo_state_change(type);
                swal.close();
            }
        });
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

    setup_comment_hooks: function() {
        // Attach comment pk's to form submits for
        // smooth scroll to comment after sending it
        $('[data-comment]').each(function() {
            var comment = $(this),
                form = comment.parents('.comment_parent').find('form');

            if (comment.prop('id')) {
                form.attr('action', '#' + comment.prop('id'));
            } else {
                form.attr('action', '#comments');
            }
        });
    },

    leave_reply: function(event) {
        event.preventDefault();
        var link = $(event.target);

        link.next('.comment_container').slideDown(function() {
            $(this).find('textarea').summernote('focus');
            $(this).find('.note-editor .note-editor').remove();
        });
        link.remove();
    }
});
