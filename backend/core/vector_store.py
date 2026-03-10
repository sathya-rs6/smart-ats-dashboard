"""
Vector Store Module
Handles different vector store implementations for the Resume Analyzer.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from langchain.embeddings.base import Embeddings
from langchain.schema.document import Document
from langchain.vectorstores.base import VectorStore

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """Manages different vector store implementations"""
    
    def __init__(self, embeddings: Embeddings):
        self.embeddings = embeddings
        self.vector_store = None
        
    def initialize_vector_store(
        self,
        store_type: str = "chroma",
        collection_name: str = "resume_collection",
        **kwargs
    ) -> VectorStore:
        """Initialize the vector store based on the specified type.
        
        Args:
            store_type: Type of vector store to use (chroma, weaviate, faiss)
            collection_name: Name of the collection/index to use
            **kwargs: Additional arguments for the vector store
            
        Returns:
            Initialized vector store instance
        """
        store_type = store_type.lower()
        
        if store_type == "chroma":
            self.vector_store = self._init_chroma(collection_name, **kwargs)
        elif store_type == "weaviate":
            self.vector_store = self._init_weaviate(collection_name, **kwargs)
        elif store_type == "faiss":
            self.vector_store = self._init_faiss(collection_name, **kwargs)
        else:
            raise ValueError(f"Unsupported vector store type: {store_type}")
            
        logger.info(f"Initialized {store_type} vector store")
        return self.vector_store
    
    def _init_chroma(
        self, 
        collection_name: str,
        persist_directory: Optional[str] = None,
        **kwargs
    ) -> VectorStore:
        """Initialize ChromaDB vector store"""
        try:
            try:
                from langchain_chroma import Chroma
            except ImportError:
                from langchain_community.vectorstores import Chroma
            
            if persist_directory:
                persist_path = Path(persist_directory)
                persist_path.mkdir(parents=True, exist_ok=True)
                
            return Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=persist_directory,
                **kwargs
            )
        except ImportError as e:
            logger.error("ChromaDB not installed. Install with: pip install chromadb")
            raise
            
    def _init_weaviate(
        self, 
        collection_name: str,
        weaviate_url: Optional[str] = None,
        weaviate_api_key: Optional[str] = None,
        **kwargs
    ) -> VectorStore:
        """Initialize Weaviate vector store"""
        try:
            import weaviate
            from weaviate.classes.init import Auth
            try:
                from langchain_weaviate.vectorstores import WeaviateVectorStore
            except ImportError:
                from langchain_community.vectorstores import Weaviate as WeaviateVectorStore
            
            if not weaviate_url or not weaviate_api_key:
                raise ValueError("Weaviate URL and API key are required")
                
            client = weaviate.connect_to_weaviate_cloud(
                cluster_url=weaviate_url,
                auth_credentials=Auth.api_key(weaviate_api_key),
                **kwargs
            )
            
            if not client.is_ready():
                raise ConnectionError("Failed to connect to Weaviate")
                
            return WeaviateVectorStore(
                client=client,
                index_name=collection_name,
                text_key="text",
                embedding=self.embeddings,
                by_text=False
            )
            
        except ImportError as e:
            logger.error("Weaviate client not installed. Install with: pip install weaviate-client")
            raise
            
    def _init_faiss(
        self,
        index_name: str,
        persist_directory: Optional[str] = None,
        **kwargs
    ) -> VectorStore:
        """Initialize FAISS vector store"""
        try:
            from langchain_community.vectorstores import FAISS
            
            if persist_directory:
                persist_path = Path(persist_directory)
                persist_path.mkdir(parents=True, exist_ok=True)
                
                # Check if index exists
                index_file = persist_path / "index.faiss"
                if index_file.exists():
                    return FAISS.load_local(
                        folder_path=str(persist_path),
                        embeddings=self.embeddings,
                        index_name=index_name,
                        **kwargs
                    )
                    
            # Create new index
            return FAISS.from_texts(
                texts=[""],  # Empty document to initialize
                embedding=self.embeddings,
                **kwargs
            )
            
        except ImportError as e:
            logger.error("FAISS not installed. Install with: pip install faiss-cpu")
            raise
            
    def add_documents(self, documents: List[Document], **kwargs) -> List[str]:
        """Add documents to the vector store"""
        if not self.vector_store:
            raise ValueError("Vector store not initialized. Call initialize_vector_store() first.")
            
        return self.vector_store.add_documents(documents, **kwargs)
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 4, 
        **kwargs
    ) -> List[Document]:
        """Perform similarity search"""
        if not self.vector_store:
            raise ValueError("Vector store not initialized. Call initialize_vector_store() first.")
            
        return self.vector_store.similarity_search(query, k=k, **kwargs)
    
    def save_local(self, persist_directory: str, **kwargs) -> None:
        """Save the vector store to disk"""
        if not self.vector_store:
            raise ValueError("Vector store not initialized. Call initialize_vector_store() first.")
            
        if hasattr(self.vector_store, 'save_local'):
            persist_path = Path(persist_directory)
            persist_path.mkdir(parents=True, exist_ok=True)
            self.vector_store.save_local(folder_path=str(persist_path), **kwargs)
        else:
            logger.warning("This vector store does not support local persistence")
            
    @classmethod
    def load_local(
        cls,
        persist_directory: str,
        embeddings: Embeddings,
        store_type: str = "chroma",
        **kwargs
    ) -> 'VectorStoreManager':
        """Load a vector store from disk"""
        manager = cls(embeddings)
        manager.initialize_vector_store(store_type=store_type, **kwargs)
        
        # For FAISS, we need to handle loading differently
        if store_type == "faiss":
            from langchain_community.vectorstores import FAISS
            persist_path = Path(persist_directory)
            manager.vector_store = FAISS.load_local(
                folder_path=str(persist_path),
                embeddings=embeddings,
                **kwargs
            )
            
        return manager


def create_vector_store(
    documents: List[Document],
    embeddings: Embeddings,
    store_type: str = "chroma",
    collection_name: str = "resume_collection",
    persist_directory: Optional[str] = None,
    **kwargs
) -> VectorStoreManager:
    """Helper function to create and populate a vector store"""
    manager = VectorStoreManager(embeddings)
    manager.initialize_vector_store(
        store_type=store_type,
        collection_name=collection_name,
        persist_directory=persist_directory,
        **kwargs
    )
    
    if documents:
        manager.add_documents(documents)
        if persist_directory and hasattr(manager.vector_store, 'persist'):
            manager.vector_store.persist()
            
    return manager
