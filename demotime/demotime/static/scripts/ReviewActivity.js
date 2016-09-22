DemoTime.ReviewActivity = Backbone.View.extend({
    el: '.review',

    events: {
        'click #activity_toggler': 'toggle_activity_pane',
        'click .reply_to_thread': 'toggle_activity_pane',
        'click #refresh_events': 'render'
    },

    initialize: function(options) {
        this.options = options;
    },

    toggle_activity_pane: function(event) {
        var self = this,
            link = $('#activity_toggler'),
            trigger = $(event.target);

        event.preventDefault();

        this.$el.find('#events').slideToggle(function() {
            if ($(this).is(':visible')) {
                link.addClass('enabled');
                link.stick_in_parent({
                    'parent': '.main-content',
                    'offset_top': 75,
                    'recalc_every': 100,
                });
                self.render();
            } else {
                link.trigger("sticky_kit:detach");
                link.removeClass('enabled');
                // Check to see if the trigger was the Toggler button or
                // a reply link. Scroll to top if the former, trigger reply
                // if the latter
                if (trigger.data('thread')) {
                    // Get the thread ID from the clicked Reply link
                    thread_id = $(event.target).data('thread');
                    // Traverse the DOM to get the page's thread
                    reply_link = self.$el.find('[data-thread=' + thread_id +']').find('.expand_reply_link');
                    reply_link.click();
                } else {
                    ScrollToLink.jump_to_link('review');
                }
            }
        });
    },

    render: function(event) {
        var self = this,
            container = $('#events');

        if (event) {
            event.preventDefault();
        }

        container.html('<center><img src="/static/images/loading.gif"></center>');

        if (self.options) {
            $.ajax({
                url: '/projects/' + self.options.project_slug + '/events/',
                method: 'GET',
                data: {
                    review: self.options.review_pk
                }
            }).success(function(data) {
                var html = $('#events_pattern').html(),
                    template = _.template(html);

                if (data.events.length) {
                    template = template({ moments: data.events });
                } else {
                    template = "No events to show";
                }

                container.html(template);
            });
        }
    }
});
