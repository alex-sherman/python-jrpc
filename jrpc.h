#ifndef _JRPC_H_
#define _JRPC_H_

#include <stdlib.h>
#include <sys/socket.h>
#include <stdint.h>
#include <string.h>
#include <json/json.h>
#include "uthash.h"

struct jrpc_proxy
{
    struct sockaddr_storage remote;
    json_object *result;
    int sockfd;
    int next_id;
};

struct jrpc_server
{
    int listen_sockfd;
    struct jrpc_server_method *methods;
    volatile int running;
    int client_sockfd;
};

typedef json_object *(*jrpc_function)(json_object *);

struct jrpc_server_method
{
    char name[10];
    jrpc_function function;
    UT_hash_handle hh;
};

struct jrpc_server *jrpc_server_init(uint16_t port);
int jrpc_server_register(struct jrpc_server *server, jrpc_function func, char *name);
void jrpc_server_run(struct jrpc_server *server);

struct jrpc_proxy *jrpc_proxy_init(char *host, uint16_t port);
int jrpc_proxy_close(struct jrpc_proxy *proxy);
int jrpc_proxy_call(struct jrpc_proxy *proxy, const char *method_name, const char *parameters, ...);

#endif //_JRPC_H_