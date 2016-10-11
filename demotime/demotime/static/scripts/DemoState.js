DemoTime.DemoState = Backbone.View.extend({
    el: 'body',

    events: {
        'click .demo-changer': 'change_demo_state'
    },

    initialize: function(options) {
        this.options = options;
    },

    // Changing demo state
    change_demo_state: function(event) {
        var self = this,
            link = $(event.target),
            parent = link.parents('li'),
            state = link.data('state'),
            pk = link.data('pk'),
            creator = link.data('creator'),
            url = link.data('url');

        event.preventDefault();

        if (!state || !pk) return false;

        var req = $.ajax({
            url: url,
            method: 'POST',
            data: {
                review: pk,
                reviewer: creator,
                state: state
            }
        });

        req.success(function(msg) {
            if (msg.success) {
                parent.slideUp();
            }
        });
    }
});
