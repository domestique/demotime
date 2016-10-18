DemoTime.ReviewActivity = Backbone.View.extend({
    el: 'body',

    events: {
        'click #activity_toggler': 'toggle_activity_pane',
        'click .comment_link': 'jump_to_comment',
        'change #events_filter': 'render',
        'click #refresh_events': 'render'
    },

    jump_to_comment: function(event) {
        this.hide_pane();
    },

    initialize: function(options) {
        this.options = options;
        // If there's no toggler, just launch onload (dashboard)
        if (!$('#activity_toggler').length) {
            this.render();
        }
    },

    toggle_activity_pane: function(event) {
        event.preventDefault();

        if ($('#events').is(':visible')) {
            this.hide_pane();
            ScrollToLink.jump_to_link('review');
        } else {
            this.show_pane();
        }
    },

    hide_pane: function() {
        var triggerer = $('#activity_toggler');

        this.$el.find('#events').slideUp('fast', function() {
            triggerer.trigger("sticky_kit:detach");
            triggerer.removeClass('enabled');
        });
    },

    show_pane: function() {
        var triggerer = $('#activity_toggler'),
            self = this;

        this.$el.find('#events').slideDown('fast', function() {
            triggerer.addClass('enabled');
            triggerer.stick_in_parent({
                'parent': '.main-content',
                'offset_top': 75,
                'recalc_every': 100,
            });
            self.render();
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

        self.options.exclusion_list = self.options.exclusion_list || '';

        if (self.options) {
            $.ajax({
                url: '/projects/' + self.options.project_slug + '/events/' + self.options.exclusion_list,
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

                $('.events').linkify({
                    target: "_blank"
                });

                // For over-arching activity, set the max-height intelligently
                if ($('.events').length && $(window).width() > 720) {
                    $('.events').css('max-height', $('#dashboard_left').height() - 80 + 'px');
                }
            });
        }
    }
});
