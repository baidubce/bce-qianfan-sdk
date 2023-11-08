from enum import Enum


class DataProjectType(int, Enum):
    """
    Project type used by Qianfan Data
    """

    Conversation: int = 20
    GenericText: int = 401
    QuerySet: int = 402
    Text2Speech: int = 705


class DataTemplateType(int, Enum):
    """
    Template type used by Qianfan Data
    """

    NonAnnotatedConversation: int = 2000
    AnnotatedConversation: int = 2001
    GenericText: int = 40100
    QuerySet: int = 40200
    Text2Speech: int = 70500


class DataSetType(int, Enum):
    TextOnly: int = 4
    MultiModel: int = 7


class DataStorageType(str, Enum):
    PublicBos: str = "sysBos"
    PrivateBos: str = "usrBos"


class DataSourceType(int, Enum):
    Local: int = 0
    PrivateBos: int = 1
    SharedZipUrl: int = 2


class DataZipInnerContentFormatType(int, Enum):
    Json: int = 2
    xml_voc: int = 3


class DataExportScene(int, Enum):
    Normal: int = 0
    Release: int = 1
