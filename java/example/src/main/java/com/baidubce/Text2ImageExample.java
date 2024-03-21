package com.baidubce;

import com.baidubce.qianfan.Qianfan;
import com.baidubce.qianfan.model.image.Text2ImageResponse;

import java.io.FileOutputStream;
import java.io.IOException;

/**
 * 本示例实现了Text2Image调用流程，并将生成的图片保存到本地
 */
public class Text2ImageExample {
    public static void main(String[] args) throws IOException {
        Qianfan qianfan = new Qianfan();
        Text2ImageResponse response = qianfan.text2Image()
                .prompt("cute cat")
                .execute();
        byte[] rawImage = response.getData().get(0).getImage();
        try (FileOutputStream fos = new FileOutputStream("cute_cat.png")) {
            fos.write(rawImage);
        }
    }
}
