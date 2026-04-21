from __future__ import annotations

from abc import ABC, abstractmethod
from typing import cast

from openai import OpenAI


SYSTEM_PROMPT = (
    "You summarize PDF documents for end users. "
    "Write a faithful, concise summary with clear sections and plain language."
)


class PdfSummaryService(ABC):
    @abstractmethod
    def summarize_document(self, text: str) -> dict[str, str]:
        raise NotImplementedError


class UnconfiguredPdfSummaryService(PdfSummaryService):
    def summarize_document(self, text: str) -> dict[str, str]:
        raise RuntimeError("OPENROUTER_API_KEY is required to summarize PDFs.")


class OpenRouterPdfSummaryService(PdfSummaryService):
    def __init__(self, api_key: str, model: str = "openrouter/free") -> None:
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        self.model = model

    def summarize_document(self, text: str) -> dict[str, str]:
        chunks = self._chunk_text(text)
        chunk_summaries = [self._summarize_chunk(chunk, index + 1, len(chunks)) for index, chunk in enumerate(chunks)]
        final_summary = self._summarize_final("\n\n".join(chunk_summaries))
        return {
            "summary": final_summary,
            "model": self.model,
        }

    def _summarize_chunk(self, chunk: str, index: int, total: int) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Summarize part {index} of {total} of a PDF document. "
                        "Preserve important facts, names, dates, and conclusions.\n\n"
                        f"{chunk}"
                    ),
                },
            ],
        )
        return self._extract_content(response)

    def _summarize_final(self, combined_chunk_summaries: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Create a final PDF summary from these section summaries. "
                        "Structure it with a short overview and concise bullet points.\n\n"
                        f"{combined_chunk_summaries}"
                    ),
                },
            ],
        )
        return self._extract_content(response)

    @staticmethod
    def _extract_content(response: object) -> str:
        choices = cast(object, response).choices
        content = choices[0].message.content
        if isinstance(content, str) and content.strip():
            return content.strip()
        raise RuntimeError("OpenRouter returned an empty summary.")

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 12000) -> list[str]:
        normalized = " ".join(text.split())
        if not normalized:
            return []
        return [normalized[index : index + chunk_size] for index in range(0, len(normalized), chunk_size)]


def build_pdf_summary_service(api_key: str | None, model: str = "openrouter/free") -> PdfSummaryService:
    if not api_key:
        return UnconfiguredPdfSummaryService()
    return OpenRouterPdfSummaryService(api_key=api_key, model=model)
