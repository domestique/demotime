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
                        <div class="comment_form_container" style="display:none">\
                            <textarea class="form-control">Things</textarea>\
                            <div class="wysiwyg-editor">Stuff</div>\
                            <div class="attachments ajaxy_attachments">\
                                <section class="ajaxy_attachment">\
                                    <div class="attachment-container split~680 by:3 with-gap:3">\
                                        <div class="attachment-file cel">\
                                            <label>Attach your file:</label>\
                                            <input class="form-control" id="id_0-attachment" name="0-attachment" type="file">\
                                        </div>\
                                        <div class="attachment-desc cel">\
                                            <label>Short description:</label>\
                                            <input class="form-control" id="id_0-description" maxlength="2048" name="0-description" type="text">\
                                        </div>\
                                        <div class="cel">\
                                            <label>&nbsp;</label>\
                                            <a href="#" class="attachment-add icon icon-plus-circled">add another</a>\
                                            <a href="#" class="attachment-remove icon icon-cancel-circled">remove</a>\
                                        </div>\
                                    </div>\
                                </section>\
                                <input id="id_thread" name="thread" value="" type="hidden">\
                            </div>\
                            <button class="new_comment_button"></button>\
                            <button class="reply_and_approve"></button>\
                        </div>\
                        <div class="nested-reply">\
                            <div class="demobox">\
                                <div class="demobox-header">\
                                    <a href="#" class="comment_edit"></a>\
                                </div>\
                                <div class="demobox-body">\
                                Hi there\
                                </div>\
                                <div class="attachments">\
                                    <div class="demobox"></div>\
                                </div>\
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
        expect(this.comments.options.comment_form_container).toBeTruthy();
    });

    it("should find comment form control", function() {
        $('.new_comment_button').click();
        expect(this.comments.options.comment).toBe('Things');
    });

    it("should start a loading state", function() {
        $('.new_comment_button').click();
        this.comments.start_loading_state();
        expect(this.comments.options.comment_form_container.find('button').prop('disabled')).toBeTruthy();
    });

    it("should end a loading state", function() {
        $('.new_comment_button').click();
        this.comments.start_loading_state();
        this.comments.end_loading_state();
        expect(this.comments.options.comment_form_container.find('button').prop('disabled')).toBeFalsy();
    });

    it("should be able to expand a new reply", function() {
        $('.comment_form_container').hide();
        $('.expand_reply_link').click();
        expect($('.comment_form_container').is(':visible')).toBeTruthy();
        expect($('.expand_reply_link').is(':visible')).toBeFalsy();
    });

    it("should show errors", function() {
        $('.new_comment_button').click();
        this.comments.show_errors();
        expect($('.errorlist').length).toBeTruthy();
    });

    it("should be able to edit comments", function() {
        $('.new_comment_button').click();
        $(this.comments.options.comment_form_container).hide();
        expect($('.nested-reply').is(':visible')).toBeTruthy();
        expect($('.attachments .demobox').length).toBeTruthy();
        $('.comment_edit').click();
        expect($('.demobox-body').is(':visible')).toBeFalsy();
        expect($('.attachments .demobox').length).toBeFalsy();
        expect(this.comments.options.comment_form_container.data('editing')).toBe(true);
        expect(this.comments.options.comment_form_container.is(':visible')).toBeTruthy();
    });

    it("should allow for additional attachments", function() {
        $('.attachment-add').click();
        expect($('.ajaxy_attachment').length > 1).toBeTruthy();
        $('.attachment-add').click();
        expect($('.ajaxy_attachment').length > 2).toBeTruthy();
    });

    it("should increment new attachments", function() {
        $('.attachment-add').click();
        expect($('input[name="1-description"]').length).toBeTruthy();
        $('.attachment-add').click();
        expect($('input[name="2-description"]').length).toBeTruthy();
    });

    it("should be able to remove new attachments", function() {
        $('.attachment-add').click();
        expect($('.ajaxy_attachment').length > 1).toBeTruthy();
        $('.attachment-remove').click();
        expect($('.ajaxy_attachment').length > 1).toBeFalsy();
    });

    it("should generate proper success html", function() {
        $('.new_comment_button').click();
        var html = this.comments.get_success_html({"comment": {"comment": "asdf", "thread": 426, "id": 801, "name": "Danny", "attachment_count": 1, "issue": [{"id": ''}], "attachments": [{"static_url": "/file/496", "attachment_type": "image", "description": ""}]}, "errors": "", "status": "success"});
        expect(html).toContain('nested-reply');
        expect(html).toContain('demobox');
        expect(html).toContain('attachment-card');
        expect(html).toContain('comment_edit');
    });

});
