package com.baidubce;

import com.baidubce.qianfan.Qianfan;
import com.baidubce.qianfan.model.embedding.EmbeddingData;
import com.baidubce.qianfan.model.embedding.EmbeddingResponse;

import java.math.BigDecimal;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 本示例实现了Embedding调用流程，并通过余弦相似度计算两个字符串的相似度
 */
public class EmbeddingExample {
    public static void main(String[] args) {
        String textA = "晚上的饭挺不错的";
        String textB = "晚上的饭挺好吃的";

        Qianfan qianfan = new Qianfan();
        EmbeddingResponse response = qianfan.embedding()
                .model("Embedding-V1")
                .input(Arrays.asList(textA, textB))
                .execute();
        List<EmbeddingData> embeddingData = response.getData();
        List<Double> vectorA = convertToDoubleVector(embeddingData.get(0).getEmbedding());
        List<Double> vectorB = convertToDoubleVector(embeddingData.get(1).getEmbedding());

        // 计算余弦相似度
        double similarity = calculateCosineSimilarity(vectorA, vectorB);
        System.out.format("[%s]和[%s]的相似度是[%f]", textA, textB, similarity);
    }

    private static double calculateCosineSimilarity(List<Double> vectorA, List<Double> vectorB) {
        double dotProduct = 0.0;
        double normA = 0.0;
        double normB = 0.0;

        for (int i = 0; i < vectorA.size(); i++) {
            dotProduct += vectorA.get(i) * vectorB.get(i);
            normA += Math.pow(vectorA.get(i), 2);
            normB += Math.pow(vectorB.get(i), 2);
        }

        if (normA == 0 || normB == 0) {
            return 0;
        }

        return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
    }

    private static List<Double> convertToDoubleVector(List<BigDecimal> list) {
        return list.stream().map(BigDecimal::doubleValue).collect(Collectors.toList());
    }
}
