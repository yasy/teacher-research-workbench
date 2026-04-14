class AppError(Exception):
    pass


class LLMConfigError(AppError):
    pass


class PDFParseError(AppError):
    pass


class ExportError(AppError):
    pass
