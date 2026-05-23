"""Network-ready protocol helpers.

The actual socket server/client will be added later. These helpers keep the
wire format stable while the local game remains fully playable.
"""

from .protocol import Message

__all__ = ["Message"]
