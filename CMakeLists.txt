cmake_minimum_required(VERSION 2.6)

# Add -DNDEBUG for release versions to ignore assert()s
set(CMAKE_C_FLAGS "-g -rdynamic -Wall -pedantic -std=c99 -D_POSIX_C_SOURCE=200809L -DDEBUG_PRINT")

# Include the common header files
include_directories(${CMAKE_CURRENT_BINARY_DIR})
add_subdirectory(${CMAKE_CURRENT_BINARY_DIR}/test)

add_library(jrpc SHARED
    debug.c
    sockets.c
    jrpc_proxy.c
    jrpc_server.c
    message.c
)
target_include_directories (jrpc PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
install (FILES jrpc.h DESTINATION include)
target_link_libraries(jrpc json)

install (TARGETS jrpc
         ARCHIVE DESTINATION lib
         LIBRARY DESTINATION lib)