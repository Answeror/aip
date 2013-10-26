(function($) {
    $.aip.init_plus = function($this) {
        var $plus = $this.find('.plus');
        if (!$.aip.user_id()) {
            $plus.tooltip();
            return;
        }
        $plus.each(function() {
            var $plus = $(this);
            var entry = $plus.data('entry');
            var disable = function() {
                $plus.unbind('click').addClass('disabled');
            };
            var enable = function(call) {
                $plus.unbind('click').click(call).removeClass('disabled');
            };
            $plus.update = function() {
                $plus.text('+' + $plus.data('count'));
                if ($plus.data('plused')) {
                    $plus.addClass('btn-primary');
                    function minus() {
                        disable();
                        $.aip.stream({
                            url: '/api/stream/minus',
                            data: { user_id: $.aip.user_id(), entry_id: entry }
                        }).done(function(data) {
                            $plus.data('count', data.count);
                            $plus.data('plused', false);
                            $plus.update();
                        }).fail(function(reason) {
                            console.log('minus failed, reason: ' + JSON.stringify(reason));
                            enable(minus);
                        });
                    };
                    enable(minus);
                } else {
                    $plus.removeClass('btn-primary');
                    function plus() {
                        disable();
                        $.aip.stream({
                            url: '/api/stream/plus',
                            data: { user_id: $.aip.user_id(), entry_id: entry }
                        }).done(function(data) {
                            $plus.data('count', data.count);
                            $plus.data('plused', true);
                            $plus.update();
                        }).fail(function(reason) {
                            console.log('plus failed, reason: ' + JSON.stringify(reason));
                            enable(plus);
                        });
                    };
                    enable(plus);
                }
            };
            $plus.update();
        });
    };
})(jQuery);
