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
        this.pasteHtmlAtCaret('<br/><pre>' + selectedText + '</pre><br/>');
    },

    pasteHtmlAtCaret: function(html) {
        var sel, range;
        if (window.getSelection) {
            // IE9 and non-IE
            sel = window.getSelection();
            if (sel.getRangeAt && sel.rangeCount) {
                range = sel.getRangeAt(0);
                range.deleteContents();

                // Range.createContextualFragment() would be useful here but is
                // only relatively recently standardized and is not supported in
                // some browsers (IE9, for one)
                var el = document.createElement("div");
                el.innerHTML = html;
                var frag = document.createDocumentFragment(), node, lastNode;
                while ( (node = el.firstChild) ) {
                    lastNode = frag.appendChild(node);
                }
                range.insertNode(frag);

                // Preserve the selection
                if (lastNode) {
                    range = range.cloneRange();
                    range.setStartAfter(lastNode);
                    range.collapse(true);
                    sel.removeAllRanges();
                    sel.addRange(range);
                }
            }
        } else if (document.selection && document.selection.type != "Control") {
            // IE < 9
            document.selection.createRange().pasteHTML(html);
        }
    }
});
