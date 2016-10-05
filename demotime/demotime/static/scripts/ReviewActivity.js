DemoTime.ReviewActivity = Backbone.View.extend({
    el: 'body',

    events: {
        'click #activity_toggler': 'toggle_activity_pane',
        'change #events_filter': 'render',
        'click #refresh_events': 'render'
    },

    initialize: function(options) {
        this.options = options;
        // If there's no toggler, just launch onload (dashboard)
        if (!$('#activity_toggler').length) {
            this.render();
        }
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
                ScrollToLink.jump_to_link('review');
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

        if ($('#events_filter').length) {
            self.options.project_slug = $('#events_filter').val();
        }

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

                // For over-arching activity, set the max-height intelligently
                if ($('.events_list').length && $(window).width() > 720) {
                    $('.events_list').css('max-height', $('#dashboard_left').height() - 65 + 'px');
                }
            });
        }
    }
});
