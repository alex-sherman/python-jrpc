#include "jrpc.h"
#include <arpa/inet.h>
#include <json/json.h>
#include <stdio.h>

int main() {
    struct jrpc_proxy *proxy = proxy_init("localhost", 8765);
    json_object *params = json_object_new_array();
    json_object_array_add(params, json_object_new_string("herp"));
    json_object * output = proxy_call(proxy, "echo", params);
    const char * outstr = json_object_to_json_string(output);
    printf("Output: %s\n", outstr);
    proxy_close(proxy);
    return 0;
}
