// http://stackoverflow.com/a/3326655/238472
if (!window.console) console = {log: function() {}};
$.aip = {};
$.aip.range = function(n) {
    return Array(0, Array(n)).map(function(e, i) { return i; });
};
$.aip.actual_size = function(src, callback) {
    var buf = new Image();
    buf.onload = function() {
        callback(this.width, this.height);
    };
    buf.src = src;
};
$.aip.load_image = function(kargs) {
    function inner($img, src, timeout, reloads) {
        $img.attr('src', src);
        var d = $.Deferred().done(function() {
            clearTimeout(tid);
        }).fail(function() {
            clearTimeout(tid);
        });
        var rejected = false;
        function reject(reason) {
            rejected = true;
            console.log('load image failed, reason: ' + reason);
            if (reloads.length > 0) {
                setTimeout(function() {
                    console.log('reload ' + src);
                    // each cross means a reload
                    inner($img, src + 'x', timeout, reloads.slice(1)).done(d.resolve).fail(d.reject);
                }, reloads[0]);
            } else {
                d.reject(reason);
            }
        };
        var tid = setTimeout(function() {
            reject('timeout');
        }, timeout);
        var imd = $img.imagesLoaded().done(function() {
            if (!rejected) {
                $.aip.actual_size(src, function(width, height) {
                    $img.data('actual-width', width);
                    $img.data('actual-height', height);
                    $img.attr('width', $img.width());
                    $img.attr('height', $img.width() * height / width);
                    d.resolve();
                });
            }
        }).fail(function() {
            reject('unknown');
        });
        return d.promise();
    };
    return inner(kargs.img, kargs.src + '?x', kargs.timeout, kargs.reloads.slice(0));
};
$.aip.super_resolution = function($img, callback, otherwise) {
    var r = {{ config['AIP_RESOLUTION_LEVEL'] }};
    if ($img.data('actual-width') * $img.data('actual-height') * r < $img.width() * $img.height()) {
        callback();
    } else {
        otherwise();
    }
};
$.aip.error = function(message) {
    console.log(message);
    $('#alert_box').html('<div class="alert"><a class="close" data-dismiss="alert">×</a><span>'+message+'</span></div>');
};
$.aip.warning = $.aip.error;
$.aip.disturb = function(x) {
    return x * (Math.random() + 0.5)
};
$.aip.is = function(kargs) {
    defaults = {
        makePageData: $.noop
    };
    kargs = $.extend({}, defaults, kargs);
    function postprocess($this, callback) {
        var $preview = $this.find('img.preview');
        $this.find('.plus').each(function() {
            var $plus = $(this);
            var user = $plus.data('user');
            var entry = $plus.data('entry');
            $plus.update = function() {
                $plus.text('+' + $plus.data('count'));
                if ($plus.data('plused')) {
                    $plus.addClass('btn-primary');
                    $plus.click(function() {
                        $.ajax({
                            method: 'POST',
                            url: '/api/minus',
                            contentType: "application/json",
                            accepts: "application/json",
                            cache: false,
                            dataType: 'json',
                            data: JSON.stringify({ user_id: user, entry_id: entry }),
                            success: function(data) {
                                if (!('error' in data)) {
                                    $plus.data('count', data.count);
                                    $plus.data('plused', false);
                                    $plus.update();
                                }
                            },
                            error: function() {
                                console.log('minus failed');
                            }
                        })
                    });
                } else {
                    $plus.removeClass('btn-primary');
                    $plus.click(function() {
                        $.ajax({
                            method: 'POST',
                            url: '/api/plus',
                            contentType: "application/json",
                            accepts: "application/json",
                            cache: false,
                            dataType: 'json',
                            data: JSON.stringify({ user_id: user, entry_id: entry })
                        }).done(function(data) {
                            if (!('error' in data)) {
                                $plus.data('count', data.count);
                                $plus.data('plused', true);
                                $plus.update();
                            }
                        }).fail(function() {
                            console.log('plus failed');
                        }).always(function() {
                            console.log('plus complete');
                        });
                    });
                }
            };
            $plus.update();
            callback();
        });
    };
    var $container = $('#items');
    var page = 0;
    function progress(p) {
        $('#bar').width(p + '%');
    };
    var marsed = false;
    var $buffer = $('#buffer');
    $container.waypoint(
        function(direction){
            if (direction === 'down' || direction === 'right') {
                $this = $(this);
                progress(0);
                $('#loading').show();
                $buffer.empty();
                $this.waypoint('disable');
                $.ajax({
                    method: 'GET',
                    url: kargs.makePageUrl(page),
                    accepts: "application/json",
                    cache: false,
                    dataType: 'json',
                    data: kargs.makePageData(page)
                }).done(function(data) {
                    var $items = $(data.result).find('.item');
                    $items.each(function() {
                        $(this).attr('data-loading', false).attr('data-done', false);
                    });
                    $buffer.append($items);
                    var n = $items.length;
                    var loaded = 0;
                    var cleanup = function() {
                        if ($items.length) {
                            $this.waypoint('enable');
                        } else {
                            console.log('destroy waypoint');
                            $this.waypoint('destroy');
                        }
                        $('#loading').hide();
                        $('#alert_box').html('');
                        page += 1;
                    };
                    // no exception
                    var doneone = function($item) {
                        ++loaded;
                        progress(100 * loaded / n);
                        if (loaded == n) {
                            cleanup();
                        } else if (loaded > n) {
                            throw 'loaded(' + loaded + ') > n(' + n + ')';
                        }
                    };
                    var guarded_doneone = function($item) {
                        if ($item.attr('data-done') == 'false') {
                            doneone($item);
                            $item.attr('data-done', true);
                        }
                    };
                    var dealone = function($item) {
                        var guarded = function(f) {
                            var inner = function() {
                                try {
                                    return f(arguments);
                                } catch (e) {
                                    console.log(e);
                                } finally {
                                    guarded_doneone($item);
                                }
                            };
                            return inner;
                        };
                        try {
                            postprocess($item, guarded(function() {
                                $container.append($item);
                                if (!marsed) {
                                    console.log('initialize masonry');
                                    $container.masonry({
                                        itemSelector: '.item',
                                        isAnimated: true,
                                        columnWidth: '.span2',
                                        transitionDuration: '0.4s'
                                    });
                                    marsed = true;
                                } else {
                                    $container.masonry('appended', $item, true);
                                }
                            }));
                        } catch (e) {
                            console.log(e);
                            guarded_doneone($item);
                        }
                    };
                    var proxied = function($item) {
                        var error = function(message) {
                            var s = 'get proxied preview link failed';
                            if (message) {
                                s += '\n' + message;
                            }
                            $.aip.error(s);
                            guarded_doneone($item);
                        };
                        var $img = $item.find('img.preview');
                        var failCount = 0;
                        var proxy;
                        function reproxy() {
                            if (failCount >= {{ config['AIP_REPROXY_LIMIT'] }}) {
                                error('reproxy ' + $img.attr('src') + ' too many times');
                            } else {
                                ++failCount;
                                setTimeout(function() {
                                    console.log('reproxy ' + $img.attr('src'));
                                    proxy();
                                }, $.aip.disturb({{ config['AIP_REPROXY_INTERVAL'] }}));
                            }
                        };
                        var proxy = function() {
                            $.ajax({
                                method: 'GET',
                                url: $img.data('proxied-url'),
                                accepts: "application/json",
                                cache: false,
                                dataType: 'json',
                                timeout: {{ config['AIP_PROXIED_TIMEOUT'] }},
                                data: { width: $img.width() }
                            }).done(function(data) {
                                if ('error' in data) {
                                    console.log(data.error.message);
                                    reproxy();
                                } else {
                                    $.aip.load_image({
                                        img: $img,
                                        src: data.result,
                                        timeout: {{ config['AIP_LOADING_TIMEOUT'] }},
                                        reloads: $.aip.range(3).map(function() {
                                            return $.aip.disturb({{ config['AIP_RELOAD_INTERVAL'] }});
                                        })
                                    }).done(function() {
                                        dealone($item);
                                    }).fail(function(reason) {
                                        error('load image failed, reason: ' + reason);
                                    });
                                }
                            }).fail(function(x, t, m) {
                                console.log(t);
                                reproxy();
                            });
                        };
                        proxy();
                    };
                    $items.each(function() {
                        var $this = $(this);
                        var $img = $this.find('img.preview');
                        $.aip.load_image({
                            img: $img,
                            src: $img.data('src'),
                            timeout: {{ config['AIP_LOADING_TIMEOUT'] }},
                            reloads: $.aip.range(3).map(function() {
                                return $.aip.disturb({{ config['AIP_RELOAD_INTERVAL'] }});
                            })
                        }).done(function() {
                            $this.attr('data-loading', true);
                            var r = {{ config['AIP_RESOLUTION_LEVEL'] }};
                            $.aip.super_resolution($img, function() {
                                proxied($this);
                            }, function() {
                                dealone($this);
                            });
                        }).fail(function(reason) {
                            console.log('load image failed, reason: ' + reason);
                            proxied($this);
                        });
                    });
                }).fail(function() {
                    $('#loading').hide();
                    $.aip.log.warning('Load more failed.');
                });
            }
        }, {
            offset: 'bottom-in-view'
        }
    );
};
