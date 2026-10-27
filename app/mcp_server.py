"""BioPilot local stdio MCP server. The trusted launcher binds one owner/run.

No network listener, model API, arbitrary resources or file/shell tools.
"""
import argparse
import asyncio
import json
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from app.core.tool_executor import SessionContext, ToolExecutor

def create_server(executor: ToolExecutor) -> Server:
    server = Server('biopilot-atlas', version='0.1.0')

    @server.list_tools()
    async def list_tools():
        return [types.Tool(**tool) for tool in executor.list_tools()]

    @server.call_tool(validate_input=False)
    async def call_tool(name, arguments):
        result = executor.dispatch(name, arguments)
        return types.CallToolResult(
            content=[types.TextContent(type='text', text=json.dumps(result))],
            structuredContent=result, isError=result['status'] == 'blocked')

    @server.list_resources()
    async def list_resources():
        return []

    return server

def configured_executor(context, esm_settings=None):
    """Load selected launcher configuration; default remote settings stay blocked."""
    settings = None
    try:
        from app.science.provider_config import load_esm_settings, make_inference_service
        settings = esm_settings if esm_settings is not None else load_esm_settings()
        service = make_inference_service(context,settings)
        service.ensure_ready()
        return ToolExecutor(context,inference_service=service,
            backend_status={'status':'configured','backend':settings['ESM_BACKEND'],
                            'model_key':settings['ESM_MODEL_KEY']})
    except (ValueError,RuntimeError,ImportError):
        return ToolExecutor(context,backend_status={'status':'unconfigured',
            'backend':settings.get('ESM_BACKEND') if settings is not None else None,
            'code':'esm_backend_unconfigured'})

async def serve(context: SessionContext, esm_settings=None):
    server = create_server(configured_executor(context,esm_settings))
    async with stdio_server() as streams:
        await server.run(*streams, server.create_initialization_options())

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--owner-id', required=True)
    parser.add_argument('--esm-env-file',type=Path,
        help='Trusted launcher settings file; only named ESM settings are selected, never uploaded')
    args = parser.parse_args(argv)
    if not args.db.is_absolute() or not args.db.is_file():
        parser.error('--db must name the existing absolute trusted run database')
    settings = None
    if args.esm_env_file is not None:
        from app.science.provider_config import load_esm_settings
        settings = load_esm_settings(args.esm_env_file)
    asyncio.run(serve(SessionContext(args.db, args.run_id, args.owner_id),settings))

if __name__ == '__main__':
    main()
