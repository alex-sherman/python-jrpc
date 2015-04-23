#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <json/json.h>
#include <arpa/inet.h>

#include "sockets.h"
#include "debug.h"
#include <unistd.h>

json_object *jrpc_init_message(int id)
{
    json_object *output = json_object_new_object();
    json_object *j_id = json_object_new_int(id);
    json_object *jsonrpc = json_object_new_string("2.0");
    json_object_object_add(output, "id", j_id);
    json_object_object_add(output, "jsonrpc", jsonrpc);
    return output;
}

int jrpc_message_send(int sockfd, json_object * jobj)
{
    int rtn = 0;
    const char * jstr = json_object_to_json_string(jobj);
    uint32_t jlength = strlen(jstr);
    uint32_t n_jlength = htonl(jlength);
    if(write(sockfd, &n_jlength, sizeof(n_jlength)) < sizeof(n_jlength))
    {
        rtn = -1;
        goto free_return;
    }
    if(write(sockfd, jstr, jlength) < jlength)
    {
        rtn = -1;
    }

free_return:
    if(rtn == -1)
        ERROR_MSG("Message send");
    return rtn;
}

json_object *jrpc_read_message(int sockfd)
{
    uint32_t jlength;
    jrpc_read_from_socket(sockfd, (char *)&jlength, sizeof(jlength));
    jlength = ntohl(jlength);
    char buffer[jlength + +1];
    memset(buffer, 0, jlength + 1);
    jrpc_read_from_socket(sockfd, buffer, jlength);
    json_object * response = json_tokener_parse(buffer);
    return response;
}

json_object *jrpc_new_request(int id, const char *method)
{
    json_object *request = json_object_new_object();
    json_object_object_add(request, "id", json_object_new_int(id));
    json_object_object_add(request, "jsonrpc", json_object_new_string("2.0"));
    json_object_object_add(request, "method", json_object_new_string(method));
    return request;
}