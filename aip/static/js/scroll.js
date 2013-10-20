//http://james.padolsey.com/javascript/special-scroll-events-for-jquery/
(function(){
    var special = jQuery.event.special;
    var uid1 = 'D' + (+new Date());
    var uid2 = 'D' + (+new Date() + 1);

    special.scrollstart = {
        setup: function() {
            var $this = $(this);
            var timer;
            var handler =  function(evt) {
                var _args = arguments;
                if (timer) {
                    clearTimeout(timer);
                } else {
                    evt.type = 'scrollstart';
                    $this.trigger('scrollstart', _args);
                }
                timer = setTimeout( function(){
                    timer = null;
                }, special.scrollstop.latency);

            };
            $this.on('scroll', handler).data(uid1, handler);
        },
        teardown: function(){
            $this.off( 'scroll', $this.data(uid1) );
        }
    };

    special.scrollstop = {
        latency: 300,
        setup: function() {
            var $this = $(this);
            var timer;
            var handler = function(evt) {
                var _args = arguments;
                if (timer) {
                    clearTimeout(timer);
                }
                timer = setTimeout( function(){
                    timer = null;
                    evt.type = 'scrollstop';
                    $this.trigger('scrollstop', _args);

                }, special.scrollstop.latency);
            };
            $this.on('scroll', handler).data(uid2, handler);
        },
        teardown: function() {
            $this.off( 'scroll', $this.data(uid2) );
        }
    };
})();
