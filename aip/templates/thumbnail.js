(function($) {
    $.aip.thumbnail = function(kargs) {
        var options = $.extend({
            selector: 'img.preview'
        }, kargs);
        var $d = $.Deferred();
        var $img = options.$item.find(options.selector);
        $.aip.load_image({
            img: $img,
            src: $.param.querystring(
                options.$item.data('thumbnail'), $.param({
                    width: Math.round($img.width())
                })
            ),
            timeout: 1e3 * {{ config['AIP_LOADING_TIMEOUT'] }},
            reloads: $.aip.range({{ config['AIP_RELOAD_LIMIT'] }}).map(function() {
                return $.aip.disturb(1e3 * {{ config['AIP_RELOAD_INTERVAL'] }});
            })
        }).done($d.resolve).fail($d.reject);
        return $d;
    };
})(jQuery);
