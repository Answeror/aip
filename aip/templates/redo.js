(function($) {
    $.aip.redo = function(kargs) {
        function inner(depth, make, reloads) {
            var $d = $.Deferred();
            function reject() {
                console.log('deferred failed, arguments: ' + JSON.stringify(arguments));
                if (reloads && reloads.length > 0) {
                    setTimeout(function() {
                        console.log('redo');
                        inner(depth + 1, make, reloads.slice(1)).done($d.resolve).fail($d.reject);
                    }, reloads[0]);
                } else {
                    $d.reject(arguments);
                }
            };
            make(depth).done($d.resolve).fail(reject);
            return $d.promise();
        };
        return inner(0, kargs.make, kargs.reloads);
    };
})(jQuery);
