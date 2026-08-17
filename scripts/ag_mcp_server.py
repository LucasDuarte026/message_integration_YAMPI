import os
import sys
import asyncio
from typing import Optional, List, Dict, Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
)
from qdrant_client import QdrantClient

app = Server("ag-local-rag-server-qdrant")

def search_index(project_dir: str, query: str, top_k: int = 5) -> str:
    db_path = os.path.join(project_dir, '.agents', 'local_index', 'qdrant_db')
    if not os.path.exists(db_path):
        return f"Error: No Qdrant DB found at {db_path}. Run the indexer first."
        
    try:
        client = QdrantClient(path=db_path)
        collection_name = "project_knowledge"
        
        from qdrant_client.models import Document
        # client.query_points automatically converts the query text to embedding via fastembed 
        search_result = client.query_points(
            collection_name=collection_name,
            query=Document(
                text=query,
                model="sentence-transformers/all-MiniLM-L6-v2"
            ),
            limit=top_k
        ).points

        
        if not search_result:
            return "No relevant context found in the local vector DB."
            
        response = f"Found {len(search_result)} semantically relevant nodes for query '{query}':\n\n"
        for hit in search_result:
            meta = hit.metadata
            title = meta.get('title', 'Unknown')
            rel_path = meta.get('relative_path', 'Unknown')
            node_type = meta.get('type', 'Unknown')
            score = round(hit.score, 4)
            
            response += f"--- {title} (Similarity Score: {score}) ---\n"
            response += f"Path: {rel_path}\n"
            response += f"Type: {node_type}\n\n"
            
            snippet = meta.get('chunk_text', '')[:700]
            response += f"Snippet:\n{snippet}...\n\n"
            
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        return f"Error executing semantic search: {e}"

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="search_project_context",
            description="Semantic search the local project knowledge graph (Vector DB) for context. Used to understand system rules and project-specific skills before taking action.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query or intent to look up (e.g., 'email state machine', 'how to review python', 'version control rules')."
                    },
                    "project_dir": {
                        "type": "string",
                        "description": "Absolute path to the current project workspace."
                    }
                },
                "required": ["query", "project_dir"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a tool."""
    if name == "search_project_context":
        query = arguments.get("query")
        project_dir = arguments.get("project_dir")
        
        if not query or not project_dir:
            return [TextContent(type="text", text="Error: query and project_dir are required.")]
            
        result = search_index(project_dir, query)
        return [TextContent(type="text", text=result)]
        
    raise ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
