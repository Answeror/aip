(function($) {
    // http://stackoverflow.com/a/3326655/238472
    if (!window.console) console = {log: function() {}};

    String.prototype.startswith = function(needle) {
        return(this.indexOf(needle) == 0);
    };

    // aip namespace
    if (!$.aip) $.aip = {};
})(jQuery);
