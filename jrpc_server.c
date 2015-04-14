#include <errno.h>
#include <unistd.h>

#include "jrpc.h"
#include "debug.h"
#include "message.h"
#include "sockets.h"

struct jrpc_server *jrpc_server_init(uint16_t port)
{
    struct jrpc_server * server = malloc(sizeof(struct jrpc_server));
    server->listen_sockfd = tcp_passive_open(port, 0);
    server->client_sockfd = 0;
    server->running = 0;
    server->methods = NULL;
    if(server->listen_sockfd == FAILURE){
        return NULL;
    }

    return server;
}

void jrpc_server_run(struct jrpc_server * server)
{
    server->running = 1;
    int result;
    fd_set read_set;
    while(server->running)
    {
        FD_ZERO(&read_set);
        if(server->client_sockfd != 0)
        {
            FD_SET(server->client_sockfd, &read_set);
        }
        else
        {
            FD_SET(server->listen_sockfd, &read_set);
        }
        struct timespec timeout;
        timeout.tv_sec = 0;
        timeout.tv_nsec = 500 * 1000000;
        result = pselect(FD_SETSIZE, &read_set, NULL, NULL, &timeout, NULL);
        if(result == -1) {
            if(errno != EINTR) {
                ERROR_MSG("select failed");
                return;
            }
        }
        else if (result == 0)
        {
            //Time out occurs
        }
        else //result was greater than 0
        {
            if(server->client_sockfd != 0)
            {
                if(FD_ISSET(server->client_sockfd, &read_set))
                {
                    json_object *message = read_message(server->client_sockfd);
                    json_object *obj;
                    const char *method_name;
                    if(!json_object_object_get_ex(message, "method", &obj))
                        goto client_error;
                    method_name = json_object_get_string(obj);
                    if(!json_object_object_get_ex(message, "params", &obj))
                        goto client_error;
                    struct jrpc_server_method *method;
                    HASH_FIND_STR(server->methods, method_name, method);
                    if(method != NULL)
                    {
                        json_object *response_message = json_object_new_object();

                        obj = method->function(obj);
                        json_object_object_add(response_message, "result", obj);

                        char buffer[1024];
                        serialize_message(response_message, buffer, sizeof(buffer));
                        write(server->client_sockfd, buffer, sizeof(buffer));
                    }
                    else
                    {
                        DEBUG_MSG("Method not found: %s", method_name);
                    }
client_error:
                    close(server->client_sockfd);
                    server->client_sockfd = 0;
                }
            }
            else if(FD_ISSET(server->listen_sockfd, &read_set)) {
                DEBUG_MSG("Responding to client");

                struct sockaddr addr;
                socklen_t addr_size = sizeof(addr);

                server->client_sockfd = accept(server->listen_sockfd, &addr, &addr_size);
                if(server->client_sockfd == -1) {
                    ERROR_MSG("accept() failed");
                    return;
                }
            }
        }
    }
}

int jrpc_server_register(struct jrpc_server *server, jrpc_function func, char *name)
{
    struct jrpc_server_method * method = malloc(sizeof(struct jrpc_server_method));
    memcpy(method->name, name, sizeof(method->name));
    method->function = func;
    HASH_ADD_STR(server->methods, name, method);
    return SUCCESS;
}