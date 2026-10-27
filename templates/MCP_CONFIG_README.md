# Non-runnable host-configuration shape

`muse_mcp.example.json` contains no secrets and is not a verified launch config. The application
module does not exist in this design ZIP. Confirm the installed Muse Code configuration syntax,
file location, interpreter and module after implementing the app. Official changelog support for
MCP does not certify every configuration or SDK version [S23].

Keep Meta credentials in the host, scientific-worker credentials in the worker/secret store, and
no evaluator labels in either environment. Run from the isolated runtime workspace. Do not copy
`.mcp.json` into a broad development workspace and assume a prompt blocks filesystem access.
