(function($) {
    $.fn.plus_update = function() {
        var $plus = $(this);
        var enable = function(call) {
            $plus.unbind('click').click(call).removeClass('disabled');
        };
        var disable = function() {
            $plus.unbind('click').addClass('disabled');
        };
        var entry = $plus.data('entry');
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
                    $plus.plus_update();
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
                    $plus.plus_update();
                }).fail(function(reason) {
                    console.log('plus failed, reason: ' + JSON.stringify(reason));
                    enable(plus);
                });
            };
            enable(plus);
        }
    };
    $.fn.plus_init = function() {
        var $plus = $(this)
        if (!$.aip.user_id()) {
            $plus.tooltip();
            return;
        }
        $plus.plus_update();
    };
})(jQuery);
