(function($) {
    $.aip.thumbnail = function(kargs) {
        var options = $.extend({
            selector: 'img.preview'
        }, kargs);
        var $d = $.Deferred();
        var $item = options.$item;
        var $img = $item.find(options.selector);
        var load = function(src) {
            $.aip.load_image({
                img: $img,
                src: src,
                timeout: 1e3 * {{ config['AIP_LOADING_TIMEOUT'] }},
                reloads: $.aip.range({{ config['AIP_RELOAD_LIMIT'] }}).map(function() {
                    return $.aip.disturb(1e3 * {{ config['AIP_RELOAD_INTERVAL'] }});
                })
            }).done($d.resolve).fail($d.reject);
        };
        // use actual width as param
        var p = $.param({ width: Math.round($img.width()) });
        // try hotlink first
        if ($item.data('thumbnail-link')) {
            $.get($item.data('thumbnail-link'), p).done(function(r) {
                load(r.result);
            }).fail(function() {
                console.log('get thumbnail link of ' + $item.data('md5') + ' failed');
            });
        } else {
            load($.param.querystring($item.data('thumbnail'), p));
        }
        return $d;
    };
})(jQuery);
