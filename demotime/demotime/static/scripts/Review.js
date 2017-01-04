DemoTime.Review = Backbone.View.extend({
    el: 'body',

    events: {
        'click .review-changer': 'change_review_state'
    },

    initialize: function(options) {
        this.options = options;
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
                self.change_demo_state(type, link);
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
            } else {
                window.location.reload();
            }
        });
    },

    // Changing demo state
    change_demo_state: function(type, link) {
        if (type == 'cancelled' && link.data('draft')) {
            // Warn users when deleting a draft
            this.warn_before_closing_draft(type);
        } else if ((type == 'closed' || type == 'aborted') && this.options.reviewer_state == 'reviewing') {
            // Check to warn if there are active reviewers
            this.check_for_active_reviewers(type);
        } else {
            this.finish_demo_state_change(type);
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

        // Particularly for showing errors related to publishing a demo draft
        // with missing fields.
        req.error(function(err) {
            if (err.responseJSON) {
                self.$el.find('.error_messaging').remove();

                var err_html = '';
                err_html += '<div class="error_messaging"><ul class="errorlist">';

                for (var x = 0; x < err.responseJSON.errors.review.length; x++) {
                    err_html += '<li>' + err.responseJSON.errors.review[x] + '</li>';
                }

                err_html += '</ul></div>';

                self.$el.find('.container.content').prepend(err_html);
                $('html, body').animate({
                    scrollTop: self.$el.find('.container.content')
                }, 500);
            }
        });
    },

    warn_before_closing_draft: function(type) {
        var self = this;

        swal({
            title: "Are you sure?",
            text: "Be mindful that if this demo has co-owners, this will remove their draft as well.",
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
});
