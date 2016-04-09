var InfoModel = Backbone.Model.extend();
// Dynamically add/remove reviewers
DemoTime.Info = Backbone.View.extend({
    el: 'body',

    events: {
        'mouseover a': 'lookup',
        'mouseout a': 'destroy'
    },

    initialize: function(options) {
        this.options = options;
    },

    lookup: function(event) {
        var link = $(event.target),
            self = this;

        if (!link.data('pk')) { return false }

        var review_req = $.ajax({
            url: self.options.review_url,
            method: 'POST',
            data: {
                pk: link.data('pk')
            }
        });
        review_req.success(function(data) {
            console.log(data);
            self.review = new InfoModel(data);
            if (self.review.get('reviews').length) {
                console.log(self.review.get('reviews')[0]);
                // Grab the container template
                var html = $('#review_info').html(),
                    template = _.template(html);
                template = template({ review: self.review.get('reviews')[0] });

                link.tooltipster({
                    content: template,
                    contentAsHTML: true,
                    interactive: true,
                    delay: 500,
                    animation: 'grow',
                    position: 'left',
                    onlyOne: true,
                    minWidth: 500
                });
                link.tooltipster('show');
            }
        });
    },

    destroy: function(event) {
        /*this.$el.find('[data-tipster]').each(function() {
            $(this).tooltipster('hide');
            $(this).data('tipster', false);
        });*/
    }

});
