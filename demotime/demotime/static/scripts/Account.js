DemoTime.Account = Backbone.View.extend({
    el: '.manage_user',

    events: {
        'click .manage_user-item': 'clicked',
        'click .manage_user-toggler': 'toggle'
    },

    initialize: function() {
        this.render();
    },

    render: function() {
        var self = this;

        this.$body = this.$el.parents('body');

        this.$body.find('main, .subnav').click(function() {
            self.$el.find('ul').slideUp();
        });
    },

    toggle: function(event) {
        event.preventDefault();
        this.$el.find('ul').slideToggle();
    },

    clicked: function(event) {
        this.$el.find('ul').slideUp();
    }
});
