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

        req.always(function(msg) {
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
});
