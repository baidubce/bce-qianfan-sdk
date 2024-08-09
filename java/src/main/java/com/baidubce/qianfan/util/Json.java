/*
 * Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.baidubce.qianfan.util;

import com.google.gson.FieldNamingPolicy;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.lang.reflect.Type;

public class Json {
    private static final Gson GSON = new GsonBuilder()
            .setFieldNamingStrategy(field -> {
                JsonProp annotation = field.getAnnotation(JsonProp.class);
                if (annotation != null) {
                    return annotation.value();
                }
                return FieldNamingPolicy.LOWER_CASE_WITH_UNDERSCORES.translateName(field);
            })
            .create();

    private Json() {
    }

    public static String serialize(Object object) {
        return GSON.toJson(object);
    }

    public static <T> T deserialize(String json, TypeRef<T> typeRef) {
        return GSON.fromJson(json, typeRef.getType());
    }

    public static <T> T deserialize(String json, Class<T> clazz) {
        return GSON.fromJson(json, clazz);
    }

    public static <T> T deserialize(String json, Type type) {
        return GSON.fromJson(json, type);
    }
}
