#ifndef JRPC_MESSAGE_H_
#define JRPC_MESSAGE_H_

json_object *jrpc_init_message(int id);
int jrpc_message_send(int sockfd, json_object * jobj);
json_object *jrpc_read_message(int sockfd);
json_object *jrpc_new_request(int id, const char *method);

#endif //JRPC_MESSAGE_H_