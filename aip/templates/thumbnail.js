(function($) {
    $.aip.thumbnail = function(kargs) {
        var options = $.extend({
            selector: 'img.preview'
        }, kargs);
        var $d = $.Deferred();
        var $item = options.$item;
        var $img = $item.find(options.selector);
        $.get($item.data('thumbnail-link'), $.param({
            width: Math.round($img.width())
        })).done(function(r) {
            $.aip.load_image({
                img: $img,
                src: r.result,
                timeout: 1e3 * {{ config['AIP_LOADING_TIMEOUT'] }},
                reloads: $.aip.range({{ config['AIP_RELOAD_LIMIT'] }}).map(function() {
                    return $.aip.disturb(1e3 * {{ config['AIP_RELOAD_INTERVAL'] }});
                })
            }).done($d.resolve).fail($d.reject);
        }).fail(function() {
            console.log('get thumbnail link of ' + $item.data('md5') + ' failed');
        });
        return $d;
    };
})(jQuery);
