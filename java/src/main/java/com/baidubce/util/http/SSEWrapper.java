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

package com.baidubce.util.http;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.Iterator;
import java.util.NoSuchElementException;

public class SSEWrapper {
    private SSEWrapper() {
    }

    public static Iterator<String> wrap(InputStream stream, AutoCloseable closeable) {
        return new Iterator<String>() {
            final BufferedReader reader = new BufferedReader(new InputStreamReader(stream));
            String nextLine = null;

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

            private void silentlyClose() {
                try {
                    closeable.close();
                } catch (Exception ignored) {
                }
            }
        };
    }
}
