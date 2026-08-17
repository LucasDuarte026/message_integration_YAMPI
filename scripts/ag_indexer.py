import os
import argparse
import glob
import re
from typing import List, Dict, Any
from qdrant_client import QdrantClient, models

def parse_yaml_frontmatter(content: str) -> tuple[Dict[str, str], str]:
    """Parses simple YAML frontmatter from a markdown string."""
    frontmatter = {}
    body = content
    
    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    if match:
        yaml_text = match.group(1)
        body = match.group(2)
        
        for line in yaml_text.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if ':' in line:
                key, val = line.split(':', 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                frontmatter[key] = val
                
    return frontmatter, body

def chunk_text(text: str, max_chars: int = 2000) -> List[str]:
    """Basic chunking to avoid embedding overly huge text blocks."""
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = ""
    
    for p in paragraphs:
        if len(current_chunk) + len(p) < max_chars:
            current_chunk += "\n\n" + p
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = p
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    if not chunks:
        chunks = [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
        
    return chunks

def scan_directory(base_dir: str, sub_dir: str, file_pattern: str = '**/*.md') -> List[Dict[str, Any]]:
    """Scans a directory for files and returns structured dictionaries."""
    results = []
    target_dir = os.path.join(base_dir, sub_dir)
    
    if not os.path.exists(target_dir):
        print(f"Directory {target_dir} not found. Skipping...")
        return results

    search_pattern = os.path.join(target_dir, file_pattern)
    for filepath in glob.glob(search_pattern, recursive=True):
        if not os.path.isfile(filepath):
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            title_match = re.search(r'^#\s+(.+)', content, re.MULTILINE)
            title = title_match.group(1) if title_match else os.path.basename(filepath)
            
            frontmatter, body = parse_yaml_frontmatter(content)
            if 'name' in frontmatter:
                title = frontmatter['name']
                
            results.append({
                'filepath': filepath,
                'relative_path': os.path.relpath(filepath, base_dir),
                'type': sub_dir,
                'title': title,
                'frontmatter': frontmatter,
                'content': body
            })
            print(f"Read: {filepath}")
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            
    return results

def main():
    parser = argparse.ArgumentParser(description='Antigravity Global Vector RAG Indexer (Qdrant)')
    parser.add_argument('--project-dir', required=True, help='Path to the local project root')
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    if not os.path.isdir(project_dir):
        print(f"Error: {project_dir} is not a valid directory.")
        return

    print(f"Starting Vector Index generation for project: {project_dir}")
    
    scan_targets = [
        '.agents',
        'docs'
    ]
    
    all_nodes = []
    for target in scan_targets:
        nodes = scan_directory(project_dir, target)
        all_nodes.extend(nodes)
        
    print(f"\nExtracted {len(all_nodes)} files. Chunking and Embedding...")
    
    db_path = os.path.join(project_dir, '.agents', 'local_index', 'qdrant_db')
    os.makedirs(db_path, exist_ok=True)
    
    client = QdrantClient(path=db_path)
    
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    
    collection_name = "project_knowledge"
    
    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)
    
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=client.get_embedding_size(model_name),
            distance=models.Distance.COSINE
        )
    )
    
    payloads = []
    texts = []
    
    for node in all_nodes:
        chunks = chunk_text(node['content'])
        for chunk in chunks:
            desc = node['frontmatter'].get('description', '')
            embedding_text = f"Title: {node['title']}\nDescription: {desc}\n\nContent:\n{chunk}"
            
            texts.append(embedding_text)
            payloads.append({
                "title": node['title'],
                "relative_path": node['relative_path'],
                "type": node['type'],
                "chunk_text": chunk
            })

    if not texts:
        print("No documents found to index.")
        return

    print(f"Total chunks to embed: {len(texts)}. Calling FastEmbed model...")
    
    docs = [models.Document(text=t, model=model_name) for t in texts]

    client.upload_collection(
        collection_name=collection_name,
        vectors=docs,
        payload=payloads
    )
    
    print(f"\nSuccessfully generated Vector Index at {db_path}")

if __name__ == '__main__':
    main()
