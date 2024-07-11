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

package com.baidubce.qianfan.util.http;

import java.io.*;
import java.util.Iterator;
import java.util.NoSuchElementException;

public class SSEIterator implements Iterator<String>, Closeable {
    private final BufferedReader reader;
    private final AutoCloseable closeable;
    private String nextLine = null;

    public SSEIterator(InputStream stream, AutoCloseable closeable) {
        this.reader = new BufferedReader(new InputStreamReader(stream));
        this.closeable = closeable;
    }

    @Override
    public boolean hasNext() {
        if (nextLine != null) {
            return true;
        }
        try {
            nextLine = reader.readLine();
            if (nextLine == null) {
                silentlyClose();
            }
            return nextLine != null;
        } catch (Exception e) {
            silentlyClose();
            return false;
        }
    }

    @Override
    public String next() {
        if (nextLine != null || hasNext()) {
            String lineToReturn = nextLine;
            nextLine = null;
            return lineToReturn;
        } else {
            silentlyClose();
            throw new NoSuchElementException();
        }
    }

    @Override
    public void close() throws IOException {
        try {
            closeable.close();
        } catch (Exception e) {
            throw new IOException("Failed to close sseIterator", e);
        }
    }

    public void silentlyClose() {
        try {
            closeable.close();
        } catch (Exception ignored) {
            // ignored
        }
    }
}
