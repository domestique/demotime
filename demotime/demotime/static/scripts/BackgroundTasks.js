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

    fetch_new_messages: function() {
        var self = this;

        var req = $.ajax({
            url: self.options.messages_url
        });

        req.success(function(data) {
            if (data.message_count > 0) {
                $('.msg_notifier').removeClass('read_notification').addClass('unread_notification').find('a').html(data.message_count);
            }
        });
    },

    fetch_new_comments: function() {
        var self = this;

        var req = $.ajax({
            url: self.options.comments_url
        });

        req.success(function(data) {
            var update_obj = data.bundles[0].messages[0],
                bundle_obj = data.bundles[0];
            if (data.message_count > 0 && !self.options.noty) {
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
                            // Mark message as read on balloon click
                            var bundle_array = new Array();

                            // Create an array from the bundle pk
                            bundle_array.push(bundle_obj.bundle_pk);

                            // Send request to mark message as read
                            var req = $.ajax({
                                url: self.options.messages_url,
                                method: 'POST',
                                data: {
                                    'messages': bundle_array,
                                    'action': 'read'
                                }
                            });

                            req.success(function(data) {
                                // Redirect the user to the comment
                                window.location.href = window.location.origin + window.location.pathname + '#' + update_obj.comment_pk;
                            });
                        }
                    }
                });
            }
        });
    },
});
