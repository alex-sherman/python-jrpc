#include <jrpc.h>
#include "debug.h"

json_object *echo(json_object *params)
{
    DEBUG_MSG("Called echo!");
    return json_object_array_get_idx(params, 0);
}

int main(int argc, char *argv[])
{
    struct jrpc_server *server = jrpc_server_init(8765);
    jrpc_server_register(server, echo, "echo");
    jrpc_server_run(server);
    assert(server);
    return 0;
}