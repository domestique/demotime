DemoTime.EditGroupsProjects = Backbone.View.extend({
    el: 'body',

    events: {
        'click #add_member': 'add_member',
        'click #add_group': 'add_group',
        'blur #id_name': 'create_slug',
        'click .toggle_admin': 'toggle_admin'
    },

    initalize: function() {
        this.render();
    },

    render: function() {
    },

    // A new member within the 'project admin' form
    add_member: function(event) {
        event.preventDefault();

        var link = $(event.target),
            member_wrap = link.parents('.member');

        link.remove();
        member_wrap.next('.member').slideDown();
    },

    // A new group within the 'project admin' form
    add_group: function(event) {
        event.preventDefault();

        var link = $(event.target),
            group_wrap = link.parents('.group');

        link.remove();
        group_wrap.next('.group').slideDown();
    },

    // auto-make slug on the 'new group/type' form
    create_slug: function(event) {
        var name = $(event.target);
        this.$el.find('#id_slug').val(name.val().replace(/ /g,'-').toLowerCase());
    },

    // toggle yes/no admin on 'edit admins' form
    toggle_admin: function(event) {
        var person = $(event.target);
        person.toggleClass('icon').toggleClass('icon-star');
        person.find('input').prop('checked', person.hasClass('icon-star'));
    }
})
