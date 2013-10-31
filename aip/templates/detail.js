(function($) {
    $.aip.init_detail = function($item) {
        $item.find('a.preview').click(function(e) {
            e.preventDefault();
            $.get(
                '/art/detail/part/' + $item.data('md5')
            ).then($.aip.jsonresult).done(function(r) {
                var $detail = $('.level-1');
                $detail.empty();
                $detail.html(r);
                $detail.find('.plus').plus_init();
                var $preview = $detail.find('div[name=preview]');
                var $img = $preview.find('img.detail');
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
                    $.get($img.data('src-template'), $.param({
                        width: Math.round($preview.width())
                    })).done(function(r) {
                        $.aip.load_image({
                            img: $img,
                            src: r.result,
                            timeout: 1e3 * {{ config['AIP_DETAIL_LOADING_TIMEOUT'] }},
                            reloads: $.aip.range({{ config['AIP_DETAIL_RELOAD_LIMIT'] }}).map(function() {
                                return $.aip.disturb(1e3 * {{ config['AIP_DETAIL_RELOAD_INTERVAL'] }});
                            })
                        }).done(function() {
                            $loading.hide();
                            $img.show();
                        }).fail(function() {
                            $.aip.notice('get detail of ' + $item.data('md5') + ' failed');
                        });
                    }).fail(function() {
                        $.aip.notice('get detail link of ' + $item.data('md5') + ' failed');
                    });
                });
                // smooth scrolling of detail page
                $detail.find('button[name=back]').click(function(e) {
                    $detail.stop().animate({
                        left: '100%'
                    }, 500, 'swing', function() {
                        window.location.hash = '#wall';
                        $detail.hide();
                    });
                    e.preventDefault();
                });
            }).fail(function(reason) {
                $.aip.notice('load art detail failed: ' + reason);
            });
        });
    };
})(jQuery);
