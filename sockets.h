#ifndef _SOCKETS_H_
#define _SOCKETS_H_
#include <sys/time.h>
#include <sys/socket.h>

extern int tcp_active_open(struct sockaddr_storage* dest, const char *device, struct timeval *timeout);
int read_from_socket(int sockfd, char *buffer, int size);
#endif //_SOCKETS_H_
