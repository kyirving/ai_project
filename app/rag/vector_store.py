import os
import shutil
import app.utils.config as config
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_core.documents import Document

# 尝试导入向量库
try:
    import chromadb
    from langchain_chroma import Chroma
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False

try:
    from langchain_community.vectorstores import FAISS
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False

class MeetingKnowledgeBase:
    def __init__(self, persist_dir="./data/vector_store"):
        self.persist_dir = persist_dir
        self.store_type = None # "chroma" or "faiss"
        self.vector_store = None
        
        # 1. 初始化 Embedding 模型
        print("📚 正在加载向量模型 (FastEmbed)")
        model_name = config.FASTEMBED_MODEL_DIR or "BAAI/bge-small-zh-v1.5"
        self.embedding_fn = FastEmbedEmbeddings(model_name=model_name)
        
        # 2. 尝试初始化向量库
        self._init_vector_store()

    def _init_vector_store(self):
        """
        初始化向量库。
        当 VECTOR_STORE=chroma 时强制使用 Chroma；
        当 VECTOR_STORE=faiss 时强制使用 FAISS；
        当 VECTOR_STORE=auto 时优先 Chroma，失败则降级 FAISS。
        """
        pref = getattr(config, "VECTOR_STORE", "auto")
        if pref == "chroma":
            if not HAS_CHROMA:
                print("❌ 未安装 ChromaDB 或 langchain-chroma")
                return
            try:
                print("尝试初始化 ChromaDB...")
                chroma_dir = os.path.join(self.persist_dir, "chroma")
                self.vector_store = Chroma(
                    persist_directory=chroma_dir,
                    embedding_function=self.embedding_fn,
                    collection_name="meeting_records"
                )
                self.store_type = "chroma"
                print(f"✅ ChromaDB 初始化成功: {chroma_dir}")
                return
            except Exception as e:
                print(f"❌ ChromaDB 初始化失败: {e}")
                return
        
        if pref == "faiss":
            if not HAS_FAISS:
                print("❌ 未安装 FAISS")
                return
            try:
                print("尝试初始化 FAISS...")
                faiss_dir = os.path.join(self.persist_dir, "faiss")
                if os.path.exists(faiss_dir):
                    self.vector_store = FAISS.load_local(
                        faiss_dir, 
                        self.embedding_fn,
                        allow_dangerous_deserialization=True
                    )
                    print(f"🗄️  加载现有 FAISS 索引: {faiss_dir}")
                else:
                    print("🆕 FAISS 索引将会在第一次添加数据时创建")
                    self.vector_store = None
                self.store_type = "faiss"
                print("✅ FAISS 模式已启用")
                return
            except Exception as e:
                print(f"❌ FAISS 初始化失败: {e}")
                return
        
        # auto 模式：优先 Chroma，失败则降级 FAISS
        if HAS_CHROMA:
            try:
                print("尝试初始化 ChromaDB...")
                chroma_dir = os.path.join(self.persist_dir, "chroma")
                self.vector_store = Chroma(
                    persist_directory=chroma_dir,
                    embedding_function=self.embedding_fn,
                    collection_name="meeting_records"
                )
                self.store_type = "chroma"
                print(f"✅ ChromaDB 初始化成功: {chroma_dir}")
                return
            except Exception as e:
                print(f"⚠️ ChromaDB 初始化失败 ({e})，尝试降级到 FAISS...")
        
        if HAS_FAISS:
            try:
                print("尝试初始化 FAISS...")
                faiss_dir = os.path.join(self.persist_dir, "faiss")
                if os.path.exists(faiss_dir):
                    self.vector_store = FAISS.load_local(
                        faiss_dir, 
                        self.embedding_fn,
                        allow_dangerous_deserialization=True
                    )
                    print(f"🗄️  加载现有 FAISS 索引: {faiss_dir}")
                else:
                    print("🆕 FAISS 索引将会在第一次添加数据时创建")
                    self.vector_store = None
                self.store_type = "faiss"
                print("✅ FAISS 模式已启用")
                return
            except Exception as e:
                print(f"❌ FAISS 初始化失败: {e}")
                return
        
        print("❌ 无法初始化任何向量库 (请检查 requirements.txt)")

    def add_meeting(self, summary, transcript, metadata=None):
        """
        将会议纪要存入知识库
        """
        if metadata is None:
            metadata = {}
            
        doc = Document(
            page_content=summary,
            metadata=metadata
        )
        
        if self.store_type == "chroma":
            self.vector_store.add_documents([doc])
            print("✅ [Chroma] 会议记录已存入")
            
        elif self.store_type == "faiss":
            faiss_dir = os.path.join(self.persist_dir, "faiss")
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents([doc], self.embedding_fn)
            else:
                self.vector_store.add_documents([doc])
            # FAISS 需要手动保存
            self.vector_store.save_local(faiss_dir)
            print("✅ [FAISS] 会议记录已存入并保存")
        else:
            print("❌ 向量库未初始化，无法存储")

    def search(self, query, k=3):
        """
        语义搜索
        """
        if self.vector_store is None:
            return []
        
        try:
            results = self.vector_store.similarity_search(query, k=k)
            return results
        except Exception as e:
            print(f"搜索出错: {e}")
            return []

    def query_with_llm(self, query, llm):
        """
        RAG: 检索 + 生成回答
        """
        if self.vector_store is None:
            return "知识库为空，无法回答。"
            
        # 1. 检索相关文档
        docs = self.search(query)
        if not docs:
            return "未找到相关信息。"
            
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # 2. 构造 Prompt
        prompt = f"""
        基于以下历史会议记录回答问题。如果不知道，就说不知道。
        
        --- 历史记录 ---
        {context}
        --- 结束 ---
        
        问题: {query}
        回答:
        """
        
        # 3. 调用 LLM
        return llm.invoke(prompt).content
