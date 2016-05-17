DemoTime.EditGroupsProjects = Backbone.View.extend({
    el: 'body',

    events: {
        'click #add_member': 'add_member',
        'click #add_group': 'add_group',
        'blur #id_name': 'create_slug'
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
    },

    add_group: function(event) {
        event.preventDefault();

        var link = $(event.target),
            group_wrap = link.parents('.group');

        link.remove();
        group_wrap.next('.group').slideDown();
    },

    create_slug: function(event) {
        var name = $(event.target);
        this.$el.find('#id_slug').val(name.val().replace(/ /g,'-').toLowerCase());
    }

})
