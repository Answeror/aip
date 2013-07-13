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
        truesize(
            $preview.data('src'),
            function(width, height) {
                if ($preview.width() * $preview.height() > width * height * 3) {
                    //usesample();
                }
            }
        );
        //$preview.lazyload();
    };
    var $container = $('#items');
    var $items = $container.find('.item');
    $items.each(dealimage);
    $items.width(fit);
    $container.masonry({
        itemSelector: '.item',
        gutter: gutter,
        isAnimated: true,
        columnWidth: min_width
    });
    var bootstrap_alert = function() {}
    bootstrap_alert.warning = function(message) {
        $('#alert_box').html('<div class="alert"><a class="close" data-dismiss="alert">×</a><span>'+message+'</span></div>');
    }
    $('#items').waypoint('infinite', {
        items: '.item',
        more: '.more',
        onBeforeAppended: function($items) {
            $items.each(dealimage);
        },
        onAfterAppended: function($items) {
            console.log('append');
            if ($items) {
                $items.width(fit);
                try {
                    $container.masonry('appended', $items, true);
                } catch (e) {}
            }
        },
        onBeforePageLoad: function() {
            $('#loading').show();
        },
        onAfterPageLoad: function() {
            $('#loading').hide();
            $('#alert_box').html('');
        },
        error: function() {
            $('#loading').hide();
            bootstrap_alert.warning('Load more failed.');
        }
    });
});
