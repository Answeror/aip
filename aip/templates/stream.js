(function($){
    $.aip.stream = function(kargs) {
        var defaults = {
            timeout: 1e8
        };
        kargs = $.extend({}, defaults, kargs);
        var tid = setTimeout(function() {
            reject('timeout');
        }, kargs.timeout);
        var $d = $.Deferred().done(function() {
            clearTimeout(tid);
        }).fail(function() {
            clearTimeout(tid);
        });
        var rejected = false;
        function reject(reason) {
            rejected = true;
            $d.reject(reason);
        };
        var es = new EventSource($.param.querystring(kargs.url, $.param(kargs.data)));
        es.onmessage = function(e) {
            $.Deferred()
            .resolve($.parseJSON(e.data))
            .then($.aip.error_guard)
            .done(function(r) {
                clearTimeout(tid);
                if (!rejected) {
                    if ('result' in r) {
                        e.target.close();
                        $d.resolve(r.result);
                    } else {
                        reject('unknown event: ' + JSON.stringify(r));
                    }
                }
            }).fail(function(reason) {
                e.target.close();
                reject(reason);
            });
        };
        return $d;
    };
})(jQuery);
