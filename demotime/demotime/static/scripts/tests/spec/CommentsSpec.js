describe("Comments.js", function() {
    var is_phantom = function() {
        return navigator.userAgent.toLowerCase().indexOf('phantom') > -1;
    }
    beforeEach(function() {
        $('body').html('\
            <div id="comment_tester">\
                <h3 class="icon icon-comment collapser"></h3>\
                <div class="comment_wrapper">\
                    <div class="comment_parent collapser_parent">\
                        <label class="icon collapser icon-minus-squared-alt"></label>\
                        <a href="#" class="icon icon-comment expand_reply_link"></a>\
                        <div class="comment_container collapseable">\
                            <textarea class="form-control">Things</textarea>\
                            <div class="wysiwyg-editor">Stuff</div>\
                            <input type="file"></input>\
                            <select name="attachment_type"><option value="image">Image</option></select>\
                            <input name="attachment_description"></input>\
                            <button class="new_comment_button"></button>\
                            <button class="reply_and_approve"></button>\
                        </div>\
                        <div class="comments-reply">\
                            Hi there\
                            <a href="#" class="comment_edit"></a>\
                            <div class="attachments">\
                                <div class="summary">foo</div>\
                            </div>\
                        </div>\
                    </div>\
                </div>\
            </div>');

        comment_test_dom = $('#comment_tester');

        jQuery.fx.off = true;
        this.comments = new DemoTime.Comments();
    });

    afterEach(function() {
        this.comments.$el.each(function() {
            $(this).unbind('click')
        });
    });

    it("should find comments container", function() {
        $('.new_comment_button').click();
        expect(this.comments.options.container).toBeTruthy();
    });

    it("should find comment form control", function() {
        $('.new_comment_button').click();
        expect(this.comments.options.comment).toBe('Things');
    });

    it("should start a loading state", function() {
        $('.new_comment_button').click();
        this.comments.start_loading_state();
        expect(this.comments.options.container.find('button').prop('disabled')).toBeTruthy();
    });

    it("should end a loading state", function() {
        $('.new_comment_button').click();
        this.comments.start_loading_state();
        this.comments.end_loading_state();
        expect(this.comments.options.container.find('button').prop('disabled')).toBeFalsy();
    });

    it("should be collapseable/expandable", function() {
        $('.collapser').click();
        expect($('.collapseable').is(':visible')).toBeFalsy();
        expect($('.collapser').hasClass('.icon-minus-squared-alt')).toBeFalsy();
        $('.collapser').click();
        expect($('.collapseable').is(':visible')).toBeTruthy();
        expect($('.collapser').hasClass('.icon-plus-squared-alt')).toBeFalsy();
    });

    it("should be able to expand a new reply", function() {
        $('.comment_container').hide();
        expect($('.wysiwyg-editor').html()).toBeTruthy();
        $('.expand_reply_link').click();
        expect($('.comment_container').is(':visible')).toBeTruthy();
        expect($('.wysiwyg-editor').html()).toBeFalsy();
        expect($('.expand_reply_link').is(':visible')).toBeFalsy();
    });

    it("should show errors", function() {
        $('.new_comment_button').click();
        this.comments.show_errors();
        expect($('.errorlist').length).toBeTruthy();
    });

    it("should be able to edit comments", function() {
        $('.new_comment_button').click();
        $(this.comments.options.container).hide();
        expect($('.comments-reply').is(':visible')).toBeTruthy();
        expect($('.attachments .summary').length).toBeTruthy();
        $('.comment_edit').click();
        expect($('.comments-reply').is(':visible')).toBeFalsy();
        expect($('.attachments .summary').length).toBeFalsy();
        expect(this.comments.options.container.data('editing')).toBe(true);
        expect(this.comments.options.container.is(':visible')).toBeTruthy();
    });

    it("should generate proper success html", function() {
        $('.new_comment_button').click();
        var html = this.comments.get_success_html({"comment": {"comment": "asdf", "thread": 426, "id": 801, "name": "Danny", "attachment_count": 1, "attachments": [{"static_url": "/file/496", "attachment_type": "image", "description": ""}]}, "errors": "", "status": "success"});
        expect(html).toContain('comments-reply');
        expect(html).toContain('blockquote');
        expect(html).toContain('attachment-card');
        expect(html).toContain('comment_edit');
    });

});
