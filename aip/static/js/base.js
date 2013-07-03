$(function() {
    $.fn.lazyload = function(){
        $this = $(this);
        $this.find('img').waypoint(function(){
            $this = $(this);
            $this.hide().attr("src", $this.data('original')).fadeIn(1000);
        }, {
            triggerOnce: true,
            offset: function() {
                return $.waypoints('viewportHeight') + $(this).height();
            }
        });
    };
    var $container = $('#items');
    var gutter = 10;
    var min_width = 200;
    function fit(index, width){
        var cols = Math.floor(width / min_width);
        return cols * min_width + (cols - 1) * gutter;
    };
    $('.item').width(fit);
    function proxy() {
        this.src = $(this).data('proxy');
    };
    $('img').one('error', proxy);
    //$('[data-lightbox]').simpleLightbox();
    $container.masonry({
        itemSelector: '.item',
        gutter: gutter,
        isAnimated: true,
        columnWidth: min_width
    });
    $container.lazyload();
    bootstrap_alert = function() {}
    bootstrap_alert.warning = function(message) {
        $('#alert_box').html('<div class="alert"><a class="close" data-dismiss="alert">×</a><span>'+message+'</span></div>');
    }
    $('#items').waypoint('infinite', {
        items: '.item',
        more: '.more',
        onAfterAppended: function($items) {
            // ensure that images load before adding to masonry layout
            $items.width(fit);
            $items.find('img').one('error', proxy);
            //$items.find('[data-lightbox]').simpleLightbox();
            $container.masonry('appended', $items, true);
            $items.lazyload();
        },
        onBeforePageLoad: function() {
            $('#progress > .bar').css('width', '0%');
            $('#progress').show();
        },
        onAfterPageLoad: function() {
            $('#progress').hide();
            $('#alert_box').html('');
        },
        progress: function(e) {
            console.log('progress');
            if (e.lengthComputable) {
                var p = (e.loaded / e.total) * 100;
                console.log(p);
                $('#progress > .bar').css('width', p + '%');
            } else {
                console.warn('Content Length not reported!');
            }
        },
        error: function() {
            $('#progress').hide();
            bootstrap_alert.warning('Load more failed. Retrying...');
            $.waypoints('refresh');
        }
    });
});
