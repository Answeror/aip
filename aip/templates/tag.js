(function($) {
    $.aip.init_tags = function($item) {
        // sticky popover
        // http://stackoverflow.com/a/9400740/238472
        var timer = null;
        var clicked = false;
        $item.find('.btn[name="tags"]').popover({
            container: 'body',
            html: true,
            trigger: 'manual',
            content: function() {
                return $(this).closest('.item').find('.tags').html();
            },
            placement: function(context, source) {
                var $s = $(source);
                var p = $s.offset();
                p.right = ($(window).width() - (p.left + $s.outerWidth()));
                if (p.right > 276) return 'right';
                if (p.left > 276) return 'left';
                if (p.top > 110) return 'top';
                return 'bottom';
            },
            template: '<div class="popover" onmouseover="$(this).mouseleave(function() { $(this).hide(); });"><div class="arrow"></div><div class="popover-inner"><h3 class="popover-title"></h3><div class="popover-content"><p></p></div></div></div>'

        }).click(function(e) {
            if (clicked) {
                $('.popover').hide();
                clicked = false;
            } else {
                // click listener for tablet
                if (timer) {
                    // prevent popup flash
                    clearTimeout(timer);
                    timer = null;
                } else {
                    $('.popover').hide();
                    $(this).popover('show');
                }
                clicked = true;
            }
            e.preventDefault();
        }).mouseenter(function(e) {
            $('.popover').hide();
            var $this = $(this);
            $this.popover('show');
            timer = setTimeout(function(){
                if (!$('.popover:hover').length && !$this.is(':hover')) {
                    $this.popover('hide');
                }
                // make further click take effect
                timer = null;
            }, 1000);
        });
    };
})(jQuery);
