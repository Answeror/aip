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
    //$('[data-lightbox]').simpleLightbox();
    $container.masonry({
        itemSelector: '.item',
        gutter: gutter,
        isAnimated: true,
        columnWidth: min_width
    });
    $container.lazyload();
    $('#items').waypoint('infinite', {
        items: '.item',
        more: '.more',
        onAfterAppended: function($items) {
            // ensure that images load before adding to masonry layout
            $items.width(fit);
            //$items.find('[data-lightbox]').simpleLightbox();
            $container.masonry('appended', $items, true);
            $items.lazyload();
        }
    });
});
