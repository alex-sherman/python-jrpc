#include "sockets.h"
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

#include "debug.h"

#define BLOCKING 0
#define NONBLOCKING 1

const static struct addrinfo build_sockaddr_hints = {
    .ai_family = AF_INET6,
    .ai_flags = AI_NUMERICSERV | AI_V4MAPPED | AI_ADDRCONFIG,
};

const static struct addrinfo build_sockaddr_hints_fallback = {
    .ai_family = AF_INET,
    .ai_flags = AI_NUMERICSERV | AI_V4MAPPED,
};

int jrpc_build_sockaddr(const char* ip, unsigned short port, struct sockaddr_storage* dest)
{
    assert(ip && dest);

    struct addrinfo* results = 0;
    int err;

    char *serv = NULL;
    char serv_buffer[16];
    if(port > 0) {
        snprintf(serv_buffer, sizeof(serv_buffer), "%hu", port);
        serv = serv_buffer;
    }

    err = getaddrinfo(ip, serv, &build_sockaddr_hints_fallback, &results);
    if(err != 0) {
        DEBUG_ONCE("getaddrinfo failed - host: %s port: %hu reason: %s", 
                ip, port, gai_strerror(err));

        /* TODO: There seems to be a problem with the AI_ADDRCONFIG option on
         * some systems.  This fallback code is in here to make sure the system
         * will run anyway, but we should try to understand this problem
         * better. */
        err = getaddrinfo(ip, serv, &build_sockaddr_hints_fallback, &results);
        if(err != 0) {
            DEBUG_MSG("getaddrinfo fallback failed - host: %s port: %hu reason: %s", 
                    ip, port, gai_strerror(err));
            return FAILURE;
        }
    }

    if(err != 0) {
        DEBUG_MSG("Failed to convert IP address %s: %s", ip, gai_strerror(err));
        return FAILURE;
    }

    memset(dest, 0, sizeof(*dest));
    memcpy(dest, results->ai_addr, results->ai_addrlen);
    freeaddrinfo(results);

    return results->ai_addrlen;
}

/*
 * TCP PASSIVE OPEN
 *
 * local_port should be in host byte order.
 * Returns a valid socket file descriptor or -1 on failure.
 */
int jrpc_tcp_passive_open(unsigned short local_port, int backlog)
{
    int sockfd = -1;

    sockfd = socket(PF_INET6, SOCK_STREAM, IPPROTO_TCP);
    if(sockfd < 0) {
        ERROR_MSG("failed creating socket");
        return -1;
    }

    // Prevent bind from failing in case the program was restarted.
    const int yes = 1;
    if(setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) < 0) {
        DEBUG_MSG("SO_REUSEADDR failed");
        close(sockfd);
        return -1;
    }

    char portString[16];
    snprintf(portString, sizeof(portString), "%d", local_port);

    struct addrinfo hints;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET6;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags = AI_V4MAPPED | AI_NUMERICHOST | AI_PASSIVE;

    struct addrinfo* results = 0;
    int ret = getaddrinfo(0, portString, &hints, &results);
    if(ret != 0) {
        DEBUG_MSG("getaddrinfo() failed: %s", gai_strerror(ret));
        close(sockfd);
        return -1;
    }
    
    // If getaddrinfo completed successfully, these pointers should not be
    // null, so this assert should never be triggered
    assert(results != 0 && results->ai_addr != 0);

    if(bind(sockfd, results->ai_addr, results->ai_addrlen) < 0) {
        ERROR_MSG("failed binding socket");
        goto free_and_return;
    }

    if(listen(sockfd, backlog) < 0) {
        ERROR_MSG("failed to listen on socket");
        goto free_and_return;
    }
   
    freeaddrinfo(results);
    return sockfd;

free_and_return:
    freeaddrinfo(results);
    close(sockfd);
    return -1;
}

/*
 * SET NONBLOCK
 *
 * enable should be non-zero to set or 0 to clear.
 * Returns 0 on success or -1 on failure.
 */
int set_nonblock(int sockfd, int enable)
{
    int flags;

    flags = fcntl(sockfd, F_GETFL, 0);
    if(flags == -1) {
        perror("fcntl F_GETFL failed");
        return -1;
    }

    if(enable && !(flags & O_NONBLOCK)) {
        flags = flags | O_NONBLOCK;
        if(fcntl(sockfd, F_SETFL, flags) == -1) {
            perror("fcntl F_SETFL failed");
            return -1;
        }
    } else if(!enable && (flags & O_NONBLOCK)) {
        flags = flags & ~O_NONBLOCK;
        if(fcntl(sockfd, F_SETFL, flags) == -1) {
            perror("fcntl F_SETFL failed");
            return -1;
        }
    }

    return 0;
}

extern int jrpc_tcp_active_open(struct sockaddr_storage* dest, const char *device, struct timeval *timeout)
{
    int sockfd;
    int rtn;

    sockfd = socket(dest->ss_family, SOCK_STREAM, IPPROTO_TCP);
    if(sockfd < 0) {
        goto free_and_return;
    }
    
    if(device) {
        // Bind socket to device
        if(setsockopt(sockfd, SOL_SOCKET, SO_BINDTODEVICE, device, IFNAMSIZ) < 0) {
            /* TODO: The bind will fail with EACCES if we are running as an
             * unprivileged user.  In that case, we should try to achieve the
             * same result by binding to the interface's address. */
            goto free_and_return;
        }
    }

    if(timeout)
        set_nonblock(sockfd, NONBLOCKING);
    

    if(timeout) {
        fd_set write_set;
        FD_ZERO(&write_set);
        FD_SET(sockfd, &write_set);

        // sockfd will become writable if connect finishes before timeout
        rtn = select(sockfd + 1, 0, &write_set, 0, timeout);
        if(rtn < 0) {
            goto close_and_return;
        } else if(rtn == 0) {
            goto close_and_return;
        }

        set_nonblock(sockfd, BLOCKING);
    }
    
    rtn = connect(sockfd, (struct sockaddr*)dest, sizeof(struct sockaddr));
    if(rtn == -1 && errno != EINPROGRESS) {
        goto close_and_return;
    }
    return sockfd;

close_and_return:
    close(sockfd);
free_and_return:
    return -1;
}


int jrpc_read_from_socket(int sockfd, char *buffer, int size)
{
    int bytes_read = 0;
    int ret;
    while(bytes_read < size)
    {
        ret = read(sockfd, buffer + bytes_read, size - bytes_read);
        if(ret < 1){
            return -1;
        }
        bytes_read += ret;
    }
    return 0;
}