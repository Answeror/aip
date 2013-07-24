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
        function usesample(width, height) {
            console.log('use sample');
            $sample.attr('src', $sample.data('src'));
            $sample.imagesLoaded().done(function() {
                console.log('use sample done');
                $preview.fadeOut('slow', function() {
                    $sample.width($preview.width());
                    $sample.height(height * $preview.width() / width);
                    $sample.fadeIn('slow');
                });
            }).error(function() {
                console.log('use sample error');
            });
        };
        $src = $preview.attr('src');
        if ($src) {
            truesize(
                $src,
                function(width, height) {
                    if ($preview.width() * $preview.height() > width * height * 3) {
                        usesample(width, height);
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
                    //$items.width(fit);
                    var n = $items.length;
                    var loaded = 0;
                    $items.each(function() {
                        $(this).imagesLoaded(function() {
                            ++loaded;
                            progress(100 * loaded / n);
                        });
                    });
                    $container.imagesLoaded(function() {
                        if ($items.length) {
                            $items.show();
                            $items.each(dealimage);
                            try {
                                if (page == 0) {
                                    $container.masonry({
                                        itemSelector: '.item',
                                        isAnimated: true,
                                        columnWidth: '.span2',
                                        transitionDuration: '0.4s'
                                    });
                                } else {
                                    $container.masonry('appended', $items, true);
                                }
                            } catch (e) {
                                console.log(e);
                            }
                        }
                        if ($items.length) {
                            $this.waypoint('enable');
                        } else {
                            console.log('destroy waypoint');
                            $this.waypoint('destroy');
                        }
                        $('#loading').hide();
                        $('#alert_box').html('');
                        page += 1;
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
