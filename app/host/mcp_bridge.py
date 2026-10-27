"""Official SDK bridge to an explicitly provisioned local stdio workspace."""
from contextlib import asynccontextmanager
import json
from pathlib import Path
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPBridge:
    def __init__(self,session):
        self.session=session

    async def list_allowed(self):
        result=await self.session.list_tools()
        return [{'name':t.name,'description':t.description or '', 'inputSchema':t.inputSchema} for t in result.tools]

    async def call(self,name,arguments):
        result=await self.session.call_tool(name,arguments)
        if result.structuredContent is not None:
            return result.structuredContent
        texts=[c.text for c in result.content if c.type=='text']
        if len(texts)!=1:
            return {'status':'blocked','reason':'invalid_mcp_result'}
        return json.loads(texts[0])

@asynccontextmanager
async def connect(bundle,db_path,run_id,owner_id,*,esm_env_file=None):
    args=['-m','app.mcp_server','--db',str(Path(db_path).resolve()),'--run-id',run_id,'--owner-id',owner_id]
    if esm_env_file is not None:
        args.extend(['--esm-env-file',str(Path(esm_env_file).resolve())])
    params=StdioServerParameters(command=sys.executable,
        args=args,
        cwd=str(Path(bundle).resolve()),env={'PYTHONNOUSERSITE':'0','PYTHONDONTWRITEBYTECODE':'1'})
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            initialized=await session.initialize()
            bridge=MCPBridge(session)
            bridge.protocol_version=initialized.protocolVersion
            yield bridge
