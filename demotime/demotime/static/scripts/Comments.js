/** ajax-y comments */
DemoTime.Comments = Backbone.View.extend({
    el: '.comment_wrapper',

    events: {
        'click .collapser': 'collapse_comment',
        'click .expand_reply_link': 'expand_new_reply',
        'click .reply_and_approve': 'reply_and_approve',
        'click .new_comment_button': 'post_new_comment',
        'click .comment_edit': 'comment_edit',
        'click .attachment-add': 'attachment_add',
        'click .attachment-remove': 'attachment_remove',
        'click .attachment-delete': 'attachment_delete',
        'click .issue-new': 'change_issue',
        'click .issue-unresolved': 'change_issue'
    },

    initialize: function(options) {
        this.options = options || [];

        Mousetrap.bind('command+enter', function(e) {
            $(e.target).parents('.comment_form_container').find('.new_comment_button').click();
            return false;
        });
    },

    post_new_comment: function(event, also_approve) {
        var button = $(event.target),
            self = this,
            comment_parent = button.parents('.comment_parent'),
            thread = comment_parent.data('thread');

        // Saving container as an option for global use
        this.options.comment_form_container = button.parents('.comment_form_container');
        this.options.comment = comment_parent.find('.form-control').val();
        this.options.comment_form_container.find('input, button').prop('disabled', true);

        // Check for 'editing' data attr, otherwise it's a new comment
        if (this.options.comment_form_container.data('editing')) {
            // PATCH needs data jsonified
            var data = {
                comment_pk: self.options.comment_pk,
                comment: self.options.comment,
                thread: thread
            }
            var req = $.ajax({
                url: self.options.comments_url,
                method: 'PATCH',
                dataType: 'json',
                data: JSON.stringify(data)
            });
        } else { // new comment
            var formData = new FormData();
            if (thread) {
                formData.append('thread', thread);
            }
            formData.append('comment', self.options.comment);

            if (this.options.comment_form_container.find('#id_is_issue').prop('checked')) {
                formData.append('is_issue', true);
            }

            x = 0;
            comment_parent.find('.ajaxy_attachment').each(function() {
                var attachment_file = $(this).find('#id_' + x + '-attachment').get(0),
                    attachment_desc = $(this).find('#id_' + x + '-description').val();

                if (attachment_file) {
                    if (attachment_file.files[0]) {
                        formData.append(x + '-attachment', attachment_file.files[0]);
                        formData.append(x + '-description', attachment_desc);
                        formData.append('sort_order', x);
                    }
                }
                x++
            });

            var req = $.ajax({
                url: self.options.comments_url,
                method: 'POST',
                contentType: false,
                processData: false,
                data: formData
            });
        }

        req.always(function() {
            // Remove any errors
            comment_parent.find('.errorlist').remove();

            // Cancel loading state
            self.options.comment_form_container.find('input, button').prop('disabled', false);
        });

        req.success(function(data) {
            if (data.status == 'failure') {
                // Write the error message html
                self.show_errors(data.errors.comment);
            } else {
                // Slide up the editor if in a thread
                if (thread) {
                    self.options.comment_form_container.slideUp();
                } else {
                    comment_parent.find('.wysiwyg-editor').html('').focus();
                    self.options.comment_form_container.find('input[type="file"]').val('');
                    self.options.comment_form_container.find('select[name="attachment_type"]').val('');
                    self.options.comment_form_container.find('input[name="description"]').val('');
                }

                // Write the new comment HTML
                var html = self.get_success_html(data);

                // New comment DOM's a bit different than threaded DOM:
                if (self.options.top_level_comment) {
                    self.options.comment_form_container.parents('.comment_parent').prepend(html);
                } else if (thread) {
                    self.options.comment_form_container.parent().before(html);
                } else {
                    self.options.comment_form_container.before(html);
                }

                // Syntax highlighting
                comment_parent.find('pre').each(function(i, block) {
                    hljs.highlightBlock(block);
                });

                // Make urls clickable
                comment_parent.linkify({
                    target: "_blank"
                });

                // Clean up attachments
                comment_parent.find('.attachments').slideUp();
                comment_parent.find('.wysiwyg-editor').html('');
                comment_parent.find('input[type="file"]').val('');
                comment_parent.find('input[name="0-description"]').val('');
                comment_parent.find('#id_is_issue').prop('checked', false);

                // Remove all but the first attachment container
                comment_parent.find('.ajaxy_attachment').each(function() {
                    if ($(this).index() > 0) {
                        $(this).remove();
                    }
                });

                $('.temporary-attachments-preview').remove();

                // If reply and approve, trigger button click, otherwise
                // just scroll the new comment in to view.
                if (also_approve) {
                    $('a[data-type="approved"]').click();
                } else {
                    if (self.options.top_level_comment) {
                        $('html, body').animate({
                            scrollTop: comment_parent.offset().top - 75
                        }, 500);
                    } else {
                        $('html, body').animate({
                            scrollTop: comment_parent.find('.nested-reply').last().offset().top - 75
                        }, 500);
                    }

                    // Show 'new reply' link
                    if (self.options.trigger_link) {
                        self.options.trigger_link.show();
                    }
                    if (self.options.attachment_adder) {
                        self.options.attachment_adder.show();
                    }
                    if (self.options.issues_adder) {
                        self.options.issues_adder.show();
                    }
                }

                // Clean up
                self.options.comment_form_container.data('editing', false);
                self.options.top_level_comment = null;
                self.options.attachment_adder = null;
            }
        });

        req.error(function(data) {
            // Write the error message html
            if (data.statusText == 'error') {
                self.show_errors('Sorry, the server is not responding at this time.');
            } else {
                self.show_errors(data.statusText);
            }
        });
    },

    get_success_html: function(data) {
        if (data) {
            if (this.options.top_level_comment) {
                var html = '<div class="comment_parent" style="margin-top: 10px">';
            } else {
                var html = '<div class="comment_parent nested-reply">';
            }

            html += '<div class="demobox" id="' + data.comment.id + '">'
            html += '<div class="demobox-header">Your comment:</div>'
            html += '<div class="demobox-body"><div class="demobox-body-contents">' + this.options.comment + '</div></div>'

            if (data.comment.attachment_count && data.comment.attachments.length) {
                html += '<div class="demobox-body-attachments">';
                    for (var x = 0; x < data.comment.attachments.length; x++) {
                        html += '\
                            <div class="demobox attachment-card">\
                                <div class="demobox-header">';
                                    if (data.comment.attachments[x].description) {
                                        html += '<strong>' + data.comment.attachments[x].description + '</strong> - ';
                                    }
                                    html += '<a href="#" class="attachment-delete" data-comment="' + data.comment.id + '" data-attachment="' + data.comment.attachments[x].pk + '">delete</a>\
                                </div>\
                                <div class="demobox-body">';
                                    if (data.comment.attachments[x].attachment_type == 'image') {
                                        html += '<a href="' + data.comment.attachments[x].static_url + '" class="lightbox_img">\
                                                    <img src="' + data.comment.attachments[x].static_url + '" class="img-thumbnail">\
                                                 </a>';
                                    } else {
                                        html += '<em>Your <strong>' + data.comment.attachments[x].attachment_type + '</strong> was uploaded successfully.</em></p>';
                                    }
                                html += '</div>\
                            </div>';
                    }
                html += '</div>';
            }

            html += '<div class="demobox-footer">'
                html += '<div class="split by:2 align:m">'
                    html += '<div class="cel">'
                        html += '<a href="#" class="comment_edit" data-top-level="' + this.options.top_level_comment + '" data-comment="' + data.comment.id + '">edit</a>'
                    html += '</div>'
                    html += '<div class="cel" style="text-align: right">'
                        if (data.comment.issue.id) {
                            html += '<span class="issue-unresolved" data-pk="' + data.comment.id + '" data-resolve="true">unresolved</span>';
                        } else {
                            html += '<span class="issue-new" data-pk="' + data.comment.id + '">mark as issue</span>';
                        }
                    html += '</div>'
                html += '</div>'

            html += '</div>';

            return html;
        }
    },

    comment_edit: function(event) {
        var self = this,
            link = $(event.target),
            comment_parent = link.parents('.comment_parent'),
            comment = link.parents('.demobox');

        // Remove existing comment html

        // Grab comment html
        var edit_html = comment.find('.demobox-body-contents').html(),
            attachments = comment.find('.demobox-body-attachments').html();

        event.preventDefault();

        // Grab the 'Reply' link to re-show later (then hide, to reduce confusion)
        this.options.trigger_link = comment_parent.find('.expand_reply_link');
        this.options.trigger_link.hide();

        // Remove old comment and attachments
        comment.slideUp().remove();

        // Rename the button
        comment_parent.find('button.new_comment_button').html('Save');

        // Disable attachment editing (for now)
        this.options.attachments = comment_parent.find('.attachments').hide();
        this.options.attachment_adder = comment_parent.find('.toggle_sibling');
        this.options.attachment_adder.hide();

        // Don't allow checkbox for toggling issue state on ajaxy edit (should be done with button in comment)
        this.options.issues_adder = comment_parent.find('.issue-marker');
        this.options.issues_adder.hide();

        // Grab comment ID
        this.options.comment_pk = link.data('comment');
        // Determine if this is a top level comment (for indentation, scroll to)
        this.options.top_level_comment = link.data('top-level');

        // Set the form container
        this.options.comment_form_container = comment_parent.find('.comment_form_container');

        // Enable 'editing' mode
        this.options.comment_form_container.data('editing', true);

        // Re-show wysiwyg
        this.options.comment_form_container.slideDown(function() {
            self.options.comment_form_container.find('.wysiwyg-editor').html(edit_html);
            if (attachments) {
                self.options.comment_form_container.after('<div class="temporary-attachments-preview">' + attachments + '</div>');
            }
            self.options.comment_form_container.find('.wysiwyg-editor').focus();
            if ($(window).width() > 720) {
                $('html, body').animate({
                    scrollTop: self.options.comment_form_container.offset().top - 200
                }, 500);
            }
        });
    },

    show_errors: function(msg) {
        var self = this;
        this.options.comment_form_container.before('<ul class="errorlist"><li>' + msg + '</li></ul>');
        $('html, body').animate({
            scrollTop: self.options.comment_form_container.offset().top - 150
        }, 500);
    },

    // Leave a comment and approve at the same time
    reply_and_approve: function(event) {
        this.post_new_comment(event, true);
    },

    // Expand 'reply' wysiwyg on 'Leave a reply' click
    expand_new_reply: function(event) {
        event.preventDefault();

        this.options.trigger_link = $(event.target);

        var comment_form_container = this.options.trigger_link.next('.comment_form_container');

        // Show new comment container
        this.options.trigger_link.next('.comment_form_container').slideDown(function() {
            comment_form_container.find('.wysiwyg-editor').focus();
            if ($(window).width() > 720) {
                $('html, body').animate({
                    scrollTop: comment_form_container.offset().top - 200
                }, 500);
            }
        });
        this.options.trigger_link.hide();
    },

    attachment_add: function(event) {
        event.preventDefault();
        var attachment = $(event.target).parents('.ajaxy_attachment'),
            new_attachment = attachment[0].outerHTML;

        this.attachment_parent = attachment.parents('.ajaxy_attachments');

        attachment.after(new_attachment);
        this.reorder_attachments(event);
    },

    attachment_remove: function(event) {
        var self = this;
        event.preventDefault();

        this.attachment_parent = $(event.target).parents('.ajaxy_attachments');

        $(event.target).parents('.ajaxy_attachment').slideUp(function() {
            $(this).remove();
            self.reorder_attachments();
        });
    },

    reorder_attachments: function() {
        var attachment_list = this.attachment_parent.find('.ajaxy_attachment');

        for (var x=0; x < attachment_list.length; x++) {
            var attachment = attachment_list.eq(x);
            attachment.find('.attachment-file input').prop('id', 'id_' + x + '-attachment');
            attachment.find('.attachment-file input').attr('name', x + '-attachment');
            attachment.find('.attachment-desc input').prop('id', 'id_' + x + '-description');
            attachment.find('.attachment-desc input').attr('name', x + '-description');
            if (x == 9) {
                attachment.find('.attachment-add').remove();
            }
        }
    },

    attachment_delete: function(event) {
        var el = $(event.target),
            self = this;

        event.preventDefault();

        var attachments = [];

        attachments.push(el.data('attachment'));

        var data = {
            delete_attachments: attachments,
            comment_pk: el.data('comment')
        };

        var del = $.ajax({
            url: self.options.comments_url,
            method: 'PATCH',
            dataType: 'json',
            data: JSON.stringify(data)
        });

        del.success(function(msg) {
            el.parents('.attachment-card').slideUp(function() {
                $(this).remove();
                if (!$('.current_attachments .demobox').length) {
                    $('.current_attachments .attachments').html('No attachments found');
                }
            });
        });
    },

    change_issue: function(event) {
        var link = $(event.target),
            self = this;

        if (link.data('resolve')) {
            var data = {
                comment_pk: link.data('pk'),
                issue: {
                    resolve: true
                }
            }
        } else {
            var data = {
                comment_pk: link.data('pk'),
                issue: {
                    create: true
                }
            }
        }
        var req = $.ajax({
            url: self.options.comments_url,
            method: 'PATCH',
            dataType: 'json',
            data: JSON.stringify(data)
        });

        req.success(function(data) {
            if (link.data('resolve')) {
                link.data('resolve', false);
                link.toggleClass('issue-unresolved issue-new');
                link.html('mark as issue');
            } else {
                link.data('resolve', true);
                link.toggleClass('issue-new issue-unresolved');
                link.html('unresolved');
            }
            if (typeof demo_info !== 'undefined') {
                demo_info.render();
            }
        });
    }
});
