describe("ReviewActivity.js", function() {
    var is_phantom = function() {
        return navigator.userAgent.toLowerCase().indexOf('phantom') > -1;
    }
    beforeEach(function() {
        $('body').html('\
            <div id="activity_tester" class="main-content">\
                <div class="review">\
                    <div class="review_toggles">\
                        <a href="#" id="activity_toggler">Activity log</a>\
                    </div>\
                    <section class="review-overview events" id="events" style="display:none">\
                        <center><img src="/static/images/loading.gif"></center>\
                    </section>\
                </div>\
            </div>');

        comment_test_dom = $('#activity_tester');

        jQuery.fx.off = true;
        this.activity = new DemoTime.ReviewActivity();
        this.activity.scroller = new DemoTime.ScrollToLink();

        link = $('#activity_toggler');
        events = $('#events');
    });

    afterEach(function() {
        this.activity.$el.each(function() {
            $(this).unbind('click');
        });
    });

    it("should toggle the activity pane", function() {
        link.trigger('click');
        expect(events.is(':visible')).toBeTruthy();
        expect(link.hasClass('enabled')).toBeTruthy();
        link.trigger('click');
        expect(events.is(':visible')).toBeFalsy();
        expect(link.hasClass('enabled')).toBeFalsy();
    });

    it("should show a loading state", function() {
        link.trigger('click');
        this.activity.render();
        expect(events.html()).toContain('loading');
    });
});
