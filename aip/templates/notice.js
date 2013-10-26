(function($) {
    $.aip.notice = function(message) {
        console.log(message);
        var $message = $('<p style="display:none;">' + message + '</p>');
        $('.notice').append($message);
        $message.slideDown(300, function() {
            window.setTimeout(function() {
                $message.slideUp(300, function() {
                    $message.remove();
                });
            }, 2000);
        });
    };
})(jQuery);
