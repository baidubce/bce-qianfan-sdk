try:
    import semantic_kernel  # noqa F401
except ImportError:
    raise ImportError(
        "Could not import semantic_kernel python package. "
        "Please install it with `pip install semantic_kernel`."
    )

from qianfan.extensions.semantic_kernel.connectors.qianfan_chat_completion import (
    QianfanChatCompletion,
)
from qianfan.extensions.semantic_kernel.connectors.qianfan_settings import (
    QianfanChatRequestSettings,
    QianfanEmbeddingRequestSettings,
    QianfanRequestSettings,
    QianfanTextRequestSettings,
)
from qianfan.extensions.semantic_kernel.connectors.qianfan_text_completion import (
    QianfanTextCompletion,
)
from qianfan.extensions.semantic_kernel.connectors.qianfan_text_embedding import (
    QianfanTextEmbedding,
)

__all__ = [
    "QianfanChatCompletion",
    "QianfanTextCompletion",
    "QianfanTextEmbedding",
    "QianfanEmbeddingRequestSettings",
    "QianfanRequestSettings",
    "QianfanChatRequestSettings",
    "QianfanTextRequestSettings",
]
