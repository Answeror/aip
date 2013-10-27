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
            if ($a.eq(mid).offset().top < top) begin = mid + 1;
            else end = mid;
        }
        var mid = begin;
        while (begin >= 0 && $a.eq(begin).visible(true)) --begin;
        ++begin;
        end = mid + 1;
        while (end < n && $a.eq(end).visible(true)) ++end;
        //$.aip.notice('(' + begin + ',' + end + ') take ' + (new Date().getTime() - start));
        return $a.slice(begin, end);
    };
    $.fn.reset_fadeout_timer = function() {
        var $this = $(this);
        if ($this.data('tid')) {
            clearTimeout($this.data('tid'));
            $this.data('tid', null);
        }
        $this.data('tid', setTimeout(function() {
            if ($this.visible(true)) {
                $this.reset_fadeout_timer();
            } else {
                $this.find('img').each(function() {
                    var $img = $(this);
                    if ($img.attr('src') == $img.data('src')) {
                        $img.attr('src', $.aip.placehold($img.width(), $img.height()));
                    }
                    $this.hide();
                });
            }
        }, 1e3 * {{ config['AIP_FADEOUT_TIMEOUT'] }}));
    };
})(jQuery);
