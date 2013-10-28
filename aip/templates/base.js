(function($) {
    $(function() {
        $.aip.wall = (function() {
            var inc = function(name, value) {
                var $t = $('#loading li[name="' + name + '"]');
                if (value == undefined) value = 1;
                $t.text(parseInt($t.text()) + value);
            };
            var options = {
                makePageData: $.noop,
                pulling_threshold: {{ config['AIP_PULLING_THRESHOLD'] }}
            };
            var $container = $('#items');
            var page = 0;
            function progress(p) {
                $('#bar').width(p + '%');
            };
            var $items = null;
            var marsed = false;
            var mars = function($item) {
                var $old = $container.find('.item[data-md5="' + $item.data('md5') + '"]');
                if ($old.length) {
                    //$old.replaceWith($item);
                    $item.insertAfter($old);
                    $item.attr('style', $old.attr('style'));
                    $old.remove();
                } else {
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
                }
                $items = $container.find('.item');
            };
            var $buf = $('#buffer');
            var nomore = false;
            var pulling = false;
            var rest = function() {
                return $buf.find('.item').length;
            };
            var enough = function() {
                return rest() >= options.pulling_threshold;
            };
            var dealone = function($item) {
                if ($item.data('dealed')) return;
                try {
                    $.aip.init_plus($item);
                    $.aip.init_tags($item);
                    $.aip.init_detail($item);
                    mars($item);
                    $item.reset_fadeout_timer();
                    inc('done');
                } catch (e) {
                    console.log('dealone failed');
                    console.log(e);
                    console.trace();
                } finally {
                    $item.data('dealed', true);
                }
            };
            var thumbnail = function($item) {
                var error = function(message) {
                    console.log(message);
                };
                $.aip.thumbnail({
                    '$item': $item
                }).done(function() {
                    inc('proxied');
                    $item.find('.loading').hide();
                    $item.find('img.preview').show();
                    dealone($item);
                }).fail(function(reason) {
                    error('load image failed, reason: ' + JSON.stringify(reason));
                    inc('proxied-preview-loading-failed');
                });
            };
            var init_img = function($img) {
                $img.attr('width', $img.width());
                $img.attr('height', $img.width() / $img.data('ratio'));
            };
            var load_one = function($this) {
                var $img = $this.find('img.preview');
                init_img($img);
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
                    inc('original-preview-loading-failed');
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
            };
            var pull = function() {
                if (nomore) return;
                if (pulling) return;
                if (enough()) {
                    console.log('enough (' + rest() + '), pulling cancel');
                    return;
                } else {
                    $.aip.notice('not enough (' + rest() + '), pulling start');
                }
                pulling = true;
                $this = $(this);
                progress(0);
                $buf.empty();
                var data = options.makePageData(page);
                if ($.aip.user_id()) {
                    data.user_id = $.aip.user_id();
                }
                $.get(
                    options.makePageUrl(page),
                    data
                ).done(function(data) {
                    pulling = false;
                    page += 1;
                    var $items = $(data).find('.item');
                    var n = $items.length;
                    if (!n) {
                        nomore = true;
                        return;
                    }
                    inc('in-json', n);
                    $buf.append($items);
                    $items.each(function() { load_one($(this)); });
                }).fail(function(reason) {
                    $.aip.notice('load more failed, reason: ' + JSON.stringify(reason));
                });
            };
            return {
                init: function(kargs) {
                    console.log('init wall');
                    options = $.extend(options, kargs);

                    setInterval(function() {
                        if ($('.bottom-anchor').visible(true)) pull();
                    }, 1e3 * {{ config['AIP_PULLING_INTERVAL'] }});

                    $('.level-wall').on('resize scrollstop', function() {
                        var md5 = $items.inviewport().map(function() {
                            return $(this).data('md5');
                        }).get();
                        $.get('/arts', {
                            q: JSON.stringify({ 'md5': md5 })
                        }).then($.aip.jsonresult).done(function(r) {
                            for (var md5 in r) {
                                var $item = $(r[md5]);
                                $buf.append($item);
                                load_one($item);
                            }
                        }).fail(function(reason) {
                            $.aip.notice('arts fail: ' + reason);
                        });
                    });
                }
            };
        })();
    });
})(jQuery);
