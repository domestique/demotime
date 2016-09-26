describe("Wysiwyg.js", function() {
    var is_phantom = function() {
        return navigator.userAgent.toLowerCase().indexOf('phantom') > -1;
    }
    beforeEach(function() {
        jasmine.clock().install();
        $('body').html('\
            <div id="wysiwyg_tester">\
            <textarea style="display:none"></textarea>\
            <script type="text/x-pattern" id="wysiwyg_footer">\
                <div class="footer_panel">\
                    <a href="#" class="toggle_html">edit source</a>\
                    <div class="emoji_panel" title="Click to insert a reaction">\
                        <img src="https://demoti.me/static/images/emoji/gif.png" class="add_gif emoji">\
                        <img src="https://demoti.me/static/images/emoji/smiley.png" class="add_emoji emoji">\
                        <img src="https://demoti.me/static/images/emoji/grin.png" class="add_emoji emoji">\
                        <img src="https://demoti.me/static/images/emoji/frowning2.png" class="add_emoji emoji">\
                        <img src="https://demoti.me/static/images/emoji/astonished.png" class="add_emoji emoji">\
                        <img src="https://demoti.me/static/images/emoji/confounded.png" class="add_emoji emoji">\
                        <img src="https://demoti.me/static/images/emoji/cry.png" class="add_emoji emoji">\
                        <img src="https://demoti.me/static/images/emoji/heart.png" class="add_emoji emoji">\
                        <img src="https://demoti.me/static/images/emoji/thumbsup.png" class="add_emoji emoji">\
                        <img src="https://demoti.me/static/images/emoji/beers.png" class="add_emoji emoji">\
                    </div>\
                </div>\
                <div class="giphy_input_panel" style="display: none">\
                    <input type="text" placeholder="Enter a keyword here" class="giphy_input">\
                </div>\
                <div class="giphy_results"></div>\
                <div class="giphy_branding">\
                    <img src="https://demoti.me/static/images/giphy.png" class="giphy_logo">\
                </div>\
            </script>\
            <script type="text/x-pattern" id="giphy_results">\
            <div>\
                <ul>\
                    <% _.each(gif, function(gif) { %>\
                        <li>\
                            <% if (gif) { %>\
                                <img data-full="<%= gif.images.original.url %>" src=\'<%= gif.images.fixed_height_small.url %>\' class="giphy_result_image">\
                            <% } %>\
                        </li>\
                    <% }); %>\
                </ul>\
            </div>\
        </script>\
        </div>');

        wysiwyg_test_dom = $('#wysiwyg_tester');

        jQuery.fx.off = true;
        this.wysiwyg = new DemoTime.Wysiwyg({
            'dt_url': 'http://www.example.com'
        });
    });

    afterEach(function() {
        jasmine.clock().uninstall();
        this.wysiwyg.$el.each(function() {
            $(this).unbind('click')
        });
    });

    it("should render the wysiwyg", function() {
        expect(this.wysiwyg.$el.is(':visible')).toBeTruthy();
    });

    it("should show the emoji panel", function() {
        jasmine.clock().tick(1500)
        expect(this.wysiwyg.$el.find('.emoji_panel').is(':visible')).toBeTruthy();
    });

    it("should add emoji", function() {
        jasmine.clock().tick(1500)
        this.wysiwyg.$el.find('.emoji_panel').find('.add_emoji').first().click();
        jasmine.clock().tick(500)
        expect(this.wysiwyg.$el.find('.wysiwyg-editor').html()).toContain('img');
    });

    it("should toggle the html pane", function() {
        jasmine.clock().tick(1500)
        this.wysiwyg.$el.find('.toggle_html').click();
        expect(this.wysiwyg.$el.find('textarea').is(':visible')).toBeTruthy();
        expect(this.wysiwyg.$el.find('.wysiwyg-editor').is(':visible')).toBeFalsy();
        this.wysiwyg.$el.find('.toggle_html').click();
        expect(this.wysiwyg.$el.find('textarea').is(':visible')).toBeFalsy();
        expect(this.wysiwyg.$el.find('.wysiwyg-editor').is(':visible')).toBeTruthy();
    });

    it("should be able to type a gif keyword", function() {
        jasmine.clock().tick(1500)
        this.wysiwyg.$el.find('.add_gif').click();
        expect(this.wysiwyg.$el.find('.giphy_input_panel').is(':visible')).toBeTruthy();
    });
});
