"""Screening of /match inputs before anything is embedded."""

from __future__ import annotations

from dataclasses import dataclass, field

from loguru import logger


@dataclass
class ScreenedInputs:
    """
    Inputs split into those worth matching and those screened out.

    Parameters
    ----------
    ids : list of str
        Identifiers accepted for matching, in request order.
    texts : list of str
        Texts paired 1-to-1 with `ids`.
    skipped_ids : list of str
        Identifiers screened out. They still appear in the response, with no
        matches; this list exists for logging.
    """

    ids: list[str] = field(default_factory=list)
    texts: list[str] = field(default_factory=list)
    skipped_ids: list[str] = field(default_factory=list)


def screen_inputs(
    ids: list[str],
    texts: list[str],
    min_input_length: int,
) -> ScreenedInputs:
    """
    Split inputs into those to match and those too short to carry signal.

    Length is measured on the stripped text, so trailing whitespace never makes
    a short input look long enough.

    Parameters
    ----------
    ids : list of str
        Opaque identifiers, in request order.
    texts : list of str
        Texts paired 1-to-1 with `ids`.
    min_input_length : int
        Minimum number of characters an input text must have.

    Returns
    -------
    ScreenedInputs
        Accepted ids and texts, plus the ids that were screened out.
    """
    screened = ScreenedInputs()

    for doc_id, text in zip(ids, texts):
        if len(text.strip()) < min_input_length:
            screened.skipped_ids.append(doc_id)
            continue
        screened.ids.append(doc_id)
        screened.texts.append(text)

    if screened.skipped_ids:
        logger.info(
            "Screening: {}/{} input(s) shorter than {} characters, returned without matches",
            len(screened.skipped_ids),
            len(ids),
            min_input_length,
        )
    return screened
