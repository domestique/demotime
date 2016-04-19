// Message counts, reviews with new comments, etc.
DemoTime.BackgroundTasks = Backbone.View.extend({
    el: 'body',

    initialize: function(options) {
        this.options = options;
        this.render();
    },

    render: function() {
        var self = this;

        setInterval(function() {
            if (self.options.messages_url) {
                self.fetch_new_messages();
            }
            if (self.options.comments_url) {
                self.fetch_new_comments();
            }
        }, 5000);
    },

    // Update the header with any new messages
    fetch_new_messages: function() {
        var self = this;

        var req = $.ajax({
            url: self.options.messages_url
        });

        req.always(function(data) {
            if (data.message_count > 0) {
                $('.msg_notifier').removeClass('read_notification').addClass('unread_notification').find('a').html(data.message_count);
            } else {
                $('.msg_notifier').removeClass('unread_notification').addClass('read_notification').find('a').html(data.message_count);
            }
        });
    },

    // Show a balloon if there are updates to the review you are viewing.
    fetch_new_comments: function() {
        var self = this;

        var req = $.ajax({
            url: self.options.comments_url
        });

        req.success(function(data) {
            if (data.message_count > 0 && !self.options.noty) {
                var update_obj = data.bundles[0].messages[0],
                    bundle_obj = data.bundles[0];

                if (update_obj) {
                    self.options.noty = noty({
                        text: update_obj.message_title + ' (click to refresh)',
                        layout: 'bottomRight',
                        type: 'warning',
                        animation: {
                            open: 'animated flipInX',
                            close: 'animated flipOutX',
                            easing: 'swing', // easing
                            speed: 500 // opening & closing animation speed
                        },
                        callback: {
                            onCloseClick: function() {
                                // Redirect the user to the comment
                                if (update_obj.is_comment) {
                                    var url_hook = '#comments';
                                    window.location.href = self.options.dt_url + '#comments';
                                    window.location.reload();
                                // Or just reload the review
                                } else {
                                    window.location.href = self.options.dt_url;
                                }
                            }
                        }
                    });
                }
            }
        });
    }
});
