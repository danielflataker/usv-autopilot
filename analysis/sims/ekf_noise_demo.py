from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np

# Make repo-local imports work when run as a script.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from analysis.sims.scenarios.circle import make_constant_turn
from analysis.sims.scenarios.step import make_step_us
from analysis.sims.scenarios.zigzag import make_zigzag_ud
from usv_sim.digital_twin.contracts import IX_BG, IX_R, IX_X, IX_Y, STATE_DIM
from usv_sim.digital_twin.current import ProcessParams, simulate_with_inputs
from usv_sim.digital_twin.estimation import ExtendedKalmanFilter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a noisy simulator + EKF demo, then plot/animate true trajectory, "
            "EKF predict path, EKF estimate path, and GNSS points."
        )
    )
    parser.add_argument("--scenario", choices=("zigzag", "circle", "step"), default="circle")
    parser.add_argument("--dt", type=float, default=0.1)
    parser.add_argument("--duration", type=float, default=20.0)
    parser.add_argument("--seed", type=int, default=7)

    parser.add_argument("--process-xy-std", type=float, default=0.03)
    parser.add_argument("--process-psi-std", type=float, default=0.004)
    parser.add_argument("--process-v-std", type=float, default=0.03)
    parser.add_argument("--process-r-std", type=float, default=0.03)
    parser.add_argument("--process-bg-std", type=float, default=0.001)

    parser.add_argument("--gnss-std", type=float, default=0.35)
    parser.add_argument("--gyro-std", type=float, default=0.03)
    parser.add_argument("--gnss-rate-hz", type=float, default=5.0)
    parser.add_argument("--gyro-rate-hz", type=float, default=20.0)
    parser.add_argument(
        "--q-scale",
        type=float,
        default=1.0,
        help="Scale factor on process covariance Q (higher trusts model less).",
    )
    parser.add_argument(
        "--r-scale",
        type=float,
        default=1.0,
        help="Scale factor on measurement covariance R (lower trusts sensors more).",
    )

    parser.add_argument(
        "--show",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Show Matplotlib popup windows (use --no-show for headless runs).",
    )
    parser.add_argument(
        "--gif",
        type=str,
        default="",
        help="Optional output GIF path (example: analysis/sims/ekf_demo.gif).",
    )
    parser.add_argument("--fps", type=int, default=2)
    parser.add_argument("--frame-step", type=int, default=3)
    parser.add_argument(
        "--show-history",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Show all points up to the current frame in the animation.",
    )
    parser.add_argument(
        "--center-on-true",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Center animation coordinates on true position at each timestamp.",
    )
    parser.add_argument(
        "--view-radius",
        type=float,
        default=2.0,
        help="Half-width/height [m] when --center-on-true is enabled.",
    )
    return parser.parse_args()


def build_scenario(name: str, dt: float, duration: float, params: ProcessParams) -> tuple[np.ndarray, np.ndarray]:
    x0 = np.zeros(STATE_DIM, dtype=np.float64)
    if name == "zigzag":
        sc = make_zigzag_ud(
            dt=dt,
            T=duration,
            u_s=0.35,
            u_d_amp=0.2,
            period=8.0,
            x0=x0,
            params=params,
        )
    elif name == "circle":
        sc = make_constant_turn(
            dt=dt,
            T=duration,
            u_s=0.8,
            u_d=0.13,
            x0=x0,
            params=params,
        )
    else:
        sc = make_step_us(
            dt=dt,
            T=duration,
            u_s0=0.0,
            u_s1=0.4,
            t_step=6.0,
            u_d=0.08,
            x0=x0,
            params=params,
        )
    return sc.x0, sc.U


