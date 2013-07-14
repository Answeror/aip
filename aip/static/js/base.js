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
        var $preview = $this.find('.preview');
        var $sample = $this.find('.sample');
        function usesample() {
            console.log('use sample');
            $sample.attr('src', $sample.data('src'));
            $sample.imagesLoaded().done(function() {
                console.log('use sample done');
                $preview.fadeOut('slow', function() {
                    $sample.fadeIn('slow');
                });
            }).error(function() {
                console.log('use sample error');
            });
        };
        //$preview.one('error', usesample);
        $src = $preview.data('src');
        if ($src) {
            truesize(
                $src,
                function(width, height) {
                    if ($preview.width() * $preview.height() > width * height * 3) {
                        //usesample();
                    }
                }
            );
        }
        //$preview.lazyload();
    };
    var $container = $('#items');
    var $items = $container.find('.item');
    $items.each(dealimage);
    var bootstrap_alert = function() {}
    bootstrap_alert.warning = function(message) {
        $('#alert_box').html('<div class="alert"><a class="close" data-dismiss="alert">×</a><span>'+message+'</span></div>');
    }
    var page = 0;
    $container.waypoint(
        function(direction){
            if (direction === 'down' || direction === 'right') {
                $this = $(this);
                $('#loading').show();
                $this.waypoint('disable');
                $.ajax({
                    method: 'GET',
                    url: '/api/page/' + page,
                    accepts: "application/json",
                    cache: false,
                    success: function(data) {
                        var $data = $(data.result);
                        var $items = $data.find('.item');
                        $items.each(dealimage);
                        $container.append($items);
                        if ($items) {
                            $items.width(fit);
                            try {
                                if (page == 0) {
                                    $container.masonry({
                                        itemSelector: '.item',
                                        gutter: gutter,
                                        isAnimated: true,
                                        columnWidth: min_width
                                    });
                                } else {
                                    $container.masonry('appended', $items, true);
                                }
                            } catch (e) {
                                console.log(e);
                            }
                        }
                        $this.waypoint('enable');
                        $('#loading').hide();
                        $('#alert_box').html('');
                        page += 1;
                    },
                    error: function() {
                        $('#loading').hide();
                        bootstrap_alert.warning('Load more failed.');
                    }
                });
            }
        }, {
            offset: 'bottom-in-view'
        }
    );
});
