(function($) {
    $.fn.inviewport = function(selector) {
        //var start = new Date().getTime();
        if (selector) {
            var $a = $(this).eq(0).find(selector);
        } else {
            var $a = $(this);
        }
        var n = $a.length;
        var begin = 0;
        var end = n;
        var top = $(window).scrollTop();
        while (begin < end) {
            var mid = Math.floor((begin + end) / 2);
            var $t = $a.eq(mid);
            if ($t.offset().top + $t.height() < top) begin = mid + 1;
            else end = mid;
        }
        var mid = begin;
        while (begin >= 0 && $a.eq(begin).visible(true)) --begin;
        ++begin;
        end = mid + 1;
        while (end < n && $a.eq(end).visible(true)) ++end;
        //$.aip.notice('(' + begin + ',' + end + ') take ' + (new Date().getTime() - start));
        // 6 columns at most
        return $a.slice(Math.max(0, begin - 6), Math.min(n, end + 6));
    };

    $.fn.old = function() {
        return $(this).each(function() {
            var $this = $(this);
            if ($this.visible(true)) {
                $this.touch();
            }
        }).filter(function() {
            return $(this).elapsed() >= {{ config['AIP_PULLING_INTERVAL'] }};
        });
    };
    $.fn.vacuum = function() {
        $(this).removeClass('on').addClass('off').empty();
    };

    $.fn.touch = function() {
        $(this).data('touch', $.aip.now());
    };
    $.fn.elapsed = function() {
        return $.aip.now() - $(this).data('touch');
    };
})(jQuery);
