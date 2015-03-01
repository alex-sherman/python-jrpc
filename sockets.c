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

#define BLOCKING 0
#define NONBLOCKING 1

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

extern int tcp_active_open(struct sockaddr_storage* dest, const char *device, struct timeval *timeout)
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


int read_from_socket(int sockfd, char *buffer, int size)
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