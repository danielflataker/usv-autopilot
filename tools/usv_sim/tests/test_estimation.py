from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

PKG_ROOT = Path(__file__).resolve().parents[1]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from usv_sim.digital_twin.contracts import IX_BG, IX_PSI, IX_R, IX_X, IX_Y, STATE_DIM
from usv_sim.digital_twin.estimation import ExtendedKalmanFilter, jacobian_F, residual_heading
from usv_sim.digital_twin.process_model import ProcessParams, process_step


class EstimationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.params = ProcessParams(
            tau_v=2.0,
            tau_r=0.8,
            k_v=0.8,
            k_r=1.2,
        )

    def test_jacobian_matches_finite_difference(self) -> None:
        x = np.array([1.0, -2.0, 0.4, 1.3, -0.2, 0.05], dtype=float)
        u = np.array([0.35, -0.1], dtype=float)
        dt = 0.05

        F = jacobian_F(x=x, dt=dt, params=self.params)
        F_fd = np.zeros((STATE_DIM, STATE_DIM), dtype=float)
        eps = 1e-6

        for i in range(STATE_DIM):
            dx = np.zeros(STATE_DIM, dtype=float)
            dx[i] = eps
            xp = process_step(x + dx, u, dt, self.params)
            xm = process_step(x - dx, u, dt, self.params)
            F_fd[:, i] = (xp - xm) / (2.0 * eps)

        self.assertTrue(np.allclose(F, F_fd, atol=1e-6, rtol=1e-5))

    def test_heading_residual_wraps_short_way(self) -> None:
        z = np.array([-np.pi + 0.05], dtype=float)
        z_hat = np.array([np.pi - 0.05], dtype=float)
        res = residual_heading(z, z_hat)
        self.assertTrue(np.allclose(res, np.array([0.1]), atol=1e-10))

    def test_gnss_update_pulls_position_estimate(self) -> None:
        ekf = ExtendedKalmanFilter(
            params=self.params,
            Q=np.eye(STATE_DIM, dtype=float) * 1e-4,
            x0=np.zeros(STATE_DIM, dtype=float),
            P0=np.diag([100.0, 100.0, 1.0, 1.0, 1.0, 1.0]),
        )

        ekf.update_gnss_xy(
            z_xy=np.array([10.0, -5.0], dtype=float),
            R_xy=np.diag([0.1, 0.1]),
        )

        self.assertAlmostEqual(ekf.x[IX_X], 9.99000999, places=5)
        self.assertAlmostEqual(ekf.x[IX_Y], -4.99500500, places=5)

    def test_gyro_update_constrains_r_plus_bias(self) -> None:
        ekf = ExtendedKalmanFilter(
            params=self.params,
            Q=np.eye(STATE_DIM, dtype=float) * 1e-4,
            x0=np.zeros(STATE_DIM, dtype=float),
            P0=np.eye(STATE_DIM, dtype=float),
        )

        z_r = np.array([0.4], dtype=float)
        ekf.update_gyro_r(z_r=z_r, R_r=np.array([[1e-4]], dtype=float))
        self.assertAlmostEqual(ekf.x[IX_R] + ekf.x[IX_BG], 0.4, places=4)

    def test_predict_keeps_covariance_symmetric(self) -> None:
        ekf = ExtendedKalmanFilter(
            params=self.params,
            Q=np.eye(STATE_DIM, dtype=float) * 1e-3,
            x0=np.array([0.0, 0.0, 0.3, 0.2, 0.1, 0.01], dtype=float),
            P0=np.eye(STATE_DIM, dtype=float),
        )
        ekf.predict(u=np.array([0.2, 0.05], dtype=float), dt=0.02)
        self.assertTrue(np.allclose(ekf.P, ekf.P.T, atol=1e-12))
        self.assertTrue(np.isfinite(ekf.x[IX_PSI]))

    def test_process_step_rejects_non_positive_time_constants(self) -> None:
        x = np.zeros(STATE_DIM, dtype=float)
        u = np.zeros(2, dtype=float)
        dt = 0.1

        bad_tau_v = ProcessParams(tau_v=0.0, tau_r=1.0, k_v=0.8, k_r=1.2)
        with self.assertRaisesRegex(ValueError, "params.tau_v must be finite and > 0"):
            process_step(x=x, u=u, dt=dt, params=bad_tau_v)

        bad_tau_r = ProcessParams(tau_v=1.0, tau_r=-0.5, k_v=0.8, k_r=1.2)
        with self.assertRaisesRegex(ValueError, "params.tau_r must be finite and > 0"):
            process_step(x=x, u=u, dt=dt, params=bad_tau_r)


if __name__ == "__main__":
    unittest.main()
