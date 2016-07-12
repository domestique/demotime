describe("Account.js", function() {
    var html;
    beforeEach(function() {
        $('body').html('<div class="manage_user">\
            <a href="#" class="manage_user-toggler"></a>\
            <ul style="display:none">\
                <li><a class="manage_user-item" href="#"></a></li>\
            </ul>\
        </div>');
        jQuery.fx.off = true;
        var account = new DemoTime.Account();
    });


    it("should render", function() {
        expect($('.manage_user')).toBeDefined();
    });

    it("should toggle onclick", function() {
        expect($('.manage_user ul').is(':visible')).toBe(false);
        $('.manage_user-toggler').click();
        expect($('.manage_user ul').is(':visible')).toBe(true);
        $('.manage_user-toggler').click();
        expect($('.manage_user ul').is(':visible')).toBe(false);
    });

    it("should close menu on item click", function() {
        expect($('.manage_user ul').is(':visible')).toBe(false);
        $('.manage_user-toggler').click();
        expect($('.manage_user ul').is(':visible')).toBe(true);
        $('.manage_user-item').click();
        expect($('.manage_user ul').is(':visible')).toBe(false);
    });
});
