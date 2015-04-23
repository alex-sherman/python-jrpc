#include "jrpc.h"
#include "sockets.h"
#include "message.h"

#include <stdarg.h>
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

struct jrpc_proxy *jrpc_proxy_init(char *host, uint16_t port)
{
    struct jrpc_proxy *output = (struct jrpc_proxy *)malloc(sizeof(struct jrpc_proxy));
    memset(output, 0, sizeof(struct jrpc_proxy));

    ((struct sockaddr_in*)&output->remote)->sin_family = AF_INET;
    ((struct sockaddr_in*)&output->remote)->sin_port = htons(port);
    inet_pton(AF_INET, host, &(((struct sockaddr_in*)&output->remote)->sin_addr));
    output->sockfd = jrpc_tcp_active_open(&output->remote, NULL, NULL);
    return output;
}
int jrpc_proxy_close(struct jrpc_proxy *proxy)
{
    if(proxy->sockfd)
        close(proxy->sockfd);
    return 0;
}
int jrpc_proxy_call(struct jrpc_proxy *proxy, const char *method_name, const char *param_format, ...)
{
    if(proxy == NULL || proxy->sockfd == 0) return -1;
    json_object *request = jrpc_new_request(proxy->next_id++, method_name);

    va_list arg;
    va_start(arg, param_format);
    int param_length = strlen(param_format);
    json_object *parameters = json_object_new_array();
    for(int i = 0; i < param_length; i++)
    {
        switch(param_format[i])
        {
            case 'j':
                json_object_array_add(parameters, va_arg(arg, json_object *));
                break;
            case 'p':
                json_object_array_add(parameters, json_tokener_parse(va_arg(arg, const char *)));
                break;
            case 's':
                json_object_array_add(parameters, json_object_new_string(va_arg(arg, const char*)));
                break;
            case 'd':
                json_object_array_add(parameters, json_object_new_int(va_arg(arg, int)));
                break;
            case 'f':
                json_object_array_add(parameters, json_object_new_double(va_arg(arg, double)));
                break;
            default:
                break;
        }
    }
    va_end(arg);

    //TODO: Handle malformed parmeters
    json_object_object_add(request, "params", parameters);
    jrpc_message_send(proxy->sockfd, request);
    json_object_put(request);
    json_object *response = jrpc_read_message(proxy->sockfd);
    if(json_object_object_get_ex(response, "result", &proxy->result))
    {
        return 0;
    }
    return -1;
}