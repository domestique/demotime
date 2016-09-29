/** Message counts, reviews with new comments, etc. */
DemoTime.BackgroundTasks = Backbone.View.extend({
    el: 'body',

    initialize: function(options) {
        this.options = options;
        this.options.counter = 0;
        this.options.message_count = 0;
        this.options.check_every = 15000; // check for msgs every 15 seconds (15,000ms)
        this.options.max_attempts = 480; // after 2 hours of inactivity, ajax stops
        this.render();
    },

    render: function() {
        var self = this;

        self.options.interval = setInterval(function() {
            if (self.options.messages_url) {
                self.fetch_new_messages();
            }
            if (self.options.json_url) {
                self.fetch_new_comments();
                self.check_activity_count();
            }

        }, self.options.check_every);
    },

    check_activity_count: function() {
        var self = this;

        // Cancelling background task after a period of no activity
        if ((self.options.counter > self.options.max_attempts) && self.options.interval) {
            clearInterval(self.options.interval);
            self.options.noty = noty({
                text: 'Background tasks have timed out on this page (click to refresh)',
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
                        window.location.reload();
                    }
                }
            });
        }
    },

    // Update the header with any new messages
    fetch_new_messages: function() {
        var self = this;

        var req = $.ajax({
            url: self.options.messages_url
        });

        req.always(function(data) {
            console.log(data);
            if (data.message_count > 0) {
                console.log('Running background tasks and received new messages');
                $('.msg_notifier').removeClass('read_notification').addClass('unread_notification').find('a').html(data.message_count);
                if (!self.options.original_page_title) {
                    self.options.original_page_title = document.title;
                }
                document.title = '(' + data.message_count + ') ' + self.options.original_page_title;
            } else {
                console.log('Running background tasks and received no new messages');
                $('.msg_notifier').removeClass('unread_notification').addClass('read_notification').find('a').html(data.message_count);
                self.options.counter = self.options.counter + 1;
            }
        });
    },

    // Show a balloon if there are updates to the review you are viewing.
    fetch_new_comments: function() {
        var self = this;

        var req = $.ajax({
            url: self.options.json_url
        });

        req.success(function(data) {
            if (data.message_count > 0 && !self.options.noty && (self.options.last_pk != data.bundles[0].bundle_pk)) {
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
                                // self.options.noty = null;
                                // See site activity
                                self.options.last_pk = data.bundles[0].bundle_pk;
                                ScrollToLink.jump_to_link('review');
                                if ($('#events').is(':visible')) {
                                    $('#refresh_events').click();
                                } else {
                                    $('#activity_toggler').click();
                                }
                            }
                        }
                    });
                }
            } else {
                self.options.counter = self.options.counter + 1;
            }
        });
    }
});
