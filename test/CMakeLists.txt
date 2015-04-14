
add_executable(test_proxy
    test_proxy.c
)

target_link_libraries(test_proxy jrpc)

add_executable(test_server
    test_server.c
)

target_link_libraries(test_server jrpc)