def main() -> None:
    args = parse_args()

    import matplotlib

    # Select backend before importing pyplot.
    if not args.show:
        matplotlib.use("Agg")
    else:
        backend_name = str(matplotlib.get_backend()).lower()
        if "agg" in backend_name:
            # In VS Code/CI this can default to a non-interactive backend.
            # Prefer TkAgg for popup windows if available.
            try:
                matplotlib.use("TkAgg")
            except Exception:
                pass

    import matplotlib.animation as animation
    import matplotlib.pyplot as plt
    print(f"Matplotlib backend: {matplotlib.get_backend()}")

    params = ProcessParams(tau_v=2.0, tau_r=0.8, k_v=0.8, k_r=1.2)
    x0, U = build_scenario(args.scenario, args.dt, args.duration, params)
    rng = np.random.default_rng(args.seed)

    process_std = np.array(
        [
            args.process_xy_std,
            args.process_xy_std,
            args.process_psi_std,
            args.process_v_std,
            args.process_r_std,
            args.process_bg_std,
        ],
        dtype=float,
    )

    def w_func(_k: int, _t: float, _x: np.ndarray, _u: np.ndarray) -> np.ndarray:
        return rng.normal(loc=0.0, scale=process_std, size=STATE_DIM)

    t, X_true, _ = simulate_with_inputs(x0, U, args.dt, params, w_func=w_func)

    if args.q_scale <= 0.0:
        raise ValueError("--q-scale must be > 0")
    if args.r_scale <= 0.0:
        raise ValueError("--r-scale must be > 0")

    # Tie EKF covariances to the actual synthetic noise used in this run.
    Q = np.diag(np.maximum(process_std**2, 1e-12) * args.q_scale)
    P0 = np.diag([2.0, 2.0, 0.5, 0.5, 0.5, 0.2])
    ekf = ExtendedKalmanFilter(params=params, Q=Q, x0=x0, P0=P0)

    R_xy = np.diag([args.gnss_std**2, args.gnss_std**2]) * args.r_scale
    R_r = np.array([[args.gyro_std**2]], dtype=float) * args.r_scale

    gnss_stride = max(1, int(round(1.0 / (args.dt * args.gnss_rate_hz))))
    gyro_stride = max(1, int(round(1.0 / (args.dt * args.gyro_rate_hz))))

    n_steps = U.shape[0]
    X_pred = np.zeros_like(X_true)
    X_est = np.zeros_like(X_true)
    Z_xy = np.full((n_steps + 1, 2), np.nan, dtype=float)
    gnss_kx_hist: list[float] = []
    gnss_ky_hist: list[float] = []
    X_pred[0] = x0
    X_est[0] = x0

    for k in range(n_steps):
        ekf.predict(U[k], args.dt)
        X_pred[k + 1] = ekf.x

        idx = k + 1
        if idx % gnss_stride == 0:
            z_xy = X_true[idx, [IX_X, IX_Y]] + rng.normal(0.0, args.gnss_std, size=2)
            Z_xy[idx] = z_xy
            upd = ekf.update_gnss_xy(z_xy=z_xy, R_xy=R_xy)
            gnss_kx_hist.append(float(upd.K[IX_X, 0]))
            gnss_ky_hist.append(float(upd.K[IX_Y, 1]))

        if idx % gyro_stride == 0:
            z_r = np.array(
                [
                    X_true[idx, IX_R]
                    + X_true[idx, IX_BG]
                    + rng.normal(0.0, args.gyro_std)
                ],
                dtype=float,
            )
            ekf.update_gyro_r(z_r=z_r, R_r=R_r)

        X_est[idx] = ekf.x

    pred_rmse = float(np.sqrt(np.mean(np.sum((X_pred[:, :2] - X_true[:, :2]) ** 2, axis=1))))
    est_rmse = float(np.sqrt(np.mean(np.sum((X_est[:, :2] - X_true[:, :2]) ** 2, axis=1))))
    print(f"Scenario: {args.scenario}  N={n_steps}  dt={args.dt}")
    print(
        "Noise setup: "
        f"process_xy_std={args.process_xy_std:.3f}, "
        f"gnss_std={args.gnss_std:.3f}, "
        f"gnss_rate_hz={args.gnss_rate_hz:.1f}, "
        f"q_scale={args.q_scale:.2f}, r_scale={args.r_scale:.2f}"
    )
    print(f"Position RMSE (EKF predict only): {pred_rmse:.3f} m")
    print(f"Position RMSE (EKF after updates): {est_rmse:.3f} m")
    if gnss_kx_hist and gnss_ky_hist:
        print(
            "Mean GNSS gains: "
            f"Kx={np.mean(gnss_kx_hist):.3f}, "
            f"Ky={np.mean(gnss_ky_hist):.3f}"
        )

    fig_xy, ax_xy = plt.subplots(figsize=(8, 7))
    ax_xy.plot(X_true[:, 0], X_true[:, 1], color="black", linewidth=2.0, label="True (process noise)")
    ax_xy.plot(X_pred[:, 0], X_pred[:, 1], color="tab:orange", alpha=0.9, label="EKF predict path")
    ax_xy.plot(X_est[:, 0], X_est[:, 1], color="tab:blue", linewidth=1.8, label="EKF estimate path")

    valid = np.isfinite(Z_xy[:, 0])
    ax_xy.scatter(
        Z_xy[valid, 0],
        Z_xy[valid, 1],
        s=18,
        alpha=0.55,
        color="tab:green",
        label="GNSS measurements",
    )
    ax_xy.set_aspect("equal", adjustable="box")
    ax_xy.set_xlabel("x [m]")
    ax_xy.set_ylabel("y [m]")
    ax_xy.set_title("True vs EKF vs GNSS")
    ax_xy.grid(True, alpha=0.3)
    ax_xy.legend(loc="best")

    fig_err, ax_err = plt.subplots(figsize=(9, 4.5))
    pred_err = np.linalg.norm(X_pred[:, :2] - X_true[:, :2], axis=1)
    est_err = np.linalg.norm(X_est[:, :2] - X_true[:, :2], axis=1)
    ax_err.plot(t, pred_err, color="tab:orange", label="Predict error")
    ax_err.plot(t, est_err, color="tab:blue", label="Estimate error")
    ax_err.set_xlabel("t [s]")
    ax_err.set_ylabel("XY error [m]")
    ax_err.set_title("Position error over time")
    ax_err.grid(True, alpha=0.3)
    ax_err.legend(loc="best")

    if args.view_radius <= 0.0:
        raise ValueError("--view-radius must be > 0")

    fig_anim, ax_anim = plt.subplots(figsize=(8, 7))
    if args.center_on_true:
        ax_anim.set_xlim(-args.view_radius, args.view_radius)
        ax_anim.set_ylim(-args.view_radius, args.view_radius)
    else:
        x_series = [X_true[:, 0], X_pred[:, 0], X_est[:, 0]]
        y_series = [X_true[:, 1], X_pred[:, 1], X_est[:, 1]]
        valid_gnss = np.isfinite(Z_xy[:, 0]) & np.isfinite(Z_xy[:, 1])
        if np.any(valid_gnss):
            x_series.append(Z_xy[valid_gnss, 0])
            y_series.append(Z_xy[valid_gnss, 1])

        x_all = np.concatenate(x_series)
        y_all = np.concatenate(y_series)
        x_span = float(np.max(x_all) - np.min(x_all))
        y_span = float(np.max(y_all) - np.min(y_all))
        pad = max(1.0, 0.05 * max(x_span, y_span))

        xmin = float(np.min(x_all)) - pad
        xmax = float(np.max(x_all)) + pad
        ymin = float(np.min(y_all)) - pad
        ymax = float(np.max(y_all)) + pad
        ax_anim.set_xlim(xmin, xmax)
        ax_anim.set_ylim(ymin, ymax)
    ax_anim.set_aspect("equal", adjustable="box")
    if args.center_on_true:
        ax_anim.set_xlabel("x - x_true [m]")
        ax_anim.set_ylabel("y - y_true [m]")
        ax_anim.set_title("Current state (centered on true)")
    else:
        ax_anim.set_xlabel("x [m]")
        ax_anim.set_ylabel("y [m]")
        ax_anim.set_title("Current state per timestamp")
    ax_anim.grid(True, alpha=0.3)

    (line_true,) = ax_anim.plot([], [], color="red", linewidth=1.1, label="True")
    (line_pred,) = ax_anim.plot([], [], color="tab:orange", linewidth=0.9, alpha=0.9, label="EKF predict")
    (line_est,) = ax_anim.plot([], [], color="tab:blue", linewidth=0.9, label="EKF estimate")
    (line_gnss,) = ax_anim.plot([], [], color="tab:green", linewidth=0.8, alpha=0.6, label="GNSS")

    # Current-step markers (drawn on top of history lines).
    (pt_true,) = ax_anim.plot(
        [],
        [],
        color="red",
        marker="x",
        markersize=11,
        markeredgewidth=2.2,
        linestyle="None",
    )
    (pt_pred,) = ax_anim.plot(
        [],
        [],
        color="tab:orange",
        marker="o",
        markersize=8,
        linestyle="None",
    )
    (pt_est,) = ax_anim.plot(
        [],
        [],
        color="tab:blue",
        marker="o",
        markersize=8,
        linestyle="None",
    )
    (pt_gnss,) = ax_anim.plot(
        [],
        [],
        color="tab:green",
        marker="o",
        markersize=7,
        linestyle="None",
        alpha=0.8,
    )
    ax_anim.legend(loc="best")

    frame_step = max(1, int(args.frame_step))
    frame_indices = list(range(0, n_steps + 1, frame_step))
    if frame_indices[-1] != n_steps:
        frame_indices.append(n_steps)

    def init_anim():
        line_true.set_data([], [])
        line_pred.set_data([], [])
        line_est.set_data([], [])
        line_gnss.set_data([], [])
        pt_true.set_data([], [])
        pt_pred.set_data([], [])
        pt_est.set_data([], [])
        pt_gnss.set_data([], [])
        return line_true, line_pred, line_est, line_gnss, pt_true, pt_pred, pt_est, pt_gnss

    def update_anim(frame_idx: int):
        k = frame_indices[frame_idx]
        x_ref = float(X_true[k, 0])
        y_ref = float(X_true[k, 1])
        if args.center_on_true:
            x_true_k = 0.0
            y_true_k = 0.0
            x_pred_k = float(X_pred[k, 0] - x_ref)
            y_pred_k = float(X_pred[k, 1] - y_ref)
            x_est_k = float(X_est[k, 0] - x_ref)
            y_est_k = float(X_est[k, 1] - y_ref)
            if args.show_history:
                line_true.set_data(X_true[: k + 1, 0] - x_ref, X_true[: k + 1, 1] - y_ref)
                line_pred.set_data(X_pred[: k + 1, 0] - x_ref, X_pred[: k + 1, 1] - y_ref)
                line_est.set_data(X_est[: k + 1, 0] - x_ref, X_est[: k + 1, 1] - y_ref)
            else:
                k0 = max(0, k - 1)
                line_true.set_data(
                    X_true[k0 : k + 1, 0] - x_ref,
                    X_true[k0 : k + 1, 1] - y_ref,
                )
                line_pred.set_data(
                    X_pred[k0 : k + 1, 0] - x_ref,
                    X_pred[k0 : k + 1, 1] - y_ref,
                )
                line_est.set_data(
                    X_est[k0 : k + 1, 0] - x_ref,
                    X_est[k0 : k + 1, 1] - y_ref,
                )
        else:
            x_true_k = float(X_true[k, 0])
            y_true_k = float(X_true[k, 1])
            x_pred_k = float(X_pred[k, 0])
            y_pred_k = float(X_pred[k, 1])
            x_est_k = float(X_est[k, 0])
            y_est_k = float(X_est[k, 1])
            if args.show_history:
                line_true.set_data(X_true[: k + 1, 0], X_true[: k + 1, 1])
                line_pred.set_data(X_pred[: k + 1, 0], X_pred[: k + 1, 1])
                line_est.set_data(X_est[: k + 1, 0], X_est[: k + 1, 1])
            else:
                k0 = max(0, k - 1)
                line_true.set_data(X_true[k0 : k + 1, 0], X_true[k0 : k + 1, 1])
                line_pred.set_data(X_pred[k0 : k + 1, 0], X_pred[k0 : k + 1, 1])
                line_est.set_data(X_est[k0 : k + 1, 0], X_est[k0 : k + 1, 1])

        if args.show_history:
            gx = Z_xy[: k + 1, 0].copy()
            gy = Z_xy[: k + 1, 1].copy()
            if args.center_on_true:
                gx = gx - x_ref
                gy = gy - y_ref
            line_gnss.set_data(gx, gy)
        else:
            if np.isfinite(Z_xy[k, 0]):
                valid_before = np.isfinite(Z_xy[:k, 0]) & np.isfinite(Z_xy[:k, 1])
                if np.any(valid_before):
                    k_prev = int(np.where(valid_before)[0][-1])
                    gx = np.array([Z_xy[k_prev, 0], Z_xy[k, 0]], dtype=float)
                    gy = np.array([Z_xy[k_prev, 1], Z_xy[k, 1]], dtype=float)
                else:
                    gx = np.array([], dtype=float)
                    gy = np.array([], dtype=float)
                if args.center_on_true:
                    gx = gx - x_ref
                    gy = gy - y_ref
                line_gnss.set_data(gx, gy)
            else:
                line_gnss.set_data([], [])

        # Current-step markers.
        pt_true.set_data([x_true_k], [y_true_k])
        pt_pred.set_data([x_pred_k], [y_pred_k])
        pt_est.set_data([x_est_k], [y_est_k])
        if np.isfinite(Z_xy[k, 0]):
            if args.center_on_true:
                pt_gnss.set_data([float(Z_xy[k, 0] - x_ref)], [float(Z_xy[k, 1] - y_ref)])
            else:
                pt_gnss.set_data([float(Z_xy[k, 0])], [float(Z_xy[k, 1])])
        else:
            pt_gnss.set_data([], [])
        if args.center_on_true:
            ax_anim.set_title(f"Current state (centered on true)  t={t[k]:.1f}s")
        else:
            ax_anim.set_title(f"Current state per timestamp  t={t[k]:.1f}s")
        return line_true, line_pred, line_est, line_gnss, pt_true, pt_pred, pt_est, pt_gnss

    anim = animation.FuncAnimation(
        fig_anim,
        update_anim,
        init_func=init_anim,
        frames=len(frame_indices),
        interval=max(20, int(1000 / max(1, args.fps))),
        blit=True,
        repeat=False,
    )

    if args.gif:
        gif_path = Path(args.gif)
        gif_path.parent.mkdir(parents=True, exist_ok=True)
        anim.save(gif_path, writer="pillow", fps=args.fps)
        print(f"Saved GIF: {gif_path}")

    if args.show:
        plt.show()
    else:
        plt.close(fig_xy)
        plt.close(fig_err)
        plt.close(fig_anim)


if __name__ == "__main__":
    main()
