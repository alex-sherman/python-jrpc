#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <json/json.h>
#include <arpa/inet.h>

#include "sockets.h"

int jrpc_serialize_message(json_object * jobj, char * buffer, int size)
{
    const char * jstr = json_object_to_json_string(jobj);
    int jlength = strnlen(jstr, size);
    *(int *)buffer = htonl(jlength);
    memcpy(&buffer[4], jstr, jlength);
    return jlength + 4;
}

json_object *jrpc_read_message(int sockfd)
{
    char buffer[4097];
    jrpc_read_from_socket(sockfd, buffer, 4);
    int jlength = ntohl(*(int *)buffer);
    memset(buffer, 0, 4097);
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