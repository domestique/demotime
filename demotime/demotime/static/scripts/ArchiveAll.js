// Archive All Messages
DemoTime.ArchiveAll = Backbone.View.extend({
    el: '#archive_all',

    events: {
        'click': 'archive'
    },

    initialize: function(options) {
        this.options = options;
    },

    archive: function(event) {
        var self = this,
            link = $(event.target),
            messages = link.parents('.dashboard').find('.messages-list');

        event.preventDefault();
        link.fadeOut();

        var req = $.ajax({
            url: self.options.url,
            method: 'post',
            data: {
                'mark_all_read': true,
                'action': 'read'
            }
        });

        req.done(function(msg) {
            console.log(msg);
            messages.slideUp(function() {
                messages.html('No unread messages.').slideDown();
                $('.msg_notifier').removeClass('unread_notification').addClass('read_notification').find('a').html(msg.message_count);
            });
        });
    }
});
