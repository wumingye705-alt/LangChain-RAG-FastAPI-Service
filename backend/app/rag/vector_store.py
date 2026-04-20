import asyncio
import sys
import os
import tempfile
import json
import hashlib
import shutil
from datetime import datetime

from langchain_classic.retrievers import EnsembleRetriever

# 将根目录添加到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import aiofiles
from aiofiles import os as aio_os

from langchain_chroma import Chroma
from langchain_core.documents import Document
from app.rag.text_spliter import AsyncTextSplitter
from langchain_community.retrievers import BM25Retriever

from app.utils.config import chroma_config
from app.utils.factory import embed_model
from app.utils.file_handler import pdf_loader, txt_loader, listdir_allowed_type, get_file_md5_hex, markdown_loader, \
    ppt_loader, word_loader
from app.core.logger_handler import logger
from app.utils.path_tool import get_abstract_path

class VectorStoreService:
    """向量数据库服务"""
    def __init__(self):
        persist_dir = get_abstract_path(chroma_config['persist_directory'])
        # 使用同步 Chroma, 在调用时用 to_thread 包裹
        self.vectors_store = Chroma(
            collection_name=chroma_config['collection_name'],
            embedding_function=embed_model,
            persist_directory=persist_dir,
        )
        self.spliter = AsyncTextSplitter(
            chunk_size=chroma_config['chunk_size'],
            chunk_overlap=chroma_config['chunk_overlap'],
            separators=chroma_config['separators'],
            embedding_model=embed_model
        )

    def _user_upload_dir(self, user_id: str) -> str:
        safe_user_id = "".join(ch for ch in str(user_id) if ch.isalnum() or ch in ("-", "_"))
        return get_abstract_path(os.path.join("data", "uploads", safe_user_id))

    def _user_registry_path(self, user_id: str) -> str:
        return os.path.join(self._user_upload_dir(user_id), "files.json")

    async def _read_user_registry(self, user_id: str) -> list[dict]:
        registry_path = self._user_registry_path(user_id)
        if not await aio_os.path.exists(registry_path):
            return []
        async with aiofiles.open(registry_path, "r", encoding="utf-8") as f:
            raw = await f.read()
        if not raw.strip():
            return []
        try:
            data = json.loads(raw)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

    async def _write_user_registry(self, user_id: str, files: list[dict]) -> None:
        upload_dir = self._user_upload_dir(user_id)
        await aio_os.makedirs(upload_dir, exist_ok=True)
        async with aiofiles.open(self._user_registry_path(user_id), "w", encoding="utf-8") as f:
            await f.write(json.dumps(files, ensure_ascii=False, indent=2))

    async def save_uploaded_file_record(self, user_id: str, record: dict) -> None:
        files = await self._read_user_registry(user_id)
        files = [item for item in files if item.get("file_id") != record.get("file_id")]
        files.insert(0, record)
        await self._write_user_registry(user_id, files)

    async def list_user_files(self, user_id: str) -> list[dict]:
        files = await self._read_user_registry(user_id)
        return [
            {key: value for key, value in item.items() if key != "stored_path"}
            for item in files
        ]

    async def get_user_file_record(self, user_id: str, file_id: str) -> dict | None:
        files = await self._read_user_registry(user_id)
        for item in files:
            if item.get("file_id") == file_id:
                stored_path = item.get("stored_path")
                if stored_path and await aio_os.path.exists(stored_path):
                    return item
        return None

    async def clear_user_files(self, user_id: str) -> None:
        upload_dir = self._user_upload_dir(user_id)
        if await aio_os.path.exists(upload_dir):
            await asyncio.to_thread(shutil.rmtree, upload_dir, True)

    async def get_bm25_retriever(self):
        """
        获取BM25检索器
        :return: BM25Retriever实例
        """
        # 从文件直接加载文档，不依赖向量数据库
        allowed_file_path: tuple[str] = await listdir_allowed_type(
            chroma_config['data_path'],
            tuple(chroma_config['allow_knowledge_file_types'])
        )
        file_paths = list(allowed_file_path)
        
        all_docs = []
        for file_path in file_paths:
            documents = await self.get_file_document(file_path)
            if documents:
                split_docs = await self.spliter.split_documents(documents)
                all_docs.extend(split_docs)
        
        # 创建BM25检索器
        if all_docs:
            bm25_retriever = BM25Retriever.from_documents(
                documents=all_docs,
                k=chroma_config['k']
            )
            return bm25_retriever
        else:
            return None

    async def _get_all_documents(self) -> list[Document]:
        """
        获取向量库中的所有文档
        :return: 文档列表
        """
        # 使用同步操作获取所有文档
        all_docs = await asyncio.to_thread(
            self.vectors_store.get,
            include=['documents', 'metadatas']
        )
        # 构建Document对象列表
        documents = []
        for i, doc in enumerate(all_docs['documents']):
            metadata = all_docs['metadatas'][i] if i < len(all_docs['metadatas']) else {}
            documents.append(Document(page_content=doc, metadata=metadata))
        return documents

    async def get_retriever(self, query: str = None, user_id: str = None):
        """
        获取混合检索器（BM25 + 向量检索）
        :param query: 查询语句，用于动态调整权重
        :return: EnsembleRetriever实例或单独的向量检索器
        """
        # 创建向量检索器
        search_kwargs = {'k': chroma_config['k']}
        if user_id:
            search_kwargs['filter'] = {"user_id": user_id}

        vector_retriever = self.vectors_store.as_retriever(
            search_type='similarity',
            search_kwargs=search_kwargs,
        )
        if user_id:
            return vector_retriever
        # 创建BM25检索器
        bm25_retriever = await self.get_bm25_retriever()
        
        # 根据是否有BM25检索器决定返回哪种检索器
        if bm25_retriever:
            # 获取动态权重
            weights = await self.get_dynamic_weights(query)
            # 创建混合检索器
            ensemble_retriever = EnsembleRetriever(
                retrievers=[vector_retriever, bm25_retriever],
                weights=weights
            )
            return ensemble_retriever
        else:
            # 如果没有BM25检索器，只返回向量检索器
            return vector_retriever

    @staticmethod
    async def get_dynamic_weights(query: str = None):
        """
        根据查询动态调整权重
        :param query: 查询语句
        :return: 权重列表 [向量检索权重, BM25检索权重]
        """
        # 默认权重
        default_vector_weight = 0.5
        default_bm25_weight = 0.5
        
        if not query:
            return [default_vector_weight, default_bm25_weight]
        
        # 根据查询特征调整权重
        query_length = len(query)
        query_words = len(query.split())
        
        # 长查询（>50字符）更适合向量检索
        if query_length > 50:
            vector_weight = 0.7
            bm25_weight = 0.3
        # 短查询（<20字符）更适合BM25检索
        elif query_length < 20:
            vector_weight = 0.3
            bm25_weight = 0.7
        # 中等长度查询使用默认权重
        else:
            vector_weight = default_vector_weight
            bm25_weight = default_bm25_weight
        
        # 关键词密集的查询（词数/长度比例高）更适合BM25
        if query_words > 0:
            word_density = query_words / query_length
            if word_density > 0.1:
                bm25_weight = min(bm25_weight + 0.1, 0.7)
                vector_weight = max(vector_weight - 0.1, 0.3)
        
        return [vector_weight, bm25_weight]

    async def check_md5_hex(self, md5_for_check: str) -> bool:
        """异步检查md5"""
        md5_path = get_abstract_path(chroma_config['md5_hex_store'])
        # 确保目录存在
        md5_dir = os.path.dirname(md5_path)
        if not await aio_os.path.exists(md5_dir):
            await aio_os.makedirs(md5_dir, exist_ok=True)
        if not await aio_os.path.exists(md5_path):
            async with aiofiles.open(md5_path, 'w', encoding="utf-8"):
                pass
            return False

        async with aiofiles.open(md5_path, 'r', encoding="utf-8") as f:
            async for line in f:
                if line.strip() == md5_for_check:
                    return True
            return False

    async def save_md5_hex(self, md5_hex: str):
        """异步保存md5"""
        async with aiofiles.open(get_abstract_path(chroma_config['md5_hex_store']), 'a', encoding="utf-8") as f:
            await f.write(md5_hex + '\n')

    async def delete_user_documents(self, user_id: str):
        """
        删除指定用户的所有文档
        :param user_id: 用户ID
        """
        try:
            # 使用同步操作删除文档
            await asyncio.to_thread(
                self.vectors_store.delete, 
                where={"user_id": user_id}
            )
            logger.info(f"【向量数据库】已删除用户 {user_id} 的所有文档")
        except Exception as e:
            logger.error(f"【向量数据库】删除用户 {user_id} 的文档时出错: {e}")
            raise

    async def get_file_document(self, read_path: str) -> list[Document]:
        """异步加载文件"""
        if read_path.endswith('.txt'):
            return await txt_loader(read_path)
        elif read_path.endswith('.pdf'):
            return await pdf_loader(read_path)
        elif read_path.endswith('.md'):
            return await markdown_loader(read_path)
        elif read_path.endswith('.pptx'):
            return await ppt_loader(read_path)
        elif read_path.endswith('.docx'):
            return await word_loader(read_path)
        else:
            return []

    async def get_document(self, files: list = None, user_id: str = None):
        """
        处理文档并将其转为向量存入向量数据库
        :param files: 上传的文件列表，如果为None则从数据文件夹读取
        :param user_id: 用户ID，用于标记文档的所有者
        """
        # 确定要处理的文件列表
        file_paths = []
        upload_records_by_path = {}
        if files:
            # 处理上传的文件
            for file in files:
                # 创建临时文件，使用asyncio.to_thread 包裹
                content = await file.read()
                original_filename = os.path.basename(file.filename or "upload")
                md5_hex = hashlib.md5(content).hexdigest()
                extension = os.path.splitext(original_filename)[1]
                stored_filename = f"{md5_hex[:16]}{extension}"
                upload_dir = self._user_upload_dir(user_id or "anonymous")
                await aio_os.makedirs(upload_dir, exist_ok=True)
                stored_path = os.path.join(upload_dir, stored_filename)
                async with aiofiles.open(stored_path, "wb") as f:
                    await f.write(content)
                file_paths.append(stored_path)
                upload_records_by_path[stored_path] = {
                    "file_id": md5_hex,
                    "filename": original_filename,
                    "stored_filename": stored_filename,
                    "stored_path": stored_path,
                    "download_url": f"/api/vector/files/{md5_hex}",
                    "size": len(content),
                    "indexed": False,
                    "uploaded_at": datetime.now().isoformat(timespec="seconds"),
                }
        else:
            # 从数据文件夹读取文件
            allowed_file_path: tuple[str] = await listdir_allowed_type(
                chroma_config['data_path'],
                tuple(chroma_config['allow_knowledge_file_types'])
            )
            file_paths = list(allowed_file_path)

        for file_path in file_paths:
            # 2. 计算MD5
            md5_hex = await get_file_md5_hex(file_path)
            md5_key = f"{user_id}:{md5_hex}" if files and user_id else md5_hex
            upload_record = upload_records_by_path.get(file_path)
            if upload_record and user_id:
                await self.save_uploaded_file_record(user_id, upload_record)

            if await self.check_md5_hex(md5_key):
                if upload_record and user_id:
                    upload_record["indexed"] = True
                    await self.save_uploaded_file_record(user_id, upload_record)
                logger.info(f"【向量数据库】文件 {file_path} 的md5值 {md5_hex} 已存在，跳过")
                # 如果是临时文件，删除
                if files and file_path not in upload_records_by_path:
                    try:
                        os.unlink(file_path)
                    except:
                        pass
                continue

            try:
                # 3. 加载文档
                document: list[Document] = await self.get_file_document(file_path)
                if not document:
                    logger.error(f"【向量数据库】文件 {file_path} 加载内容为空，跳过")
                    # 如果是临时文件，删除
                    if files and file_path not in upload_records_by_path:
                        try:
                            os.unlink(file_path)
                        except Exception as e:
                            pass
                    continue

                # 4. 切分文档
                document: list[Document] = await self.spliter.split_documents(document)
                if not document:
                    logger.error(f"【向量数据库】文件 {file_path} 切分内容为空，跳过")
                    # 如果是临时文件，删除
                    if files and file_path not in upload_records_by_path:
                        try:
                            os.unlink(file_path)
                        except:
                            pass
                    continue

                # 5. 添加用户ID作为元数据
                if user_id:
                    for doc in document:
                        doc.metadata['user_id'] = user_id
                        if upload_record:
                            doc.metadata['file_id'] = upload_record["file_id"]
                            doc.metadata['source_filename'] = upload_record["filename"]
                            doc.metadata['stored_filename'] = upload_record["stored_filename"]
                            doc.metadata['uploaded_at'] = upload_record["uploaded_at"]

                # 6. 异步写入向量库
                await asyncio.to_thread(self.vectors_store.add_documents, document)
                if upload_record and user_id:
                    upload_record["indexed"] = True
                    await self.save_uploaded_file_record(user_id, upload_record)

                # 6. 保存MD5
                await self.save_md5_hex(md5_key)
                logger.info(f"【向量数据库】文件 {file_path} 的md5值 {md5_hex} 已保存")

                # 如果是临时文件，删除
                if files and file_path not in upload_records_by_path:
                    try:
                        os.unlink(file_path)
                    except:
                        pass

            except Exception as e:
                logger.error(f"【向量数据库】文件 {file_path} 处理时出错: {e}")
                # 如果是临时文件，删除
                if files and file_path not in upload_records_by_path:
                    try:
                        os.unlink(file_path)
                    except:
                        pass
                continue


if __name__ == '__main__':
    async def main():
        store = VectorStoreService()
        await store.get_document()

        # 等待get_retriever方法完成
        retriever = await store.get_retriever()
        # 直接使用ainvoke方法，因为EnsembleRetriever的invoke可能返回协程
        results = await retriever.ainvoke('扫地')
        print(f"检索结果数量: {len(results)}")
        for result in results:
            print(result)

    asyncio.run(main())
