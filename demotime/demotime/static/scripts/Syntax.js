/** syntax highlighting */
DemoTime.Syntax = Backbone.View.extend({

    el: '.wysiwyg-toolbar',

    events: {
        'click .syntax': 'clicked'
    },

    initialize: function() {
        this.$el.append('<a class="wysiwyg-toolbar-icon syntax" href="#">&lt;pre /&gt;</a>');
    },

    clicked: function(event) {
        event.preventDefault();

        var link = $(event.target),
            wysiwyg = link.parents('.wysiwyg-container'),
            editor = wysiwyg.find('.wysiwyg-editor');

        var selectedText = window.getSelection().toString();

        function replaceSelectedText(replacementText) {
            var sel, range;
            replacementText = ''
            if (window.getSelection) {
                sel = window.getSelection();
                if (sel.rangeCount) {
                    range = sel.getRangeAt(0);
                    range.deleteContents();
                    range.insertNode(document.createTextNode(replacementText));
                }
            } else if (document.selection && document.selection.createRange) {
                range = document.selection.createRange();
                range.text = replacementText;
            }
        }

        replaceSelectedText();
        editor.append('<pre>' + selectedText + '</pre>');
    }
});
