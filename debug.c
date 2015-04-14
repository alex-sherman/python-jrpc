#include <errno.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <sys/time.h>
#include <execinfo.h>
#include <signal.h>

#include "debug.h"

/*
 * PRINT TIME
 */
void print_time(FILE* out)
{
    struct timeval now;
    struct tm broken;

    gettimeofday(&now, 0);
    localtime_r(&now.tv_sec, &broken);

    fprintf(out, "%d/%02d/%02d %02d:%02d:%02d.%06d", broken.tm_mon+1, broken.tm_mday,
            broken.tm_year+1900, broken.tm_hour, broken.tm_min, broken.tm_sec, (int)now.tv_usec);
}

#ifdef DEBUG_PRINT
void __debug_msg(const char* file, int line, const char* func, const char* msg, ...)
{
    print_time(stdout);

    va_list args;
    char buffer[MAX_DEBUG_LEN];

    va_start(args, msg);
    vsnprintf(buffer, sizeof(buffer), msg, args);
    va_end(args);
    
    const char* split_file = strrchr(file, '/');
    if(!split_file) {
        // It was not a full path
        split_file = file;
    } else {
        // Ignore the leading '/'
        split_file++;
    }

    printf("\t%s (line %d): %s() -- %s\n", split_file, line, func, buffer);
    fflush(stdout);
}

void __error_msg(const char* file, int line, const char* func, const char* msg, ...)
{
    print_time(stdout);
    
    va_list args;
    char buffer[MAX_DEBUG_LEN];

    va_start(args, msg);
    vsnprintf(buffer, sizeof(buffer), msg, args);
    va_end(args);

    const char* split_file = strrchr(file, '/');
    if(!split_file) {
        // It was not a full path
        split_file = file;
    } else {
        // Ignore the leading '/'
        split_file++;
    }

    printf("\tERROR_MSG: %s (line %d): %s() -- %s: %s - Error #(%d)\n", split_file,
           line, func, buffer, strerror(errno), errno);
    fflush(stdout);
}
#endif //DEBUG_PRINT

void __print_warning(const char *msg, ...)
{
    print_time(stdout);
    
    va_list args;
    char buffer[MAX_DEBUG_LEN];

    va_start(args, msg);
    vsnprintf(buffer, sizeof(buffer), msg, args);
    va_end(args);

    printf("\tWarning: %s\n", buffer);
    fflush(stdout);
}

void print_backtrace(FILE *out)
{
    void* ptrs[MAX_BACKTRACE_LEN];
    int nptrs = backtrace(ptrs, MAX_BACKTRACE_LEN);

    char** symbols;
    symbols = backtrace_symbols(ptrs, nptrs);
    if(!symbols) {
        perror("backtrace_symbols");
        return;
    }

    fprintf(out, "Backtrace:\n");

    int i;
    for(i = 0; i < nptrs; i++) {
        fprintf(out, "%2d %s\n", i, symbols[i]);
    }

    free(symbols);
}

void segfault_handler(int signo)
{
    if(signo == SIGSEGV) {
        print_backtrace(stderr);
        exit(1);
    }
}
