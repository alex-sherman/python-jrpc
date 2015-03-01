cmake_minimum_required(VERSION 2.6)

# Add -DNDEBUG for release versions to ignore assert()s
set(CMAKE_C_FLAGS "-g -rdynamic -Wall -pedantic -std=c99 -D_POSIX_C_SOURCE=200809L")

# Include the common header files
include_directories(${CMAKE_CURRENT_BINARY_DIR})

add_library(libjrpc
    sockets.c
    jrpc.c
    message.c
)

target_link_libraries(libjrpc json)

add_executable(test
    test.c
)

target_link_libraries(test libjrpc)
