var DemoInfoModel = Backbone.Model.extend();
DemoTime.DemoInfo = Backbone.View.extend({
    el: '.review-meta',

    events: {
        'click .issue-unresolved': 'focus_issue',
        'click .issue-resolved': 'focus_comments'
    },

    initialize: function(options) {
        this.options = options;
        this.render();
    },

    render: function(event) {
        var self = this;
        var review_req = $.ajax({
            url: self.options.review_url,
            method: 'POST',
            data: {
                pk: self.options.review_pk
            }
        });
        review_req.success(function(data) {
            self.model = new DemoInfoModel(data.reviews[0]);
            self.show_issue_counts();
        });
    },

    show_issue_counts: function() {
        var html = '',
            issues_placeholder = this.$el.find('#issues_placeholder');

        if (this.model.get('active_issues_count')) {
            html += '<span class="issue-unresolved">' + this.model.get('active_issues_count') + ' unresolved issue(s)</span>';
        }
        if (this.model.get('resolved_issues_count')) {
            html += '<span class="issue-resolved">' + this.model.get('resolved_issues_count') + ' resolved issue(s)</span>';
        }
        if (this.model.get('active_issues_count') || this.model.get('resolved_issues_count')) {
            issues_placeholder.html(html);
            issues_placeholder.show();
        } else {
            issues_placeholder.hide();
        }
    },

    focus_issue: function() {
        ScrollTo($('#comments').find('.issue-unresolved').first().parents('.demobox'));
    },

    focus_comments: function() {
        ScrollTo($('#comments'));
    }
});
