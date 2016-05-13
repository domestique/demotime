DemoTime.EditProject = Backbone.View.extend({
    el: '.project',

    events: {
        'click #add_member': 'add_member'
    },

    initalize: function() {
        this.render();
    },

    render: function() {
    },

    add_member: function(event) {
        event.preventDefault();

        var link = $(event.target),
            member_wrap = link.parents('.member');

        link.remove();
        member_wrap.next('.member').slideDown();
    }

})
