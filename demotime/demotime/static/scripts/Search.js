var SearchModel = Backbone.Model.extend();

DemoTime.Search = Backbone.View.extend({
    el: '.quickfind',

    events: {
        'keyup input': 'typing',
        'click .quickfind-heading': 'toggle'
    },

    initialize: function(options) {
        this.options = options;

        this.options.interval = 500;
    },

    typing: function(event) {
        var $input = $(event.target),
            self = this;

        clearTimeout(self.options.timer);
        self.options.timer = setTimeout(execute_search, this.options.interval);

        if (event.keyCode == 27) {
            $input.val('');
            self.$el.find('.quickfind-results').slideUp();
        }

        function execute_search() {
            if ($input.val().length > 1) {
                var user_req = $.ajax({
                    url: self.options.user_url,
                    method: 'POST',
                    data: {
                        action: 'search_users',
                        name: $input.val()
                    }
                });

                user_req.success(function(data) {
                    self.users = new SearchModel(data);

                    // Grab the container template
                    var html = $('#user_results').html(),
                        template = _.template(html);
                    template = template({ user: self.users.get('users') });

                    self.$el.find('.quickfind-users').html(template);
                    self.$el.find('.quickfind-results').slideDown();
                });

                var review_req = $.ajax({
                    url: self.options.review_url,
                    method: 'POST',
                    data: {
                        title: $input.val()
                    }
                });

                review_req.success(function(data) {
                    self.reviews = new SearchModel(data);
                    // Grab the container template
                    var html = $('#review_results').html(),
                        template = _.template(html);
                    template = template({ reviews: self.reviews.get('reviews') });

                    self.$el.find('.quickfind-reviews').html(template);
                    self.$el.find('.quickfind-results').slideDown();
                });

                var project_req = $.ajax({
                    url: self.options.project_url,
                    method: 'POST',
                    data: {
                        name: $input.val()
                    }
                });

                project_req.success(function(data) {
                    self.projects = new SearchModel(data);
                    // Grab the container template
                    var html = $('#project_results').html(),
                        template = _.template(html);
                    template = template({ projects: self.projects.get('projects') });

                    self.$el.find('.quickfind-projects').html(template);
                    self.$el.find('.quickfind-results').slideDown();
                });
            } else {
                if (self.$el.find('.quickfind-results').length) {
                    self.$el.find('.quickfind-results').slideUp();
                }
            }
        }
    },

    toggle: function() {
        var heading = $(event.target),
            list = heading.next('.quickfind-list')

        list.slideToggle(function() {
            if (list.is(':visible')) {
                heading.removeClass('icon-plus-squared-alt').addClass('icon-minus-squared-alt');
            } else {
                heading.removeClass('icon-minus-squared-alt').addClass('icon-plus-squared-alt');
            }
        });
    }
});
