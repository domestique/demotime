var SearchModel = Backbone.Model.extend();
// Dynamically add/remove reviewers
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

        if ($input.val().length > 1 && String.fromCharCode(event.keyCode).match(/[a-zA-Z]/i)) {
            var reviewer_req = $.ajax({
                url: self.options.reviewer_url,
                method: 'POST',
                data: {
                    reviewer_name: $input.val()
                }
            });

            reviewer_req.success(function(data) {
                self.reviewers = new SearchModel(data);

                if (self.reviewers.get('reviewers').length) {
                    // Grab the container template
                    var html = $('#reviewer_results').html(),
                        template = _.template(html);
                    template = template({ user: self.reviewers.get('reviewers') });


                    self.$el.find('.quickfind-users').html(template);
                    self.$el.find('.quickfind-results').slideDown();
                } else {
                    self.$el.find('.quickfind-users').html('');
                }
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
                if (self.reviews.get('reviews').length) {
                    // Grab the container template
                    var html = $('#review_results').html(),
                        template = _.template(html);
                    template = template({ reviews: self.reviews.get('reviews') });

                    self.$el.find('.quickfind-reviews').html(template);
                    self.$el.find('.quickfind-results').slideDown();
                } else {
                    self.$el.find('.quickfind-reviews').html('');
                }
            });
        } else if (!$input.val().length) {
            this.$el.find('.quickfind-results').slideUp();
        }
    }
});
