(function($) {
    $.fn.preview_area = function() {
        return $(this).data('preview-width') * $(this).data('preview-height');
    };
    $.fn.viewport_area = function() {
        return $(this).width() * $(this).height();
    };
    $.aip.super_resolution = function($img, callback, otherwise) {
        $.aip.actual_size($img, function(width, height) {
            console.log('sized(' + width + 'x' + height + '): ' + $img.attr('src'));
            $img.data('preview-width', width);
            $img.data('preview-height', height);
            var r = {{ config['AIP_RESOLUTION_LEVEL'] }};
            var aa = $img.preview_area();
            var va = $img.viewport_area();
            var need = aa * r < va;
            console.log('super resolution ' + aa + ' x ' + r + ' < ' + va + ' -> ' + need);
            if (need) {
                callback();
            } else {
                otherwise();
            }
        });
    };
})(jQuery);
