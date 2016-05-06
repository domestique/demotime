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
                pk: link.data('pk'),
                project_pk: link.data('prj') || null
            }
        });
        review_req.success(function(data) {
            self.review = new InfoModel(data);
            if (self.review.get('reviews').length) {
                // Grab the container template
                var html = $('#review_info').html(),
                    template = _.template(html);
                template = template({ review: self.review.get('reviews')[0] });

                link.tooltipster({
                    content: template,
                    contentAsHTML: true,
                    interactive: true,
                    animation: 'grow',
                    position: 'left',
                    onlyOne: true,
                    minWidth: 500
                });
                setTimeout(function() {
                    if (link.is(":hover")) {
                        link.tooltipster('show');
                    }
                }, 1000);
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
