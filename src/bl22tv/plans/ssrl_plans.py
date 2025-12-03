# src/bl22tv/plans/ssrl_plans.py
"""
SSRL BL22 – Motor print plans (Updated to use instrument.devices)

Fixes:
- Removed globals() lookup that caused KeyError inside RunEngine
- Motors resolved dynamically from instrument.devices
"""

from bluesky import plan_stubs as bps

# BITS/Guarneri always places devices in instrument.devices
from bl22tv.startup import instrument


def motor_by_name(name):
    """Return ophyd device from the instrument registry."""
    try:
        return instrument.devices[name]
    except KeyError:
        raise RuntimeError(f"Motor '{name}' not found in instrument.devices")


def motor_print(motor):
    """
    Print live status of any motor.
    Usage: RE(motor_print(S1TOP))
    """
    yield from bps.checkpoint()

    print(f"\n{'='*68}")
    print(f"MOTOR → {motor.name:12}  |  PV: {motor.prefix}")
    print(f"Position     : {motor.user_readback.get():12.6f}  {motor.motor_egu.get()}")
    print(f"Setpoint     : {motor.user_setpoint.get():12.6f}")
    print(f"Velocity     : {motor.velocity.get():8.3f}")
    print(f"Acceleration : {motor.acceleration.get():8.3f}")
    print(f"High limit   : {motor.high_limit_travel.get():10.3f}")
    print(f"Low limit    : {motor.low_limit_travel.get():10.3f}")
    print(f"Moving       : {bool(motor.motor_is_moving.get())}")
    print(f"Done moving  : {bool(motor.motor_done_move.get())}")
    print(f"{'='*68}\n")


def print_all_slit_motors():
    """Print all four entrance-slit motors"""
    yield from bps.checkpoint()
    for name in ["S1BOT", "S1TOP", "S1SPEAR", "S1SSRL"]:
        motor = motor_by_name(name)
        yield from motor_print(motor)


# --- One-liner helpers ---

def print_bot():
    yield from motor_print(motor_by_name("S1BOT"))


def print_top():
    yield from motor_print(motor_by_name("S1TOP"))


def print_spear():
    yield from motor_print(motor_by_name("S1SPEAR"))


def print_ssrl():
    yield from motor_print(motor_by_name("S1SSRL"))

#----------------------------------------------------------------------------
def move_motor(motor_name, position, wait=True):
    """
    Move a single motor to a specified position.

    Parameters
    ----------
    motor_name : str
        Motor name in instrument.devices
    position : float
        Target position
    wait : bool
        If True, plan waits for the move to finish before returning
    """
    motor = motor_by_name(motor_name)
    yield from bps.checkpoint()
    print(f"\n=== Moving motor {motor_name} to {position:.5f} ===\n")
    yield from bps.mv(motor, position)
    if wait:
        while bool(motor.motor_is_moving.get()):
            yield from bps.sleep(0.05)
    print(f"{motor_name} reached {motor.position:.5f}")


#------------------------------------------------------------------------------
# for example
# RE(move_motor("S1TOP", 1.2))
# RE(move_two_motors("S1TOP", 1.2, "S1BOT", 0.5))
# RE(move_motors(["S1TOP","S1BOT","S1SPEAR"], [1.2,0.5,2.0]))

def move_two_motors(motorA_name, posA, motorB_name, posB, wait=True):
    """
    Move two motors simultaneously.

    Parameters
    ----------
    motorA_name, motorB_name : str
        Names of motors
    posA, posB : float
        Target positions
    wait : bool
        If True, plan waits for both moves to finish
    """
    mA = motor_by_name(motorA_name)
    mB = motor_by_name(motorB_name)

    yield from bps.checkpoint()
    print(f"\n=== Moving motors {motorA_name}, {motorB_name} to {posA:.5f}, {posB:.5f} ===\n")
    yield from bps.mv(mA, posA, mB, posB)

    if wait:
        while bool(mA.motor_is_moving.get()) or bool(mB.motor_is_moving.get()):
            yield from bps.sleep(0.05)

    print(f"{motorA_name} reached {mA.position:.5f}, {motorB_name} reached {mB.position:.5f}")
#------------------------------------------------------------------------------
def move_motors(motor_names, positions, wait=True):
    """
    Move multiple motors at once.

    Parameters
    ----------
    motor_names : list of str
    positions : list of float
    wait : bool
    """
    motors = [motor_by_name(name) for name in motor_names]
    yield from bps.checkpoint()
    moves = []
    for m, p in zip(motors, positions):
        moves.extend([m, p])
    print(f"\n=== Moving motors {motor_names} to {positions} ===\n")
    yield from bps.mv(*moves)

    if wait:
        while any(bool(m.motor_is_moving.get()) for m in motors):
            yield from bps.sleep(0.05)

    print("Motors reached positions:", {n: m.position for n, m in zip(motor_names, motors)})



#============================================================================
'''
RE(step_scan("S1TOP", start=-1, stop=1, steps=5, delay=0.2))
'''
def step_scan(motor_name, start, stop, steps, delay=0.0):
    """
    Step scan a single motor.
    
    Parameters
    ----------
    motor_name : str
        Name inside instrument.devices
    start, stop : float
        Motion range
    steps : int
        Number of steps (inclusive)
    delay : float
        Pause at each point (seconds)
    """
    motor = motor_by_name(motor_name)

    yield from bps.checkpoint()
    print(f"\n=== Step scan: {motor_name} from {start} to {stop} in {steps} steps ===\n")

    # Bluesky built-in: absolute scan without detectors
    for pos in bp.linspace(start, stop, steps):
        yield from bps.mv(motor, pos)
        if delay > 0:
            yield from bps.sleep(delay)
        print(f"{motor_name} = {motor.position: .5f}")

'''
RE(two_motor_step_scan(
        "S1TOP",    # motor A
        "S1BOT",    # motor B
        startA=-1, stopA=1,
        startB=0,  stopB=2,
        steps=5,
        delay=0.1
))

'''
def two_motor_step_scan(motorA_name, motorB_name,
                        startA, stopA, startB, stopB,
                        steps, delay=0.0):
    """
    Scan two motors together with independent linear trajectories.

    Example: slit open/close, pitch/roll correction, etc.
    """
    mA = motor_by_name(motorA_name)
    mB = motor_by_name(motorB_name)

    yield from bps.checkpoint()
    print(f"\n=== Two-motor step scan: {motorA_name}, {motorB_name} ===\n")

    positionsA = list(bp.linspace(startA, stopA, steps))
    positionsB = list(bp.linspace(startB, stopB, steps))

    for a, b in zip(positionsA, positionsB):
        yield from bps.mv(mA, a, mB, b)
        if delay > 0:
            yield from bps.sleep(delay)
        print(f"{motorA_name}={mA.position:.5f},  {motorB_name}={mB.position:.5f}")
# N-motor grid scan
def mesh_scan(motor_names, ranges):
    """
    N-motor nested mesh scan (no detectors).
    Example:
        motor_names = ["m1", "m2"]
        ranges = [(0, 1, 5), (-1, 1, 5)]   # (start, stop, steps)
    """

    motors = [motor_by_name(name) for name in motor_names]
    axes = []

    for (start, stop, steps) in ranges:
        axes.append(list(bp.linspace(start, stop, steps)))

    from itertools import product

    for coords in product(*axes):
        moves = []
        for m, pos in zip(motors, coords):
            moves.extend([m, pos])

        yield from bps.mv(*moves)
        print(" | ".join(f"{n}={p:.5f}" for n, p in zip(motor_names, coords)))

