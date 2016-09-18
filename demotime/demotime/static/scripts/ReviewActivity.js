DemoTime.ReviewActivity = Backbone.View.extend({
    el: '.review',

    events: {
        'click #activity_toggler': 'toggle_activity_pane'
    },

    initialize: function(options) {
        this.options = options;
    },

    toggle_activity_pane: function(event) {
        var link = $(event.target),
            self = this;

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

    render: function() {
        var self = this;
        $.ajax({
            url: '/projects/' + self.options.project_slug + '/events/',
            method: 'GET',
            data: {
                review: self.options.review_pk
            }
        }).success(function(data) {
            var html = $('#events_pattern').html(),
                template = _.template(html);

            template = template({ moments: data.events });
            self.$el.find('#events').html(template);
        });
    }
});
