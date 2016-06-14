DemoTime.Dashboard = Backbone.View.extend({
    el: 'body',

    events: {
        'change .new_demo_dropdown': 'create_demo',
        'click .new_demo_link': 'create_demo',
        'click .copy_link': 'copy_link'
    },

    // Create a demo
    create_demo: function(event) {
        event.preventDefault();

        var link = $(event.target),
            select = link.parents('.new_demo').find('.dd-selected-value');

        if (select.val()) {
            window.location.href = select.val();
        }
    },

    copy_link: function(event) {
        var n = noty({
            text: 'Copied to clipboard!',
            type: 'success',
            timeout: 1500,
            animation: {
                open: 'animated flipInX',
                close: 'animated flipOutX',
                easing: 'swing', // easing
                speed: 250 // opening & closing animation speed
            },
        });
    }
})

