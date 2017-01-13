DemoTime.DemoState = Backbone.View.extend({
    el: 'body',

    events: {
        'click .demo-changer': 'change_demo_state'
    },

    initialize: function(options) {
        this.options = options;
    },

    change_demo_state: function(event) {
        var self = this;
        event.preventDefault();
        this.link = $(event.target);

        if (this.link.data('state') == 'cancelled') {
            swal({
                title: "Cancel this demo?",
                type: "warning",
                showCancelButton: true,
                confirmButtonColor: "#DD6B55",
                confirmButtonText: "Confirm",
                closeOnConfirm: false
            },
            function (isConfirm) {
                if (isConfirm) {
                    self.finish_change_demo_state();
                    swal.close();
                }
            });
        } else {
            self.finish_change_demo_state();
        }
    },

    // Changing demo state
    finish_change_demo_state: function() {
        var self = this,
            link = this.link,
            parent = link.parents('.demobox'),
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
