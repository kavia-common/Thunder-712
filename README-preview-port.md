Thunder-712 preview port configuration

- The preview system expects Thunder to listen on 0.0.0.0:3001.
- This repository now provides a default PluginHost.json at Thunder-712/PluginHost.json forcing:
  - interface: 0.0.0.0
  - port: 3001
- If your environment prefers an environment variable, set PORT=3001 and ensure your launch scripts pass it to Thunder’s process and generate or override PluginHost.json accordingly.
- Health endpoint:
  - Thunder Controller plugin is enabled by default; preview health checks typically use a Controller route such as /Service/Controller or JSON-RPC at /jsonrpc depending on the orchestrator.
