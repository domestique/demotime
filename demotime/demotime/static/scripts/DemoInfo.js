var DemoInfoModel = Backbone.Model.extend();
DemoTime.DemoInfo = Backbone.View.extend({
    el: 'body',

    events: {
        'click .jump-to-first-issue': 'focus_issue',
        'click .jump-to-comments': 'focus_comments',
        'click .editable': 'edit_in_place',
        'keydown .editable': 'typing',
        'blur .editable': 'save_change'
    },

    initialize: function(options) {
        this.options = options;
        this.render();
    },

    render: function(event) {
        var self = this;
        var review_req = $.ajax({
            url: self.options.review_search_url,
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
            html += '<span class="issue-unresolved jump-to-first-issue">' + this.model.get('active_issues_count') + ' unresolved issue(s)</span>';
        }
        if (this.model.get('resolved_issues_count')) {
            html += '<span class="issue-resolved jump-to-comments">' + this.model.get('resolved_issues_count') + ' resolved issue(s)</span>';
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
    },

    edit_in_place: function(event) {
        var title = $(event.target);
        title.attr('contenteditable', true);
        title.data('existing_title', title.html());
        document.execCommand('selectAll', false, null);
    },

    typing: function(event) {
        var element = $(event.target);
        if (event.keyCode == 13) event.preventDefault();
        if (element.html().length) {
            if (event.keyCode == 13) {
                this.save_change(event);
            } else if (event.keyCode == 27) {
                element.attr('contenteditable', false);
                element.html(element.data('existing_title'));
            }
        }
    },

    save_change: function(event) {
        var element = $(event.target),
            type = element.data('type'),
            self = this;

        $.ajax({
            method: 'post',
            url: self.options.review_info_url,
            data: {
                [type]: element.html().replace(/\&nbsp\;/g, '')
            },
            success: function(data) {
                element.attr('contenteditable', false);
            },
            error: function(data) {
                element.attr('contenteditable', false);
            }
        });
    }
});
