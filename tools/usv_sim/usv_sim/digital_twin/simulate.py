# tools/usv_sim/usv_sim/digital_twin/simulate.py
from __future__ import annotations

from typing import Callable, Optional, Tuple

import numpy as np

from .contracts import INPUT_DIM, STATE_DIM, as_input_vector, as_state_vector
from .process_model import ProcessParams, process_step

State = np.ndarray  # shape (STATE_DIM,)
Input = np.ndarray  # shape (INPUT_DIM,)


def simulate(
    x0: State,
    dt: float,
    n_steps: int,
    params: ProcessParams,
    u_func: Callable[[int, float, State], Input],
    *,
    t0: float = 0.0,
    w_func: Optional[Callable[[int, float, State, Input], State]] = None,
    on_step: Optional[Callable[[int, float, State, Input, State], None]] = None,
    dtype=np.float64,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Simulate the V1 digital twin forward in time.

    Runs x_{k+1} = f(x_k, u_k, dt) (+ optional additive noise w_k).

    Args:
        x0: initial state, shape (STATE_DIM,)
        dt: time step [s]
        n_steps: number of steps to simulate
        params: process model parameters
        u_func: callback returning input u_k given (k, t, x_k), shape (2,)
        t0: initial time [s]
        w_func: optional callback returning additive noise w_k given (k, t, x_k, u_k), shape (STATE_DIM,)
        on_step: optional callback called after each step: (k, t, x_k, u_k, x_{k+1})
        dtype: float dtype for simulation arrays

    Returns:
        t: time array, shape (n_steps+1,)
        X: state array, shape (n_steps+1, STATE_DIM)
        U: input array, shape (n_steps, INPUT_DIM)
    """
    if dt <= 0.0:
        raise ValueError("dt must be > 0")
    if n_steps < 0:
        raise ValueError("n_steps must be >= 0")

    x0 = as_state_vector(np.asarray(x0, dtype=dtype), name="x0", dtype=dtype)

    t = t0 + dt * np.arange(n_steps + 1, dtype=dtype)
    X = np.empty((n_steps + 1, STATE_DIM), dtype=dtype)
    U = np.empty((n_steps, INPUT_DIM), dtype=dtype)

    X[0] = x0

    for k in range(n_steps):
        tk = float(t[k])
        xk = X[k]

        uk = as_input_vector(
            np.asarray(u_func(k, tk, xk), dtype=dtype),
            name="u_func output",
            dtype=dtype,
        )
        U[k] = uk

        wk = None
        if w_func is not None:
            wk = as_state_vector(
                np.asarray(w_func(k, tk, xk, uk), dtype=dtype),
                name="w_func output",
                dtype=dtype,
            )

        x_next = process_step(xk, uk, dt, params, w=wk)
        X[k + 1] = x_next

        if on_step is not None:
            on_step(k, tk, xk, uk, x_next)

    return t, X, U


def simulate_with_inputs(
    x0: State,
    U_in: np.ndarray,
    dt: float,
    params: ProcessParams,
    *,
    t0: float = 0.0,
    w_func: Optional[Callable[[int, float, State, Input], State]] = None,
    on_step: Optional[Callable[[int, float, State, Input, State], None]] = None,
    dtype=np.float64,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Simulate forward in time using a precomputed input sequence.

    This is a thin wrapper around `simulate()` for the common case where you already
    have `U[k] = [u_s_ach, u_d_ach]` for each step (achieved actuation).

    Args:
        x0: initial state, shape (STATE_DIM,)
        U_in: achieved actuation array, shape (n_steps, INPUT_DIM)
        dt: time step [s]
        params: process model parameters
        t0: initial time [s]
        w_func: optional additive noise callback returning w_k, shape (STATE_DIM,)
        on_step: optional callback called after each step: (k, t, x_k, u_k, x_{k+1})
        dtype: float dtype for simulation arrays

    Returns:
        t: time array, shape (n_steps+1,)
        X: state array, shape (n_steps+1, STATE_DIM)
        U: input array, shape (n_steps, INPUT_DIM)
    """
    U_arr = np.asarray(U_in, dtype=dtype)
    if U_arr.ndim != 2 or U_arr.shape[1] != INPUT_DIM:
        raise ValueError(f"U_in must have shape (n_steps, {INPUT_DIM}), got {U_arr.shape}")

    n_steps = int(U_arr.shape[0])

    def u_func(k: int, _t: float, _x: State) -> Input:
        return U_arr[k]

    return simulate(
        x0=x0,
        dt=dt,
        n_steps=n_steps,
        params=params,
        u_func=u_func,
        t0=t0,
        w_func=w_func,
        on_step=on_step,
        dtype=dtype,
    )
