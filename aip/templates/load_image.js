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
                            $.aip.actual_size($img, function(width, height) {
                                console.log('sized(' + width + 'x' + height + '): ' + preview_src);
                                $img.attr('width', width);
                                $img.attr('height', height);
                                $img.data('preview-width', width);
                                $img.data('preview-height', height);
                                $d.resolve();
                            });
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
        if (!kargs.src.startswith('http://')) {
            return inner(kargs.img, kargs.src, kargs.timeout, kargs.reloads);
        }
        return $.Deferred().reject(kargs.src + ' not support ssl');
    };
})(jQuery);
