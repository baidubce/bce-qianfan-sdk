# Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
utilities of data insight
"""
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, BinaryIO, Callable, Dict, Generator, List

from qianfan.dataset import Dataset

column_field_template = """
      {{
        title: `{0}`,
        dataIndex: `{0}`,
        key: `{0}`,
      }},
"""

top_half_html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ant Design Table Example</title>
  <!-- 引入 Ant Design 的 CSS 文件 -->
  <link rel="stylesheet" href="https://cdn.bootcdn.net/ajax/libs/antd/4.18.0/antd.min.css">
</head>
<body>
  <!-- 定义一个容器用于渲染表格 -->
  <div id="app"></div>

  <!-- 引入 Ant Design 的 JavaScript 文件 -->
  <script src="https://cdn.bootcdn.net/ajax/libs/react/17.0.2/umd/react.production.min.js"></script>
  <script src="https://cdn.bootcdn.net/ajax/libs/react-dom/17.0.2/umd/react-dom.production.min.js"></script>
  <script src="https://cdn.bootcdn.net/ajax/libs/babel-standalone/6.26.0/babel.min.js"></script>
  <script src="https://cdn.bootcdn.net/ajax/libs/antd/4.18.0/antd.min.js"></script>

  <!-- 定义表格的列和数据 -->
  <script type="text/babel">
    const { Table } = antd;


"""

bottom_half_html = """

    // 在容器中渲染表格
    ReactDOM.render(
      <Table columns={columns} dataSource={data} />,
      document.getElementById('app')
    );
  </script>
</body>
</html>
"""


def _get_generator(iteration_list: List[Dict[str, Any]], func: Callable) -> Generator:
    for single in iteration_list:
        yield func(single)


def open_html_in_browser(ds: Dataset) -> None:
    """
    Display Dataset in a web browser without creating a temp file.

    Instantiates a trivial http server and uses the webbrowser module to
    open a URL to retrieve html from that server.

    Args:
        ds (Dataset):
            Dataset need to be displayed
    """

    def _write_columns_field(bio: BinaryIO) -> None:
        bio.write(bytes("\t\tconst columns = [\n", encoding="utf8"))
        bio.write(bytes(column_field_template.format("index"), encoding="utf8"))
        for field in ds.col_names():
            bio.write(bytes(column_field_template.format(field), encoding="utf8"))
        bio.write(bytes("\t\t];\n", encoding="utf8"))

    def _write_column_data(bio: BinaryIO) -> None:
        bio.write(bytes("\t\tconst data = [\n", encoding="utf8"))
        index = 0

        def _iterate(entry: Dict[str, Any], **kwargs: Any) -> None:
            nonlocal index
            index += 1

            bio.write(bytes("\t\t\t{\n", encoding="utf8"))

            bio.write(bytes("\t\t\t\tkey: `{}`,\n".format(index), encoding="utf8"))
            bio.write(bytes("\t\t\t\tindex: `{}`,\n".format(index), encoding="utf8"))
            for k, v in entry.items():
                bio.write(bytes("\t\t\t\t{}: `{}`,\n".format(k, v), encoding="utf8"))

            bio.write(bytes("\t\t\t},\n", encoding="utf8"))

        ds.iterate(_iterate)
        bio.write(bytes("\t\t];\n", encoding="utf8"))

    browser = webbrowser.get(None)

    class OneShotRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            self.wfile.write(bytes(top_half_html, encoding="utf8"))
            _write_columns_field(self.wfile)
            _write_column_data(self.wfile)
            self.wfile.write(bytes(bottom_half_html, encoding="utf8"))

    server = HTTPServer(("127.0.0.1", 0), OneShotRequestHandler)
    browser.open("http://127.0.0.1:%s" % server.server_port)

    server.handle_request()
