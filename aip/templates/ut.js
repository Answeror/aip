(function($) {
    $.extend($.aip, {
        placehold: function(width, height) {
            return "{{ url_for('.static', filename='images/p.png') }}";
        },
        now: function() {
            return new Date().getTime() / 1000;
        },
        // http://stackoverflow.com/a/2117523/238472
        uuid: function() {
            return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
                return v.toString(16);
            });
        },
        error_guard: function(r) {
            return $.Deferred(function($d) {
                if (r && 'error' in r) {
                    $d.reject(r.error.message);
                } else {
                    $d.resolve(r);
                }
            });
        },
        range: function(n) {
            return Array.apply(0, Array(n)).map(function(e, i) { return i; });
        },
        actual_size: function($img, callback) {
            //callback($img[0].naturalWidth, $img[0].naturalHeight);
            // http://stackoverflow.com/questions/10478649/get-actual-image-size-after-resizing-it
            $("<img/>") // Make in memory copy of image to avoid css issues
                .attr("src", $img.attr("src"))
                .load(function() {
                    // Note: $(this).width() will not
                    // work for in memory images.
                    callback(this.width, this.height);
                });
        },
        disturb: function(x) {
            return x * (Math.random() + 0.5)
        },
        overflown: function($tag) {
            return $tag[0].scrollWidth >  $tag.innerWidth();
        },
        user_id: function() {
            var _user_id = $('#user-id');
            if (_user_id.length) {
                return _user_id.attr('value');
            } else {
                return undefined;
            }
        }
    });
})(jQuery);
