var ReviewerModel = Backbone.Model.extend();
// Dynamically add/remove reviewers
DemoTime.Reviewers = Backbone.View.extend({
    el: 'body',

    events: {
        'keyup #find_reviewer': 'typing',
        'click .new_reviewer_click': 'add',
        'click .reviewer_deleter': 'delete',
        'click .cancel': 'cancel'
    },

    initialize: function(options) {
        this.options = options;
    },

    cancel: function() {
        this.$el.find('#find_reviewer').val('');
    },

    typing: function(event) {
        var $input = $(event.target),
            self = this;

        if (event.keyCode == 27) {
            $input.val('');
        }

        if ($input.val().length > 2 && String.fromCharCode(event.keyCode).match(/[a-zA-Z]/i)) {
            var req = $.ajax({
                url: self.options.finder_url,
                method: 'POST',
                data: {
                    reviewer_name: $input.val()
                }
            });

            req.success(function(data) {
                self.people = new ReviewerModel(data);

                if (self.people.get('reviewers').length) {
                    // Grab the container template
                    var html = $('#new_reviewers').html(),
                        template = _.template(html);
                    template = template({ person: self.people.get('reviewers') });

                    swal ({
                        title: "Found matches",
                        text: template,
                        type: "success",
                        showConfirmButton: false,
                        showCancelButton: true,
                        html: true
                    });
                } else {
                    sweetAlert("Sorry...", "No matches found.", "error");
                    $input.val('');
                }
            });
        }
    },

    add: function(event) {
        var link = $(event.target),
            pk = link.data('pk'),
            self = this;

        event.preventDefault();

        var req = $.ajax({
            url: self.options.adder_url,
            method: 'POST',
            data: {
                reviewer_pk: pk
            }
        });

        req.always(function() {
            swal.close();
        });
        req.success(function(data) {
            self.person= new ReviewerModel(data);

            // Grab the container template
            var html = $('#added_reviewer').html(),
                template = _.template(html);
            template = template({ person: self.person });

            self.$el.find('.reviewers ul li:first-child').before(template);
            self.$el.find('.reviewers input').val('');
        });
        req.error(function(err) {
            swal ({
                title: 'Whoops',
                type: 'error',
                text: 'Your request was denied: ' + err,
                html: true
            });
        });
    },

    delete: function(event) {
        event.preventDefault();
        var $el = $(event.target),
            $li = $el.parents('li'),
            pk = $el.data('pk'),
            self = this;

        var req = $.ajax({
            url: self.options.deleter_url,
            method: 'POST',
            data: {
                reviewer_pk: pk
            }
        });

        req.success(function() {
            $li.slideUp();
        });

        req.error(function(err) {
            swal ({
                title: 'Whoops',
                type: 'error',
                text: 'Your request was denied: ' + err,
                html: true
            });
        });
    }
});
