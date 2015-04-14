#include "jrpc.h"
#include <arpa/inet.h>
#include <json/json.h>
#include <stdio.h>

int main() {
    struct jrpc_proxy *proxy = jrpc_proxy_init("localhost", 8765);
    if(jrpc_proxy_call(proxy, "echo", "p", "{'herp': 'lawl'}"))
    {
        printf("Error\n");
        exit(1);
    }
    const char * outstr = json_object_to_json_string(proxy->result);
    printf("Output: %s\n", outstr);
    jrpc_proxy_close(proxy);
    return 0;
}
