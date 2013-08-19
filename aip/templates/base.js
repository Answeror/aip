// http://stackoverflow.com/a/3326655/238472
if (!window.console) console = {log: function() {}};
$.aip = {};
// store async calls' deferred object or their result when their result comes
// earlier than their ids
$.aip.calls = {};
$.aip.now = function() {
    return new Date().getTime() / 1000;
};
// http://stackoverflow.com/a/2117523/238472
$.aip.uuid = function() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
        return v.toString(16);
    });
};
$.aip.error_guard = function(r) {
    return $.Deferred(function($d) {
        if (r && 'error' in r) {
            $d.reject(r.error.message);
        } else {
            $d.resolve(r);
        }
    });
};
$.aip.range = function(n) {
    return Array.apply(0, Array(n)).map(function(e, i) { return i; });
};
$.fn.freeze_size = function() {
    var $this = $(this);
    $this.attr('width', $this.width());
    $this.attr('height', $this.width() * $this.data('height') / $this.data('width'));
    $this.width($this.attr('width'));
    $this.height($this.attr('height'));
};
$.aip.inc = function(name, value) {
    var $t = $('#loading li[name="' + name + '"]');
    if (value == undefined) value = 1;
    $t.text(parseInt($t.text()) + value);
};
$.aip.actual_size = function($img, callback) {
    callback($img[0].naturalWidth, $img[0].naturalHeight);
};
$.aip.async = function(kargs) {
    kargs.url = '/api/async/' + $.aip.sid + kargs.url.slice(4);
    var $d = $.Deferred();
    $.ajax(kargs).then($.aip.error_guard).done(function(r) {
        if (!(r.result.id in $.aip.calls)) {
            $.aip.calls[r.result.id] = $d;
            if (kargs.timeout) {
                setTimeout(function() {
                    if (r.result.id in $.aip.calls) {
                        console.log(r.result.id + ' timeout');
                        $.aip.calls[r.result.id].reject('timeout');
                        delete $.aip.calls[r.result.id];
                    }
                }, kargs.timeout);
            }
        } else {
            console.log('async call ' + r.result.id + ' arrive later than its result');
            // result is already here
            $d.resolve($.aip.calls[r.result.id]);
            delete $.aip.calls[r.result.id];
        }
    }).fail($d.reject);
    return $d;
};
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
$.aip.load_image = function(kargs) {
    function inner($img, src, timeout, reloads) {
        return $.aip.redo({
            make: function(depth) {
                console.log((depth + 1) + 'th loading ' + src);
                // each cross means a reload
                // mod 2 to force reload
                var preview_src = src + '?x=' + ((depth + 2) % 2);
                //var preview_src = src;
                $img.attr('src', preview_src);
                var tid = setTimeout(function() {
                    reject('timeout');
                }, timeout);
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
                $img.imagesLoaded().done(function() {
                    clearTimeout(tid);
                    if (!rejected) {
                        console.log('loaded: ' + preview_src);
                        $.aip.actual_size($img, function(width, height) {
                            console.log('sized(' + width + 'x' + height + '): ' + preview_src);
                            $img.data('preview-width', width);
                            $img.data('preview-height', height);
                            $d.resolve();
                        });
                    }
                }).fail(function() {
                    clearTimeout(tid);
                    reject('unknown');
                });
                return $d.promise();
            },
            reloads: reloads
        });
    };
    return inner(kargs.img, kargs.src, kargs.timeout, kargs.reloads);
};
$.fn.preview_area = function() {
    return $(this).data('preview-width') * $(this).data('preview-height');
};
$.fn.viewport_area = function() {
    return $(this).width() * $(this).height();
};
$.aip.super_resolution = function($img, callback, otherwise) {
    var r = {{ config['AIP_RESOLUTION_LEVEL'] }};
    var aa = $img.preview_area();
    var va = $img.viewport_area();
    var need = aa * r < va;
    console.log('super resolution ' + aa + ' x ' + r + ' < ' + va + ' -> ' + need);
    if (need) {
        $.aip.inc('need-enlarge');
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
$.aip._user_id = $('#user-id');
$.aip.user_id = function() {
    if ($.aip._user_id.length) {
        return $.aip._user_id.attr('value');
    } else {
        return undefined;
    }
};
$.aip.overflown = function($tag) {
    return $tag[0].scrollWidth >  $tag.innerWidth();
};
$.aip.init = function(kargs) {
    defaults = {
        makePageData: $.noop
    };
    kargs = $.extend({}, defaults, kargs);
    function dealplus($this) {
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
                        $.aip.async({
                            method: 'POST',
                            url: '/api/minus',
                            contentType: "application/json",
                            accepts: "application/json",
                            cache: false,
                            dataType: 'json',
                            data: JSON.stringify({ user_id: $.aip.user_id(), entry_id: entry })
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
                        $.aip.async({
                            method: 'POST',
                            url: '/api/plus',
                            contentType: "application/json",
                            accepts: "application/json",
                            cache: false,
                            dataType: 'json',
                            data: JSON.stringify({ user_id: $.aip.user_id(), entry_id: entry })
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
    var $container = $('#items');
    var page = 0;
    function progress(p) {
        $('#bar').width(p + '%');
    };
    var marsed = false;
    var $buffer = $('#buffer');
    $container.popover({
        selector: '.btn[name="tags"]',
        container: 'body',
        html: true,
        content: function() {
            return $(this).closest('.item').find('.tags').html();
        },
        placement: function(context, source) {
            var $s = $(source);
            var p = $s.offset();
            p.right = ($(window).width() - (p.left + $s.outerWidth()));
            if (p.right > 276) return 'right';
            if (p.left > 276) return 'left';
            if (p.top > 110) return 'top';
            return 'bottom';
        }
    });
    function pull() {
        if ($.aip.pulling) return;
        $.aip.pulling = true;
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
        }).then($.aip.error_guard).done(function(data) {
            var $items = $(data.result).find('.item');
            var n = $items.length;
            var cleanup = function() {
                if (n) {
                    $this.waypoint('enable');
                } else {
                    console.log('destroy waypoint');
                    $this.waypoint('destroy');
                }
                $('#loading').hide();
                $('#alert_box').html('');
                page += 1;
                $.aip.pulling = false;
                if (n) {
                    $.waypoints('refresh');
                    if ($container.outerHeight() <= $.waypoints('viewportHeight')) pull();
                }
            };
            if (!n) {
                cleanup();
                return;
            }
            $.aip.inc('in-json', n);
            $items.each(function() {
                $(this).attr('data-loading', false).attr('data-done', false);
            });
            $buffer.append($items);
            var loaded = 0;
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
                if ($item.data('dealed')) return;
                try {
                    dealplus($item);
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
                    $.aip.inc('done');
                } catch (e) {
                    console.log('dealone failed');
                    console.log(e);
                } finally {
                    $item.data('dealed', true);
                    guarded_doneone($item);
                }
            };
            var proxied = function($item) {
                $.aip.inc('need-proxied');
                dealone($item);
                var error = function(message) {
                    $.aip.error(message);
                    guarded_doneone($item);
                };
                var $img = $item.find('img.preview');
                $.aip.redo({
                    make: function() {
                        return $.aip.async({
                            method: 'GET',
                            url: '/api/proxied_url/' + $img.data('md5'),
                            accepts: "application/json",
                            cache: false,
                            dataType: 'json',
                            timeout: 1e3 * {{ config['AIP_PROXIED_TIMEOUT'] }},
                            data: { width: $img.width() }
                        }).then($.aip.error_guard);
                    },
                    reloads: $.aip.range({{ config['AIP_REPROXY_LIMIT'] }}).map(function() {
                        return $.aip.disturb(1e3 * {{ config['AIP_REPROXY_INTERVAL'] }});
                    })
                }).done(function(r) {
                    $.aip.inc('proxied');
                    try {
                        $.aip.load_image({
                            img: $img,
                            src: r.result,
                            timeout: 1e3 * {{ config['AIP_LOADING_TIMEOUT'] }},
                            reloads: $.aip.range({{ config['AIP_RELOAD_LIMIT'] }}).map(function() {
                                return $.aip.disturb(1e3 * {{ config['AIP_RELOAD_INTERVAL'] }});
                            })
                        }).done($.noop).fail(function(reason) {
                            error('load image failed, reason: ' + JSON.stringify(reason));
                            $.aip.inc('proxied-preview-loading-failed');
                        });
                    } catch (e) {
                        console.log('fatal error');
                        console.log(JSON.stringify(e));
                        console.trace();
                    }
                }).fail(function(reason) {
                    error('proxy failed, reason: ' + JSON.stringify(reason));
                });
            };
            $items.each(function() {
                var $this = $(this);
                var $img = $this.find('img.preview');
                $img.freeze_size();
                var done = function() {
                    console.log($img.attr('src') + 'loaded');
                    $this.attr('data-loading', true);
                    var r = {{ config['AIP_RESOLUTION_LEVEL'] }};
                    $.aip.super_resolution($img, function() {
                        proxied($this);
                    }, function() {
                        dealone($this);
                    });
                };
                var fail = function(reason) {
                    console.log('load image failed, reason: ' + reason);
                    $.aip.inc('original-preview-loading-failed');
                    proxied($this);
                };
                var limit = {{ config['AIP_RELOAD_LIMIT'] }};
                $.aip.load_image({
                    img: $img,
                    src: $img.data('src'),
                    timeout: 1e3 * {{ config['AIP_LOADING_TIMEOUT'] }}
                }).done(done).fail(function(reason) {
                    if (limit == 0) {
                        fail(reason);
                    } else {
                        // first try failed, show blank image
                        dealone($this);
                        $.aip.load_image({
                            img: $img,
                            src: $img.data('src'),
                            timeout: 1e3 * {{ config['AIP_LOADING_TIMEOUT'] }},
                            reloads: $.aip.range(limit - 1).map(function() {
                                return $.aip.disturb({{ config['AIP_RELOAD_INTERVAL'] }});
                            })
                        }).done(done).fail(fail);
                    }
                });
            });
        }).fail(function(reason) {
            $('#loading').hide();
            $.aip.log.warning('load more failed, reason: ' + JSON.stringify(reason));
        });
    };
    $container.waypoint(
        function(direction){
            if (direction === 'down' || direction === 'right') pull();
        }, {
            offset: 'bottom-in-view'
        }
    );
    $.aip.inited = true;
};
$.aip.is = function(kargs) {
    $.aip.source = new EventSource('/api/async/stream/' + $.aip.uuid());
    $.aip.source.onmessage = function(e) {
        $.Deferred().resolve($.parseJSON(e.data)).then($.aip.error_guard).done(function(r) {
            if (r.key == 'hello') {
                $.aip.sid = r.value;
                console.log('hello: ' + $.aip.sid);
                if (!$.aip.inited) {
                    console.log('init');
                    $.aip.init(kargs);
                }
                $.ajax({
                    method: 'POST',
                    url: '/api/async/reply/' + $.aip.sid,
                    cache: false
                });
            } else if (r.key == 'result') {
                if (r.value.id in $.aip.calls) {
                    console.log('result: ' + r.value.id);
                    $.aip.calls[r.value.id].resolve(r.value.result);
                    delete $.aip.calls[r.value.id];
                } else {
                    // async call id arrive later than its result
                    // store its result first
                    $.aip.calls[r.value.id] = r.value.result;
                }
            } else {
                console.log('unknown event: ' + r.key);
            }
        }).fail(function(reason) {
            console.log('pump failed, reason: ' + JSON.stringify(reason));
        });
    };
};
