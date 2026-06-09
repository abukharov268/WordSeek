from collections.abc import Mapping
from collections import deque

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from bs4.element import NavigableString, Tag

import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


class XmlNodeVisitor:
    def __init__(self) -> None:
        self._nstack = deque[Tag]()

    def visit(self, xml: str) -> None:
        doc = BeautifulSoup(xml, "html.parser")
        self._nstack.clear()
        self._nstack.append(doc)
        self.visit_children()
        self._nstack.clear()

    def visit_tag(self, tag: str, attrs: Mapping[str, str]) -> None:
        self.visit_children()

    def visit_children(self) -> None:
        if not self._nstack:
            return
        for node in self._nstack[-1].children:
            match node:
                case str() | NavigableString():
                    self.visit_text(node)
                case Tag():
                    attrs = {
                        k.split(":")[-1]: " ".join([v] if isinstance(v, str) else v)
                        for k, v in node.attrs.items()
                    }
                    name = node.name.split(":")[-1]

                    self._nstack.append(node)
                    try:
                        self.visit_tag(name, attrs)
                    finally:
                        self._nstack.pop()

    def visit_text(self, text: str) -> None:
        pass
