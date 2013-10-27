(function($) {
    $.aip.load_image = function(kargs) {
        var inner = function($img, src, timeout, reloads) {
            return $.aip.redo({
                make: function(depth) {
                    console.log((depth + 1) + 'th loading ' + src);
                    // for no reloading usage
                    if (depth > 0) {
                        // each cross means a reload
                        // mod 2 to force reload
                        var preview_src = src + '?x=' + ((depth + 2) % 2);
                    } else {
                        var preview_src = src;
                    }
                    var tid = setTimeout(function() {
                        reject('timeout');
                    }, timeout);
                    var $d = $.Deferred().done(function() {
                        clearTimeout(tid);
                    }).fail(function() {
                        clearTimeout(tid);
                    });
                    var rejected = false;
                    function reject(reason) {
                        rejected = true;
                        $d.reject(reason);
                    };
                    $img.attr('src', '');
                    $img.imagesLoaded().done(function() {
                        clearTimeout(tid);
                        if (!rejected) {
                            console.log('loaded: ' + preview_src);
                            $img.data('src', preview_src);
                            $d.resolve();
                        }
                    }).fail(function() {
                        clearTimeout(tid);
                        reject('unknown');
                    });
                    $img.attr('src', preview_src);
                    return $d.promise();
                },
                reloads: reloads
            });
        };
        var options = $.extend({
            timeout: 1e8,
            reloads: $.aip.range(0).map($.noop)
        }, kargs);
        if (!options.src.startswith('http://')) {
            return inner(options.img, options.src, options.timeout, options.reloads);
        }
        return $.Deferred().reject(options.src + ' not support ssl');
    };
})(jQuery);
