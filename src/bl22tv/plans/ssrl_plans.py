"""
SSRL-specific plans for BL22

Includes:
- Simple plans to move the single and combined stepper motor
- Plan to print motor information
"""

# Standard library
import logging

# Bluesky
from bluesky import plan_stubs as bps
from bluesky import plans as bp

# APS/BITS utils
from apsbits.core.instrument_init import with_registry

logger = logging.getLogger(__name__)
logger.info("Loading SSRL plans")

# ----------------------------------------------------------------------
# Simple move plan for the sigmo motor
# ----------------------------------------------------------------------
@with_registry
def move_sigmo(oregistry, pos: float = 0.0):
    sigmo = oregistry["sigmo"]
    logger.info(f"Moving sigmo motor to position {pos}")
    yield from bps.mv(sigmo, pos)
    print(f"sigmo.position = {sigmo.position}")


# ----------------------------------------------------------------------
# Relative move plan
# ----------------------------------------------------------------------
@with_registry
def move_sigmo_relative(oregistry, delta: float = 1.0):
    sigmo = oregistry["sigmo"]
    current_pos = sigmo.position
    target_pos = current_pos + delta
    logger.info(f"Moving sigmo motor from {current_pos} to {target_pos}")
    yield from bps.mv(sigmo, target_pos)
    print(f"sigmo.position = {sigmo.position}")


# ----------------------------------------------------------------------
# Scan plan example
# ----------------------------------------------------------------------
@with_registry
def scan_sigmo(oregistry, start: float = 0, stop: float = 10, steps: int = 5, detector=None):
    sigmo = oregistry["sigmo"]
    positions = list(bp.linspace(start, stop, steps))
    for pos in positions:
        yield from bps.mv(sigmo, pos)
        if detector:
            reading = detector.read()
            print(f"pos={pos}, detector={reading}")
        else:
            print(f"sigmo.position = {sigmo.position}")


# ----------------------------------------------------------------------
# Print sigmo information plan
# ----------------------------------------------------------------------
@with_registry
def sigmo_print(oregistry):
    """
    Print detailed information about the sigmo motor:
    - current position
    - limits
    - read attributes
    """
    sigmo = oregistry["sigmo"]
    print("=== Mono Motor Info ===")
    print(f"Name: {sigmo.name}")
    print(f"Position: {sigmo.position}")
    # Try to print limits if available
    limits = getattr(sigmo, "limits", None)
    if limits:
        print(f"Limits: {limits}")
    else:
        print("Limits: not defined")
    # Print read attributes
    read_attrs = getattr(sigmo, "read_attrs", None)
    if read_attrs:
        print(f"Read attributes: {read_attrs}")
    else:
        print("Read attributes: not defined")
    print("======================")

