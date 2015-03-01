#include "jrpc.h"
#include "sockets.h"
#include "message.h"

#include <stdlib.h>
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <errno.h>
#include <linux/if.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <json/json.h>

struct jrpc_proxy *proxy_init(char *host, uint16_t port)
{
    struct jrpc_proxy *output = (struct jrpc_proxy *)malloc(sizeof(struct jrpc_proxy));
    memset(output, 0, sizeof(struct jrpc_proxy));

    ((struct sockaddr_in*)&output->remote)->sin_family = AF_INET;
    ((struct sockaddr_in*)&output->remote)->sin_port = htons(port);
    inet_pton(AF_INET, host, &(((struct sockaddr_in*)&output->remote)->sin_addr));
    output->sockfd = tcp_active_open(&output->remote, NULL, NULL);
    return output;
}
int proxy_close(struct jrpc_proxy *proxy)
{
    if(proxy->sockfd)
        close(proxy->sockfd);
    return 0;
}
struct json_object *proxy_call(struct jrpc_proxy *proxy, const char *method_name, json_object* parameters)
{
    if(proxy == NULL || proxy->sockfd == 0) return NULL;
    json_object *request = new_request(proxy->next_id++, method_name);
    json_object_object_add(request, "params", parameters);
    char buffer[4096];
    int length = serialize_message(request, buffer, 4096);
    write(proxy->sockfd, buffer, length);
    json_object *response = read_message(proxy->sockfd);
    return json_object_object_get(response, "result");
}