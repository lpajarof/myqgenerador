import os
import tempfile

from langchain_markitdown import (
    DocxLoader,
    ImageLoader,
    PdfLoader,
    PptxLoader,
    XlsxLoader,
)

# Loader de langchain-markitdown a usar según la extensión del archivo subido
# en el panel "Cargar caso de negocio" (Agente 2).
LOADERS_POR_EXTENSION = {
    ".pdf": PdfLoader,
    ".docx": DocxLoader,
    ".pptx": PptxLoader,
    ".xlsx": XlsxLoader,
    ".png": ImageLoader,
    ".jpg": ImageLoader,
    ".jpeg": ImageLoader,
    ".gif": ImageLoader,
    ".bmp": ImageLoader,
    ".webp": ImageLoader,
}

EXTENSIONES_SOPORTADAS = tuple(LOADERS_POR_EXTENSION.keys())


def extraer_texto_de_archivo(nombre_archivo: str, contenido: bytes) -> str:
    """Convierte un PDF, imagen, DOCX, PPTX o XLSX a texto Markdown usando
    langchain-markitdown, para poblar el cuadro de texto que se envía al
    Agente 2 (business_case_agent).

    MarkItDown solo sabe leer desde una ruta de archivo, así que el
    contenido subido se vuelca a un archivo temporal antes de convertirlo.
    """
    extension = os.path.splitext(nombre_archivo)[1].lower()
    loader_cls = LOADERS_POR_EXTENSION.get(extension)
    if loader_cls is None:
        raise ValueError(
            f"Formato no soportado: {extension or '(sin extensión)'}. "
            f"Usa uno de estos formatos: {', '.join(EXTENSIONES_SOPORTADAS)}."
        )

    with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as tmp:
        tmp.write(contenido)
        ruta_temporal = tmp.name

    try:
        documentos = loader_cls(ruta_temporal).load()
        return "\n\n".join(doc.page_content for doc in documentos if doc.page_content).strip()
    finally:
        # En Windows, algunos loaders (p. ej. XlsxLoader con openpyxl en modo
        # read_only) dejan el archivo abierto más allá del load(); no dejamos
        # que un fallo de limpieza tumbe la respuesta ya calculada.
        try:
            os.remove(ruta_temporal)
        except OSError:
            pass


__all__ = ["extraer_texto_de_archivo", "EXTENSIONES_SOPORTADAS"]
