// Generated by CoffeeScript 1.4.0

/*
   Infinite Scroll Shortcut for jQuery Waypoints - v2.0.2
   Copyright (c) 2011-2013 Caleb Troughton
   Dual licensed under the MIT license and GPL license.
   https://github.com/imakewebthings/jquery-waypoints/blob/master/licenses.txt
   */


(function() {

    (function(root, factory) {
        if (typeof define === 'function' && define.amd) {
            return define(['jquery', 'waypoints'], factory);
        } else {
            return factory(root.jQuery);
        }
    })(this, function($) {
        var defaults;
        defaults = {
            container: 'auto',
            items: '.infinite-item',
            more: '.infinite-more-link',
            offset: 'bottom-in-view',
            loadingClass: 'infinite-loading',
            onBeforePageLoad: $.noop,
            onAfterPageLoad: $.noop,
            onBeforeAppended: $.noop,
            onAfterAppended: $.noop,
            progress: $.noop,
            error: $.noop
        };
        return $.waypoints('extendFn', 'infinite', function(options) {
            var $container;
            options = $.extend({}, $.fn.waypoint.defaults, defaults, options);
            $container = options.container === 'auto' ? this : $(options.container);
            options.handler = function(direction) {
                var $this;
                if (direction === 'down' || direction === 'right') {
                    $this = $(this);
                    options.onBeforePageLoad();
                    $this.waypoint('disable');
                    $container.addClass(options.loadingClass);
                    var trigger;
                    return $.ajax({
                        method: 'GET',
                        url: $(options.more).attr('href'),
                        dataType: 'text',
                        contentType: 'application/octet-stream',
                        error: options.error,
                        success: function(data) {
                            var $data, $more, $newMore;
                            $data = $(data);
                            $more = $(options.more);
                            $newMore = $data.find(options.more);
                            $items = $data.find(options.items);
                            options.onBeforeAppended($items);
                            $container.append($items);
                            $container.removeClass(options.loadingClass);
                            options.onAfterAppended($items);
                            if ($newMore.length) {
                                $more.replaceWith($newMore);
                                $this.waypoint('enable');
                            } else {
                                $this.waypoint('destroy');
                            }
                            return options.onAfterPageLoad();
                        },
                        xhr: function() {
                            var xhr = jQuery.ajaxSettings.xhr();
                            trigger = window.setInterval(function() {
                                if (xhr.readyState > 2) {
                                    var totalBytes = xhr.getResponseHeader('Content-length');
                                    if (totalBytes > 0) {
                                        var dlBytes = xhr.responseText.length;
                                        options.progress(dlBytes / totalBytes * 100);
                                    }
                                }
                            }, 100);
                            return xhr;
                        },
                        complete: function() {
                            window.clearInterval(trigger);
                        }
                    });
                }
            };
            return this.waypoint(options);
        });
    });

}).call(this);
