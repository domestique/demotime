DemoTime.FooterScripts = Backbone.View.extend({
    el: 'body',

    initialize: function() {
        // Initialize lightboxes
        this.$el.find('.lightboxed').fancybox();

        // Set focus on pageload
        this.$el.find('.content input[type="text"]:not(.find_person)').first().focus();

        // Animate buttons
        $('button, .button-link, input[type="submit"]').click(function() {
            $(this).addClass('animated pulse');
        });

        // Initialize tooltips
        $('.help').tooltipster();

        // Initialized button clicks
        $('button').click(function() {
            if ($(this).data('href')) {
                window.location.href = $(this).data('href');
            }
        });

        // Smooth scroll to links
        var ScrollToLink = new DemoTime.ScrollToLink();
    }
})

