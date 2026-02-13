# LOS guidance (V1)

Line-of-sight (LOS) guidance computes a desired heading $\psi_d$ for the active segment using a lookahead point.

Inputs:
- current pose estimate $(x,y,\psi)$
- active segment endpoints $(x_0,y_0)$ to $(x_1,y_1)$ from the mission manager
- lookahead distance $L$

Outputs:
- desired heading $\psi_d$
- cross-track error $e_y$ (sign convention must match [architecture.md](../architecture.md))
- heading error $e_\psi \overset{\text{def}}{=} \mathrm{wrap}(\psi_d - \psi)$

## Lookahead target
Let the segment direction be:
```math
\vec{d} \overset{\text{def}}{=}
\begin{bmatrix}
x_1-x_0\\
y_1-y_0
\end{bmatrix}, \qquad
\hat{\vec{t}} \overset{\text{def}}{=} \frac{\vec{d}}{\lVert \vec{d}\rVert}.
```

Project current position onto the line to get a closest point $(x_c,y_c)$, then pick a lookahead point along the segment:
```math
\begin{bmatrix}
x_\ell\\
y_\ell
\end{bmatrix}
\overset{\text{def}}{=}
\begin{bmatrix}
x_c\\
y_c
\end{bmatrix}
+ L\,\hat{\vec{t}}.
```

Desired heading:
```math
\psi_d \overset{\text{def}}{=} \mathrm{atan2}(y_\ell - y,\; x_\ell - x).
```

## Notes
- Clamp the lookahead point to the segment (V1) so we don’t “look beyond” the next waypoint too far.
- Always wrap heading differences: $e_\psi = \mathrm{wrap}(\psi_d - \psi)$.

## TODO / Open questions
- Constant $L$ in V1, or speed-dependent $L(v)$?
- Exact definition of signed cross-track error $e_y$ (pick one convention and log it).
- What to do near waypoint transitions (blend headings vs hard switch)?