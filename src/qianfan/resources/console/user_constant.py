class DataProjectType:
    """
    Project type used by Qianfan Data
    """
    Conversation: int = 20
    GenericText: int = 401
    QuerySet: int = 402
    Text2Speech: int = 705


class DataTemplateType:
    """
    Template type used by Qianfan Data
    """
    NonAnnotatedConversation: int = 2000
    AnnotatedConversation: int = 2001
    GenericText: int = 40100
    QuerySet: int = 40200
    Text2Speech: int = 70500


class DataSetType:
    TextOnly: int = 4
    MultiModel: int = 7


class DataStorageType:
    PublicBos: str = "sysBos"
    PrivateBos: str = "usrBos"


class DataSourceType:
    Local: int = 0
    PrivateBos: int = 1
    SharedZipUrl: int = 2


class DataZipInnerContentFormatType:
    Json: int = 2
    xml_voc: int = 3


class DataExportScene:
    Normal: int = 0
    Release: int = 1
