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
        while (begin >= 0 && $a.eq(end).offset() && $a.eq(begin).visible(true)) --begin;
        ++begin;
        end = mid + 1;
        while (end < n && $a.eq(end).offset() && $a.eq(end).visible(true)) ++end;
        //$.aip.notice('(' + begin + ',' + end + ') take ' + (new Date().getTime() - start));
        // 6 columns at most
        return $a.slice(Math.max(0, begin - 6), Math.min(n, end + 6));
    };

    $.fn.old = function() {
        return $(this).each(function() {
            var $this = $(this);
            if ($this.hasClass('on') && $this.visible(true)) {
                $this.touch();
            }
        }).filter(function() {
            return $(this).elapsed() >= {{ config['AIP_FADEOUT_TIMEOUT'] }};
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

    var arts = {};

    $.aip.arts = function(kargs) {
        if ('$d' in kargs) {
            var $d = $.Deferred();
            kargs.$d.done(function(r) {
                arts = $.extend(arts, r);
                $d.resolve(r);
            }).fail($d.reject);
            return $d.promise();
        } else if ('md5' in kargs) {
            var seen = {};
            var unseen = [];
            $(kargs.md5).each(function(i, md5) {
                if (md5 in arts) {
                    seen[md5] = arts[md5];
                } else {
                    unseen.push(md5);
                }
            });
            var $d = $.Deferred();
            if (unseen.length) {
                $.aip.arts({'$d': $.get('/arts', {
                    q: JSON.stringify({ 'md5': unseen })
                }).then($.aip.jsonresult) }).done(function(r) {
                    $d.resolve($.extend(seen, r));
                }).fail($d.reject);
            } else {
                $d.resolve(seen);
            }
            return $d.promise();
        }
    };
})(jQuery);
