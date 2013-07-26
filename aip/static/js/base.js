$(function() {
    //$.fn.lazyload = function(){
        //var $this = $(this);
        //$this.waypoint(
            //function(){
                //$this.hide().attr("src", $this.data('src')).fadeIn('slow');
            //}, {
                //triggerOnce: true,
                //offset: function() {
                    //return $.waypoints('viewportHeight') + $(this).height();
                //}
            //}
        //);
    //};
    var gutter = 10;
    var min_width = 200;
    function fit(index, width){
        var cols = Math.floor(width / min_width);
        return cols * min_width + (cols - 1) * gutter;
    };
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
        var $sample = $this.find('img.sample');
        function usesample() {
            console.log('use sample');
            $.ajax({
                method: 'GET',
                url: $sample.data('src'),
                accepts: "application/json",
                cache: false
            }).done(function(data) {
                if ('error' in data) {
                    console.log('get sample link failed');
                } else {
                    $sample.attr('src', data.result);
                    $sample.imagesLoaded().done(function() {
                        console.log('use sample done');
                        $preview.fadeOut('slow', function() {
                            $sample.fadeIn('slow');
                        });
                    }).error(function() {
                        console.log('use sample error');
                    });
                }
            }).error(function() {
                console.log('get sample link failed');
            });
        };
        var src = $preview.attr('src');
        if (src) {
            truesize(
                src,
                function(width, height) {
                    $preview.attr('width', width);
                    $preview.attr('height', height);
                    $sample.attr('width', width);
                    $sample.attr('height', height);
                    if ($preview.width() * $preview.height() > width * height * 3) {
                        //usesample();
                    }
                }
            );
        }
        //$preview.lazyload();
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
        console.log(p);
        $('#bar').width(p + '%');
    };
    var marsed = false;
    $container.waypoint(
        function(direction){
            if (direction === 'down' || direction === 'right') {
                $this = $(this);
                progress(0);
                $('#loading').show();
                $this.waypoint('disable');
                $.ajax({
                    method: 'GET',
                    url: '/api/page/' + page,
                    accepts: "application/json",
                    cache: false
                }).done(function(data) {
                    var $items = $(data.result).find('.item');
                    $items.hide();
                    $container.append($items);
                    var n = $items.length;
                    var loaded = 0;
                    var always = function() {
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
                    var dealone = function($item) {
                        if ($item.data('visited')) return;
                        $item.data('visited', true);
                        ++loaded;
                        progress(100 * loaded / n);
                        $item.show();
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
                    var useproxy = function($item) {
                        var $img = $item.find('img.preview');
                        $.ajax({
                            method: 'GET',
                            url: $img.data('proxied-preview'),
                            accepts: "application/json",
                            cache: false
                        }).done(function(data) {
                            if ('error' in data) {
                                console.log('get proxied preview link failed');
                            } else {
                                $item.imagesLoaded().done(function() {
                                    dealone($item);
                                });
                                $img.attr('src', data.result);
                            }
                        }).error(function() {
                            console.log('get proxied preview link failed');
                        });
                    };
                    var timeout = false;
                    var timeoutId = window.setTimeout(function() {
                        timeout = true;
                        $items.each(function() {
                            console.log('timeout dealone');
                            useproxy($(this));
                        });
                        $items.imagesLoaded().always(always);
                    }, 5000);
                    $items.imagesLoaded().progress(function(self, image) {
                        if (!timeout) {
                            var $item = $items.filter('[data-md5="' + $(image.img).data('md5') + '"]');
                            if (image.isLoaded) {
                                if ($item.length) {
                                    dealone($item);
                                }
                            } else {
                                useproxy($item);
                            }
                        }
                    }).always(function() {
                        window.clearTimeout(timeoutId);
                        if (!timeout) {
                            always();
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
