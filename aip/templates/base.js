(function() {
    $.aip.inc = function(name, value) {
        var $t = $('#loading li[name="' + name + '"]');
        if (value == undefined) value = 1;
        $t.text(parseInt($t.text()) + value);
    };
    $.aip.error = function(message) {
        console.log(message);
        $('#alert_box').html('<div class="alert"><a class="close" data-dismiss="alert">×</a><span>'+message+'</span></div>');
    };
    $.aip.warning = $.aip.error;
    $.aip.init = function(kargs) {
        defaults = {
            makePageData: $.noop
        };
        kargs = $.extend({}, defaults, kargs);
        var $container = $('#items');
        var page = 0;
        function progress(p) {
            $('#bar').width(p + '%');
        };
        var marsed = false;
        var $buffer = $('#buffer');
        var nomore = false;
        function pull() {
            if ($.aip.pulling) return;
            if (nomore) return;
            $.aip.pulling = true;
            $this = $(this);
            progress(0);
            $('#loading').show();
            $buffer.empty();
            var data = kargs.makePageData(page);
            if ($.aip.user_id()) {
                data.user_id = $.aip.user_id();
            }
            $.get(
                kargs.makePageUrl(page),
                data
            ).done(function(data) {
                var $items = $(data).find('.item');
                var n = $items.length;
                var cleanup = function() {
                    $('#loading').hide();
                    $('#alert_box').html('');
                    page += 1;
                    $.aip.pulling = false;
                    if (n) {
                        $.waypoints('refresh');
                        if ($container.outerHeight() <= $.waypoints('viewportHeight')) pull();
                    }
                };
                if (!n) {
                    cleanup();
                    nomore = true;
                    return;
                }
                $.aip.inc('in-json', n);
                $items.each(function() {
                    $(this).attr('data-done', false);
                });
                $buffer.append($items);
                var loaded = 0;
                // no exception
                var doneone = function($item) {
                    ++loaded;
                    progress(100 * loaded / n);
                    if (loaded == n) {
                        cleanup();
                    } else if (loaded > n) {
                        throw 'loaded(' + loaded + ') > n(' + n + ')';
                    }
                };
                var guarded_doneone = function($item) {
                    if ($item.attr('data-done') == 'false') {
                        doneone($item);
                        $item.attr('data-done', true);
                    }
                };
                var mars = function($item) {
                    $container.append($item);
                    if (!marsed) {
                        console.log('initialize masonry');
                        $container.masonry({
                            itemSelector: '.item',
                            isAnimated: true,
                            columnWidth: '.span2',
                            transitionDuration: '0.4s'
                        });
                        marsed = true;
                    } else {
                        $container.masonry('appended', $item, true);
                    }
                };
                var dealone = function($item) {
                    if ($item.data('dealed')) return;
                    try {
                        $.aip.init_plus($item);
                        $.aip.init_tags($item);
                        $.aip.init_detail($item);
                        mars($item);
                        $.aip.inc('done');
                    } catch (e) {
                        console.log('dealone failed');
                        console.log(e);
                        console.trace();
                    } finally {
                        $item.data('dealed', true);
                        guarded_doneone($item);
                    }
                };
                var thumbnail = function($item) {
                    $.aip.inc('need-proxied');
                    var error = function(message) {
                        $.aip.error(message);
                        guarded_doneone($item);
                    };
                    var $img = $item.find('img.preview');
                    $.aip.load_image({
                        img: $img,
                        src: $.param.querystring(
                            $item.data('thumbnail'), $.param({
                                width: Math.round($img.width())
                            })
                        ),
                        timeout: 1e3 * {{ config['AIP_LOADING_TIMEOUT'] }},
                        reloads: $.aip.range({{ config['AIP_RELOAD_LIMIT'] }}).map(function() {
                            return $.aip.disturb(1e3 * {{ config['AIP_RELOAD_INTERVAL'] }});
                        })
                    }).done(function() {
                        $.aip.inc('proxied');
                        $item.find('.loading').hide();
                        $img.show();
                        dealone($item);
                    }).fail(function(reason) {
                        error('load image failed, reason: ' + JSON.stringify(reason));
                        $.aip.inc('proxied-preview-loading-failed');
                    });
                };
                $items.each(function() {
                    var $this = $(this);
                    var $img = $this.find('img.preview');
                    var done = function() {
                        console.log($img.attr('src') + 'loaded');
                        $this.find('.loading').hide();
                        $img.show();
                        $.aip.super_resolution($img, function() {
                            thumbnail($this);
                        }, function() {
                            dealone($this);
                        });
                    };
                    var fail = function(reason) {
                        console.log('load image failed, reason: ' + reason);
                        $.aip.inc('original-preview-loading-failed');
                        thumbnail($this);
                    };
                    $.aip.load_image({
                        img: $img,
                        src: $img.data('src'),
                        timeout: 1e3 * {{ config['AIP_LOADING_TIMEOUT'] }},
                        reloads: $.aip.range({{ config['AIP_RELOAD_LIMIT'] }}).map(function() {
                            return $.aip.disturb({{ config['AIP_RELOAD_INTERVAL'] }});
                        })
                    }).done(done).fail(fail);
                });
            }).fail(function(reason) {
                $('#loading').hide();
                $.aip.warning('load more failed, reason: ' + JSON.stringify(reason));
            });
        };
        $(pull);
        $('.level-wall').on('resize scrollstop', function() {
            if ($('.bottom-anchor').visible(true)) pull();
        });
        $.aip.inited = true;
    };
    $.aip.is = function(kargs) {
        console.log('init');
        $.aip.init(kargs);
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
})();
