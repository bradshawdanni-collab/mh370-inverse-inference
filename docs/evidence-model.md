# Evidence Model

The joint model separates latent physical states from measurement processes.

\[
P(D_j\mid X)=\int P(D_j\mid M_j,\theta_j)P(M_j\mid X)\,dM_j
\]

## Evidence layers

1. SATCOM BTO/BFO
2. Aircraft dynamics and fuel
3. Debris transport and recovery
4. Search non-detection
5. Marine biology
6. Optional atmospheric or hydroacoustic observations when independently verified

Evidence layers are not assumed independent when they share inputs or modelling assumptions. Shared dependencies must be represented explicitly or handled conservatively.
