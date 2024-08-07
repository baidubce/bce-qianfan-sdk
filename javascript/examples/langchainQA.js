import { PuppeteerWebBaseLoader } from "@langchain/community/document_loaders/web/puppeteer";
import { RecursiveCharacterTextSplitter } from "langchain/text_splitter";
import { BaiduQianfanEmbeddings } from "@langchain/baidu-qianfan";
import { Chroma } from "@langchain/community/vectorstores/chroma";
import { ChromaClient } from 'chromadb'
import { createRetrievalChain } from "langchain/chains/retrieval";
import { createStuffDocumentsChain } from "langchain/chains/combine_documents";
import {ChatPromptTemplate} from "@langchain/core/prompts";
import { ChatBaiduQianfan } from "@langchain/baidu-qianfan";

//这是一个结合了langchain.js,qianfan,chroma， puppeteer 的应用
//此应用会对特定文档完成获取、切分、转为向量并存储，而后根据你的提问来从文中获取答案
const loader = new PuppeteerWebBaseLoader(" ", {
  evaluate: async (page) => {
    return await page.evaluate(() => document.body.innerText);
  }
});
//使用load和split完成对文本的加载和分割
try {
  const docs = await loader.load();
  // console.log(docs);
  const splitter = new RecursiveCharacterTextSplitter({
    chunkSize: 1000,
    chunkOverlap: 10,
  });
  const docOutput = await splitter.splitDocuments(docs);

const userEmbed = new BaiduQianfanEmbeddings({
    //aksk
  }); 
  const llm = new ChatBaiduQianfan({
   //aksk
    //model: "ERNIE-Bot-turbo",
  });
//进行提问
  const prompt = ChatPromptTemplate.fromTemplate(`请根据以下的文本进行回答:
    <context>{context}</context>
    Question: {input}
`);
//使用docker 进行连接，然后加入进collection
    const client = new ChromaClient();
    
    const collection = await client.getOrCreateCollection({
      name: "my_collection",
      metadata: {
        description: "My first collection"
      }
    });
    await collection.add({
      documents: docOutput.map(doc => doc.pageContent),//this is
      ids: docOutput.map((_, index) => `id${index}`),//this is needed
    });
    //进行整合
    const vectorStore = new Chroma(userEmbed, {
      url: 'http://0.0.0.0:8000', //数据库的url
      collectionName: 'my_collection',
    });

    const retriever = await vectorStore.asRetriever();
    const combineDocsChain = await createStuffDocumentsChain({
      llm,
      prompt,
  }
);

const retrievalChain = await createRetrievalChain({
  combineDocsChain,
  retriever,
});
const response = await retrievalChain.invoke({ input: "animalia" });
console.log(response);
} catch (error) {
  console.error("Error loading the page:", error);
}


