var SearchModel = Backbone.Model.extend();
DemoTime.Search= Backbone.View.extend({
    el: '.quickfind',

    events: {
        'keyup input': 'typing'
    },

    initialize: function(options) {
        this.options = options;
    },

    typing: function(event) {
        var $input = $(event.target),
            self = this;

        if (event.keyCode == 27) {
            $input.val('');
            self.$el.find('.quickfind-results').slideUp();
        }

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
        } else {
            this.$el.find('.quickfind-results').slideUp();
        }
    }
});
