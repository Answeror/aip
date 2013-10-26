(function($) {
    $.aip.init_detail = function($item) {
        $item.find('a.preview').click(function(e) {
            var $detail = $('#detail');
            var $preview = $detail.find('div[name=preview]');
            var $img = $preview.find('img');
            var $loading = $detail.find('.loading');
            $img.hide();
            // must hide loading first
            // other wise detail layer won't show properly
            $loading.hide();
            $detail.show();
            $detail.stop().animate({
                left: '0%'
            }, 500, 'swing', function() {
                var hash = '#' + $item.data('md5');
                window.location.hash = hash;

                $loading.show();
                // load image after animation
                // to archive smooth transition on ipad
                $.aip.load_image({
                    img: $img,
                    src: $.param.querystring(
                        $item.data('thumbnail'), $.param({
                            width: Math.round($preview.width())
                        })
                    ),
                    timeout: 1e3 * {{ config['AIP_DETAIL_LOADING_TIMEOUT'] }},
                    reloads: $.aip.range({{ config['AIP_DETAIL_RELOAD_LIMIT'] }}).map(function() {
                        return $.aip.disturb(1e3 * {{ config['AIP_DETAIL_RELOAD_INTERVAL'] }});
                    })
                }).done(function() {
                    $loading.hide();
                    $img.show();
                });
                $detail.find('[name="source"]').attr('href', $item.data('source'));
                $detail.find('[name="raw"]').attr('href', '/raw/' + $item.data('md5'));
            });
            e.preventDefault();
        });
    };

    // smooth scrolling of detail page
    $(function() {
        $('#detail button[name=back]').click(function(e) {
            $('#detail').stop().animate({
                left: '100%'
            }, 500, 'swing', function() {
                window.location.hash = '#wall';
                $('#detail').hide();
            });
            e.preventDefault();
        });
    });
})(jQuery);
