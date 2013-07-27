$(function() {
    function truesize(src, callback) {
        var buf = new Image();
        buf.onload = function() {
            callback(this.width, this.height);
        };
        buf.src = src;
    };
    function dealimage() {
        var $this = $(this);
        var $preview = $this.find('img.preview');
        var src = $preview.attr('src');
        if (src) {
            truesize(
                src,
                function(width, height) {
                    $preview.attr('width', width);
                    $preview.attr('height', height);
                }
            );
        }
        $this.find('.plus').each(function() {
            var $plus = $(this);
            var user = $plus.data('user');
            var entry = $plus.data('entry');
            $plus.update = function() {
                $plus.text('+' + $plus.data('count'));
                if ($plus.data('plused')) {
                    $plus.addClass('btn-primary');
                    $plus.click(function() {
                        $.ajax({
                            method: 'POST',
                            url: '/api/minus',
                            contentType: "application/json",
                            accepts: "application/json",
                            cache: false,
                            dataType: 'json',
                            data: JSON.stringify({ user_id: user, entry_id: entry }),
                            success: function(data) {
                                if (!('error' in data)) {
                                    $plus.data('count', data.count);
                                    $plus.data('plused', false);
                                    $plus.update();
                                }
                            },
                            error: function() {
                                console.log('minus failed');
                            }
                        })
                    });
                } else {
                    $plus.removeClass('btn-primary');
                    $plus.click(function() {
                        $.ajax({
                            method: 'POST',
                            url: '/api/plus',
                            contentType: "application/json",
                            accepts: "application/json",
                            cache: false,
                            dataType: 'json',
                            data: JSON.stringify({ user_id: user, entry_id: entry })
                        }).done(function(data) {
                            if (!('error' in data)) {
                                $plus.data('count', data.count);
                                $plus.data('plused', true);
                                $plus.update();
                            }
                        }).fail(function() {
                            console.log('plus failed');
                        }).always(function() {
                            console.log('plus complete');
                        });
                    });
                }
            };
            $plus.update();
        });
    };
    var $container = $('#items');
    var bootstrap_alert = function() {}
    bootstrap_alert.warning = function(message) {
        $('#alert_box').html('<div class="alert"><a class="close" data-dismiss="alert">×</a><span>'+message+'</span></div>');
    };
    var page = 0;
    function progress(p) {
        $('#bar').width(p + '%');
    };
    var marsed = false;
    var $buffer = $('#buffer');
    $container.waypoint(
        function(direction){
            if (direction === 'down' || direction === 'right') {
                $this = $(this);
                progress(0);
                $('#loading').show();
                console.log('clear buffer');
                console.log('children: ' + $buffer.find('.item').length);
                $buffer.empty();
                $this.waypoint('disable');
                $.ajax({
                    method: 'GET',
                    url: '/api/page/' + page,
                    accepts: "application/json",
                    cache: false
                }).done(function(data) {
                    var $items = $(data.result).find('.item');
                    $buffer.append($items);
                    var n = $items.length;
                    var loaded = 0;
                    var cleanup = function() {
                        if ($items.length) {
                            $this.waypoint('enable');
                        } else {
                            console.log('destroy waypoint');
                            $this.waypoint('destroy');
                        }
                        $('#loading').hide();
                        $('#alert_box').html('');
                        page += 1;
                    };
                    var doneone = function($item) {
                        ++loaded;
                        progress(100 * loaded / n);
                        if (loaded == n) {
                            cleanup();
                        }
                    };
                    var dealone = function($item) {
                        if ($item.data('visited')) return;
                        $item.data('visited', true);
                        doneone($item);
                        $container.append($item);
                        $item.each(dealimage);
                        try {
                            if (!marsed) {
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
                        } catch (e) {
                            console.log(e);
                        }
                    };
                    var proxied = function($item) {
                        var error = function(message) {
                            console.log('get proxied preview link failed');
                            if (message) {
                                console.log(message);
                            }
                            doneone($item);
                        };
                        try {
                            var $img = $item.find('img.preview');
                            $.ajax({
                                method: 'GET',
                                url: $img.data('proxied-url'),
                                accepts: "application/json",
                                cache: false,
                                dataType: 'json',
                                data: { width: $img.width() }
                            }).done(function(data) {
                                try {
                                    if ('error' in data) {
                                        error(data.error.message);
                                    } else {
                                        $item.imagesLoaded().done(function() {
                                            dealone($item);
                                        });
                                        $img.attr('src', data.result);
                                    }
                                } catch (e) {
                                    error(e.message);
                                }
                            }).fail(error);
                        } catch (e) {
                            error(e.message);
                        }
                    };
                    var timeout = false;
                    var timeoutId = window.setTimeout(function() {
                        timeout = true;
                        var $items = $buffer.find('.item');
                        console.log('timeout, remains: ' + $items.length);
                        $items.each(function() {
                            proxied($(this));
                        });
                    }, 5000);
                    $items.imagesLoaded().progress(function(self, image) {
                        if (!timeout) {
                            var $item = $buffer.find('.item[data-md5="' + $(image.img).data('md5') + '"]');
                            if (image.isLoaded) {
                                var $img = $(image.img);
                                truesize(
                                    $img.attr('src'),
                                    function(width, height) {
                                        var r = {{ config['AIP_RESOLUTION_LEVEL'] }};
                                        if (width * height * r < $img.width() * $img.height()) {
                                            proxied($item);
                                        } else {
                                            dealone($item);
                                        }
                                    }
                                );
                            } else {
                                proxied($item);
                            }
                        }
                    });
                }).fail(function() {
                    $('#loading').hide();
                    bootstrap_alert.warning('Load more failed.');
                });
            }
        }, {
            offset: 'bottom-in-view'
        }
    );
});
