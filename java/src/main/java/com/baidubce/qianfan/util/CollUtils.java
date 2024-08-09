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

import java.util.*;

public class CollUtils {

    private CollUtils() {
    }

    public static <K, V> Map<K, V> mapOf(Object... keyValues) {
        if (keyValues.length % 2 != 0) {
            throw new IllegalArgumentException("Invalid key-value pairs");
        }

        Map<K, V> map = new LinkedHashMap<>();
        for (int i = 0; i < keyValues.length; i += 2) {
            @SuppressWarnings("unchecked")
            K key = (K) keyValues[i];
            @SuppressWarnings("unchecked")
            V value = (V) keyValues[i + 1];
            if (key == null) {
                throw new IllegalArgumentException("Key at index " + i + " is null");
            }
            map.put(key, value);
        }
        return map;
    }

    @SafeVarargs
    public static <T> List<T> listOf(T... values) {
        List<T> list = new ArrayList<>();
        Collections.addAll(list, values);
        return list;
    }

    @SafeVarargs
    public static <T> T[] arrayOf(T... values) {
        return values;
    }

    @SafeVarargs
    public static <T> Set<T> setOf(T... values) {
        Set<T> set = new LinkedHashSet<>();
        Collections.addAll(set, values);
        return set;
    }
}
