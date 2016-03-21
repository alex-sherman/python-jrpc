
var jrpc = function(prefix) {
    var dff = $.Deferred()
    var reflection = {};
    function getURL(method, args) {
        var path = '/' + method.name;
        if ("path" in method.options) {
            var re = /<.+?>/g;
            function replacer(match, offset, string) {
                return args[match.substring(1, match.length - 1)];
            }
            path = method.options.path.replace(re, replacer);
        }
        return path;
    }
    function makeMethodCaller(prefix, method) {
        function methodCaller() {
            var args = {}
            if(arguments[0].constructor === Array) {
                var argArray = arguments[0];
                for(var i = 0; i < argArray.length && i < method.arguments.length; i++) {
                    args[method.arguments[i].name] = argArray[i];
                }
                if(arguments[1].constructor === Object) {
                    args = Object.assign(args, arguments[1]);
                }
            }
            else if(arguments[0].constructor === Object) {
                args = arguments[0];
            }
            return $.ajax({
                url: prefix + getURL(method, args),
                dataType: "json"
            });
        }
        return methodCaller;
    }
    $.getJSON(prefix + "/Reflect", function(data) {
        var jrpc = {}
        for(var methodName in data.methods) {
            var method = Object.assign(data.methods[methodName], {"name": methodName});
            jrpc[methodName] = makeMethodCaller(prefix, method);
        }
        dff.resolve(jrpc);
    });
    return dff;
}