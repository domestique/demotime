DemoTime.Dashboard = Backbone.View.extend({
    el: 'body',

    events: {
        'change .new_demo_dropdown': 'create_demo',
        'click .new_demo_link': 'create_demo'
    },

    // Create a demo
    create_demo: function(event) {
        event.preventDefault();

        var link = $(event.target),
            select = link.parents('.new_demo').find('.dd-selected-value');

        if (select.val()) {
            window.location.href = select.val();
        }
    }
})
