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

package com.baidubce.qianfan.core;

import com.baidubce.qianfan.model.BaseResponse;
import com.baidubce.qianfan.model.plugin.PluginMetaInfo;
import com.baidubce.qianfan.model.plugin.PluginResponse;
import com.baidubce.qianfan.util.Json;
import com.baidubce.qianfan.util.http.SSEIterator;

import java.io.Closeable;
import java.util.Iterator;
import java.util.Map;
import java.util.Objects;
import java.util.function.Consumer;

public class StreamIterator<T extends BaseResponse<T>> implements Iterator<T>, Closeable {
    private final Map<String, String> headers;
    private final SSEIterator sseIterator;
    private final Class<T> responseClass;

    private PluginMetaInfo metaInfo;

    public StreamIterator(Map<String, String> headers, SSEIterator sseIterator, Class<T> responseClass) {
        this.headers = headers;
        this.sseIterator = sseIterator;
        this.responseClass = responseClass;
    }

    @Override
    public boolean hasNext() {
        return sseIterator.hasNext();
    }

    @Override
    @SuppressWarnings("unchecked")
    public T next() {
        String event = sseIterator.next().replaceFirst("data: ", "");
        // Skip sse empty line
        sseIterator.next();
        T response = Json.deserialize(event, responseClass);

        // Set meta info for PluginResponse
        if (responseClass.equals(PluginResponse.class)) {
            if (metaInfo == null) {
                metaInfo = Json.deserialize(event, PluginMetaInfo.class);
            }
            ((PluginResponse) response).setMetaInfo(metaInfo);
        }

        return (T) response.setHeaders(headers);
    }

    @Override
    public void forEachRemaining(Consumer<? super T> action) {
        Objects.requireNonNull(action);
        try {
            while (hasNext()) {
                action.accept(next());
            }
        } finally {
            sseIterator.silentlyClose();
        }
    }

    @Override
    public void close() {
        sseIterator.silentlyClose();
    }
}
