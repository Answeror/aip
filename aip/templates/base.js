(function() {
    // http://stackoverflow.com/a/3326655/238472
    if (!window.console) console = {log: function() {}};

    String.prototype.startswith = function(needle)
    {
        return(this.indexOf(needle) == 0);
    };

    $.aip = {};
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
    $.aip.inc = function(name, value) {
        var $t = $('#loading li[name="' + name + '"]');
        if (value == undefined) value = 1;
        $t.text(parseInt($t.text()) + value);
    };
    $.aip.actual_size = function($img, callback) {
        callback($img[0].naturalWidth, $img[0].naturalHeight);
    };
    $.aip.stream = function(kargs) {
        var $d = $.Deferred();
        var es = new EventSource(kargs.url + '?' + $.param(kargs.data));
        es.onmessage = function(e) {
            $.Deferred()
            .resolve($.parseJSON(e.data))
            .then($.aip.error_guard)
            .done(function(r) {
                if ('result' in r) {
                    e.target.close();
                    $d.resolve(r.result);
                } else {
                    $d.reject('unknown event: ' + JSON.stringify(r));
                }
            }).fail(function(reason) {
                e.target.close();
                $d.reject(reason);
            });
        };
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
        var inner = function($img, src, timeout, reloads) {
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
                                $img.attr('width', width);
                                $img.attr('height', height);
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
        if (kargs.src.startswith('https://')) {
            return inner(kargs.img, kargs.src, kargs.timeout, kargs.reloads);
        }
        return $.Deferred().reject(kargs.src + ' not support ssl');
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
        function init_plus($this) {
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
        var nomore = false;
        function pull() {
            if ($.aip.pulling) return;
            if (nomore) return;
            $.aip.pulling = true;
            $this = $(this);
            progress(0);
            $('#loading').show();
            $buffer.empty();
            $this.waypoint('disable');
            $.aip.stream({
                url: kargs.makePageUrl(page),
                data: kargs.makePageData(page)
            }).done(function(data) {
                var $items = $(data).find('.item');
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
                    nomore = true;
                    return;
                }
                $.aip.inc('in-json', n);
                $items.each(function() {
                    $(this).attr('data-done', false);
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
                var init_detail = function($item) {
                    $item.find('a.preview').click(function(e) {
                        var $detail = $('#detail');
                        var $preview = $detail.find('div[name=preview]');
                        var $img = $preview.find('img');
                        var $loading = $detail.find('.loading');
                        $img.hide();
                        // must hide loading first
                        // other wise detail layer won't show properly
                        $loading.hide();
                        $detail.show();
                        $detail.stop().animate({
                            left: '0%'
                        }, 500, 'swing', function() {
                            var hash = '#' + $item.data('md5');
                            window.location.hash = hash;

                            $loading.show();
                            // load image after animation
                            // to archive smooth transition on ipad
                            $.aip.stream({
                                url: '/api/stream/proxied_url/' + $item.data('md5'),
                                data: {
                                    width: $preview.width(),
                                    resolution: 1
                                }
                            }).done(function(uri) {
                                $.aip.load_image({
                                    img: $img,
                                    src: uri,
                                    timeout: 1e3 * {{ config['AIP_LOADING_TIMEOUT'] }},
                                    reloads: $.aip.range({{ config['AIP_RELOAD_LIMIT'] }}).map(function() {
                                        return $.aip.disturb(1e3 * {{ config['AIP_RELOAD_INTERVAL'] }});
                                    })
                                }).done(function() {
                                    $loading.hide();
                                    $img.show();
                                });
                            });
                            $detail.find('[name="source"]').attr('href', $item.data('source'));
                            $detail.find('[name="raw"]').attr('href', '/raw/' + $item.data('md5'));
                        });
                        e.preventDefault();
                    });
                };
                var mars = function($item) {
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
                };
                var dealone = function($item) {
                    if ($item.data('dealed')) return;
                    try {
                        init_plus($item);
                        init_detail($item);
                        mars($item);
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
                            return $.aip.stream({
                                url: '/api/stream/proxied_url/' + $img.data('md5'),
                                //timeout: 1e3 * {{ config['AIP_PROXIED_TIMEOUT'] }},
                                data: { width: $img.width() }
                            });
                        },
                        reloads: $.aip.range({{ config['AIP_REPROXY_LIMIT'] }}).map(function() {
                            return $.aip.disturb(1e3 * {{ config['AIP_REPROXY_INTERVAL'] }});
                        })
                    }).done(function(uri) {
                        $.aip.inc('proxied');
                        try {
                            $.aip.load_image({
                                img: $img,
                                src: uri,
                                timeout: 1e3 * {{ config['AIP_LOADING_TIMEOUT'] }},
                                reloads: $.aip.range({{ config['AIP_RELOAD_LIMIT'] }}).map(function() {
                                    return $.aip.disturb(1e3 * {{ config['AIP_RELOAD_INTERVAL'] }});
                                })
                            }).done(function() {
                                $item.find('.loading').hide();
                                $img.show();
                            }).fail(function(reason) {
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
                    var done = function() {
                        console.log($img.attr('src') + 'loaded');
                        $this.find('.loading').hide();
                        $img.show();
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
                $.aip.warning('load more failed, reason: ' + JSON.stringify(reason));
            });
        };
        $container.waypoint(
            function(direction){
                if (direction === 'down' || direction === 'right') pull();
            }, {
                offset: 'bottom-in-view',
                context: '.level'
            }
        );
        $.aip.inited = true;
    };
    $.aip.is = function(kargs) {
        console.log('init');
        $.aip.init(kargs);
    };

    // smooth scrolling of detail page
    $(function() {
        $('#detail button[name=back]').click(function(e) {
            $('#detail').stop().animate({
                left: '100%'
            }, 500, 'swing', function() {
                window.location.hash = '#wall';
                $('#detail').hide();
            });
            e.preventDefault();
        });
    });
})();
