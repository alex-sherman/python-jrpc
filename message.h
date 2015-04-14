#ifndef _MESSAGE_H_
#define _MESSAGE_H_

int jrpc_serialize_message(json_object * jobj, char * buffer, int size);
json_object *jrpc_read_message(int sockfd);
json_object *jrpc_new_request(int id, const char *method);

#endif //_MESSAGE_H_