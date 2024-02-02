try:
    import langchain  # noqa F401
except ImportError:
    raise ImportError(
        "Could not import langchain python package. "
        "Please install it with `pip install langchain`."
    )
